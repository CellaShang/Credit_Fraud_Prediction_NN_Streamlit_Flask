import streamlit as st
import pandas as pd
import requests
import numpy as np

FLASK_URL = "https://fraud-api-447240734112.us-central1.run.app/predict"

st.title("Credit Card Fraud Detection (Streamlit + Flask)")

# -----------------------------
# Single-row input
# -----------------------------
st.header("Single transaction input")

default_values = (
    "0.141249,-0.424929,1.277256,0.826234,3.362354,-0.524808,1.422853,"
    "-0.772826,-3.448767,-0.175739,1.201940,-0.136026,-2.776001,2.117868,"
    "1.727262,0.143567,0.041977,1.368740,0.874010,0.636302,-1.011640,"
    "5.279042,-0.680475,-1.213349,-0.037629,2.945911,2.019410,1.011748,"
    "0.405797,0.371406,1.251474,-1.716841,3.293063"
)

user_input = st.text_area(
    "Paste 33 feature values separated by commas",
    default_values
)

true_class_input = st.selectbox("True class (optional)", options=[None, 0, 1])

if st.button("Predict Single Transaction"):
    try:
        values = [float(x.strip()) for x in user_input.split(",") if x.strip() != ""]
        if len(values) != 33:
            st.error(f"You must enter exactly 33 values! You entered {len(values)}.")
        else:
            x = np.array(values).reshape(1, -1).astype(np.float32)
            if np.isnan(x).any() or np.isinf(x).any():
                st.warning("NaN or Inf detected in input, replacing with 0.")
                x = np.nan_to_num(x)

            payload = {"instances": x.tolist()}
            if true_class_input is not None:
                payload["true_class"] = int(true_class_input)

            response = requests.post(FLASK_URL, json=payload)
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

# -----------------------------
# Batch CSV input
# -----------------------------
st.header("Batch prediction via CSV")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded CSV:")
        st.dataframe(df.head())

        if st.button("Predict CSV"):
            try:
                # Separate features and labels if 'Class' exists
                if "Class" in df.columns:
                    X = df.drop(columns=["Class"])
                    y = df["Class"].astype(int).tolist()
                else:
                    X = df.copy()
                    y = None

                # Ensure numeric and float32
                X = X.apply(pd.to_numeric, errors='coerce').dropna().astype(np.float32)

                # Send entire batch in one request
                payload = {"instances": X.values.tolist()}
                if y is not None:
                    payload["true_class"] = y

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
                    st.dataframe(df_result.head())

                    csv = df_result.to_csv(index=False)
                    st.download_button(
                        "Download Predictions as CSV",
                        data=csv,
                        file_name="fraud_predictions.csv",
                        mime="text/csv"
                    )
            except Exception as e:
                st.error(f"Error during batch prediction: {e}")
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
