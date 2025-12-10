import streamlit as st
import pandas as pd
import requests
import numpy as np
import logging
from google.cloud import storage
from google.oauth2 import service_account
import io
import os

# -----------------------------
# Setup logging
# -----------------------------
logging.basicConfig(level=logging.DEBUG)

FLASK_URL = "https://fraud-api-447240734112.us-central1.run.app/predict"
GCS_BUCKET = "credit2025-batch-uploads"
GCS_SECRET_PATH = "/secrets/gcs_service_account.json"  # mounted secret

# -----------------------------
# Initialize GCS client using service account secret
# -----------------------------
if os.path.exists(GCS_SECRET_PATH):
    credentials = service_account.Credentials.from_service_account_file(GCS_SECRET_PATH)
    client = storage.Client(credentials=credentials)
else:
    st.warning(
        "GCS service account secret not found; falling back to default credentials."
    )
    client = storage.Client()

bucket = client.bucket(GCS_BUCKET)

# -----------------------------
# Streamlit UI
# -----------------------------
st.title("Credit Card Fraud Detection (Streamlit + Flask)")

# -----------------------------
# Single transaction input
# -----------------------------
st.header("Single transaction input")

default_values = (
    "0.141249,-0.424929,1.277256,0.826234,3.362354,-0.524808,1.422853,"
    "-0.772826,-3.448767,-0.175739,1.201940,-0.136026,-2.776001,2.117868,"
    "1.727262,0.143567,0.041977,1.368740,0.874010,0.636302,-1.011640,"
    "5.279042,-0.680475,-1.213349,-0.037629,2.945911,2.019410,1.011748,"
    "0.405797,0.371406,1.251474,-1.716841,3.293063"
)

user_input = st.text_area("Paste 33 feature values separated by commas", default_values)
true_class_input = st.selectbox("True class (optional)", options=[None, 0, 1])

if st.button("Predict Single Transaction"):
    try:
        values = [float(x.strip()) for x in user_input.split(",") if x.strip()]
        if len(values) != 33:
            st.error(f"You must enter exactly 33 values! You entered {len(values)}.")
        else:
            x = np.array(values).reshape(1, -1).astype(np.float32)
            x = np.nan_to_num(x)
            payload = {"instances": x.tolist()}
            if true_class_input is not None:
                payload["true_class"] = int(true_class_input)

            logging.debug(f"Sending single transaction payload to Flask: {payload}")
            response = requests.post(FLASK_URL, json=payload)
            logging.debug(
                f"Flask response status: {response.status_code}, content: {response.text}"
            )
            result = response.json()

            if "error" in result:
                st.error(result["error"])
            else:
                labels = result.get("predictions", [])
                probs = result.get("probabilities", [])
                if labels and probs:
                    st.write(f"Prediction: **{labels[0]}**")
                    st.write(f"Probability: **{probs[0]:.4f}**")
    except Exception as e:
        st.error(f"Error parsing input: {e}")
        logging.exception("Single transaction error:")
# -----------------------------
# Batch CSV input (paste or GCS path)
# -----------------------------
st.header("Batch prediction via CSV (paste content or GCS path)")

# Default CSV content for testing
DEFAULT_CSV = """Time,V1,V2,V3,V4,V5,V6,V7,V8,V9,V10,V11,V12,V13,V14,V15,V16,V17,V18,V19,V20,V21,V22,V23,V24,V25,V26,V27,V28,Amount,log_amount,hour,is_night,Class
0.304692762,-0.512482347,2.030185795,-3.675748235,4.813831933,-0.213454187,0.074391631,-1.913126239,1.079011555,-2.530369216,-4.161691395,4.61006452,-8.83258421,0.990282139,-7.643602478,-1.161835571,-3.880304373,-5.12310899,-0.514663208,2.222097314,1.493742139,0.595879755,-0.957635365,0.475025477,-1.085115667,0.202547814,0.891060127,1.989994019,1.047101095,0.376947773,1.256144943,-1.374342298,-0.303668655,1
-1.837939392,0.5204263,1.21590677,-3.168127617,2.687132109,-0.901493456,-1.28403903,-2.39796149,0.746952046,0.37331104,-3.693097328,3.507492025,-7.243929074,0.146785697,-5.480002803,1.830549903,-3.040937563,-1.582848029,-0.468985772,1.378639639,0.259732819,0.46564363,-0.075213747,1.134828092,-0.612867126,-3.889754423,0.75895652,0.952140364,0.063564326,-0.335462108,-1.488329127,-2.05934015,3.293062964,1
-1.250476146,-1.032073434,0.907099947,0.001416499,0.57077187,0.687735537,-0.471187619,-0.764278834,-2.633748997,-0.008643197,-0.115477206,0.028919634,-1.080883037,-2.015819893,-0.931387797,1.90759471,-0.121369228,2.444233563,0.376048341,0.478906589,-1.285291768,3.835565073,-1.635194123,-0.237044911,-0.139413628,-0.623618132,1.084286598,1.510585732,0.487553824,-0.336385666,-1.565628518,-0.860593909,-0.303668655,1
-1.702661449,-2.40531327,5.231561872,-10.28817119,7.265493087,-3.08151772,-2.462454552,-8.453549154,4.239744202,-5.197737981,-10.93050188,10.94025256,-16.69295689,0.303098179,-18.25350327,-0.450946686,-11.761556,-16.62403901,-5.969243301,1.432466703,1.799749299,2.689381151,0.308119263,0.884991516,-1.989354386,-0.856782569,1.32956436,3.877813058,2.312618878,-0.335462108,-1.488329127,-1.888090687,3.293062964,1
-0.201924402,-3.588883851,2.07566466,-6.324625945,3.710574031,-2.850240823,-2.123326492,-5.47698354,3.177118857,-4.224392734,-7.848947912,6.191161649,-8.645703834,0.24687294,-12.04585416,-0.398427077,-6.274642781,-14.32146842,-4.247757606,1.0806837,0.687346576,1.491768034,-0.747691542,0.052234915,-0.585237518,0.685839066,2.160653206,3.282325465,-0.873951429,-0.339310268,-1.90746737,1.536898571,-0.303668655,1
0.141249495,-0.42492908,1.277256495,0.826234309,3.362354486,-0.524808389,1.422853312,-0.772826362,-3.448767222,-0.175739252,1.201939966,-0.13602584,-2.776000564,2.117868288,1.727262305,0.143566766,0.041977044,1.368740459,0.874010439,0.636302447,-1.011639847,5.279042416,-0.68047474,-1.21334919,-0.037628921,2.945911351,2.019410371,1.011747707,0.405797322,0.371406423,1.251473756,-1.716841224,3.293062964,0
-1.124818718,0.51722394,-0.367682713,0.722552485,-0.017387933,-0.614259442,0.597730275,-0.724979212,0.400141446,0.786511206,-0.296641805,1.428960585,1.164220959,-0.371910345,-0.12513134,0.152299612,-0.248274641,0.307880385,-0.902841272,-0.257930955,-0.07754426,0.012592689,0.211389657,0.122439377,-0.35741952,-0.164386771,2.133881207,-0.035229817,0.014438077,-0.169144628,0.397327343,-0.518094983,-0.303668655,0
0.563898129,0.979287477,-0.165756431,-1.130813572,0.306661664,0.05259515,-1.032301986,0.495162252,-0.423920274,0.313749856,0.041550533,-0.803131209,0.48305121,0.127911977,0.399531589,-0.49556706,-0.652098906,-0.079653154,-1.061359921,0.250866839,-0.044057424,0.025223904,0.104624431,-0.0021567,0.210490208,0.253932041,1.371711961,-0.293923136,-0.20185488,0.019222809,0.840904086,-0.860593909,-0.303668655,0
-1.117919796,-0.017962583,1.279624854,-2.806607852,0.365102086,1.982351948,1.687174936,-0.273296065,1.328701341,-0.570919019,-1.184568243,0.656534074,-0.51942397,-0.161656035,-2.93652908,1.322578847,1.596245385,3.196164883,2.410546288,-0.094084444,0.160447624,-0.196366554,-0.716366456,0.264663443,1.078423285,-0.380950982,-0.782546571,0.27508218,-0.182916287,-0.324494852,-0.952676845,-0.518094983,-0.303668655,0
"""

csv_mode = st.radio("Input mode", ["Paste CSV content", "GCS path"])

df = None
csv_text = ""
gcs_path = ""

# Default GCS path for testing
DEFAULT_GCS_PATH = "test_subset1.csv"

if csv_mode == "Paste CSV content":
    csv_text = st.text_area("Paste CSV here (include header)", value=DEFAULT_CSV)
    if csv_text:
        # Show preview before prediction
        try:
            preview_df = pd.read_csv(io.StringIO(csv_text))
            st.write("Preview of CSV (before prediction):")
            st.dataframe(preview_df.head())
        except Exception as e:
            st.error(f"Error parsing CSV: {e}")
elif csv_mode == "GCS path":
    gcs_path = st.text_input(
        "Enter CSV path in GCS (e.g., myfile.csv)", value=DEFAULT_GCS_PATH
    )

# -----------------------------
# Predict CSV Button
# -----------------------------
if st.button("Predict CSV"):
    try:
        # Load dataframe
        if csv_mode == "Paste CSV content":
            df = pd.read_csv(io.StringIO(csv_text))
        elif csv_mode == "GCS path" and gcs_path:
            blob = bucket.blob(gcs_path)
            data = blob.download_as_bytes()
            df = pd.read_csv(io.BytesIO(data))

        if df is None:
            st.warning("No CSV data provided.")
        else:
            # Only show predictions, not preview
            if "Class" in df.columns:
                X = df.drop(columns=["Class"])
                y = df["Class"].astype(int).tolist()
            else:
                X = df.copy()
                y = None

            X = X.apply(pd.to_numeric, errors="coerce").dropna().astype(np.float32)
            payload = {"instances": X.values.tolist()}
            if y is not None:
                payload["true_class"] = y

            # Send to Flask API
            logging.debug(f"Sending batch payload to Flask: {len(X)} instances")
            response = requests.post(FLASK_URL, json=payload)
            result = response.json()

            if "error" in result:
                st.error(result["error"])
            else:
                preds = result.get("predictions", [])
                probs = result.get("probabilities", [])

                df_result = X.copy()
                df_result["Prediction"] = preds
                df_result["Probability"] = probs
                st.write("Prediction Results:")
                st.dataframe(df_result.head())

                csv_out = df_result.to_csv(index=False)
                st.download_button(
                    "Download Predictions as CSV",
                    data=csv_out,
                    file_name="fraud_predictions.csv",
                    mime="text/csv",
                )

    except Exception as e:
        st.error(f"Error during batch prediction: {e}")
        logging.exception("Batch prediction error:")
