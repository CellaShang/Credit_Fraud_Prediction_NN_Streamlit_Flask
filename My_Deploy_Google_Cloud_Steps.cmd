REM ============================================================================
REM My_Example_Cloud_Run_Deploy.cmd
REM ============================================================================
REM NOTE: This file is NOT a general deployment guide.
REM It documents the exact steps I personally used to deploy the credit card
REM fraud detection system to Google Cloud Run from my local environment.
REM It includes my specific project IDs, paths, and container images.
REM ============================================================================

:: =============================================
:: Windows CMD Instructions
:: =============================================

:: -----------------------------
:: 1. TF Serving Deployment
:: -----------------------------
echo Deploying TF Serving...
set PROJECT_ID=credit2025
set IMAGE_NAME=us-central1-docker.pkg.dev/%PROJECT_ID%/fraud-ml/fraud-serving:latest

:: Login to GCP
gcloud auth login

:: Build Docker image
docker build -t %IMAGE_NAME% ./fraud-serving

:: Push to Artifact Registry
docker push %IMAGE_NAME%

:: Deploy to Cloud Run
gcloud run deploy fraud-serving ^
  --image %IMAGE_NAME% ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --port 8080 ^
  --memory 2Gi

:: Test TF Serving
curl -X POST -H "Content-Type: application/json" ^
  -d "{\"instances\": [[0.304692762, -0.512482347, 2.030185795, -3.675748235, 4.813831933, -0.213454187, 0.074391631, -1.913126239, 1.079011555, -2.530369216, -4.161691395, 4.61006452, -8.83258421, 0.990282139, -7.643602478, -1.161835571, -3.880304373, -5.12310899, -0.514663208, 2.222097314, 1.493742139, 0.595879755, -0.957635365, 0.475025477, -1.085115667, 0.202547814, 0.891060127, 1.989994019, 1.047101095, 0.376947773, 1.256144943, -1.374342298, -0.303668655]]}" ^
  https://fraud-serving-447240734112.us-central1.run.app/v1/models/fraud_model:predict

:: -----------------------------
:: 2. Flask API Deployment
:: -----------------------------
echo Deploying Flask API...
cd "C:\Users\Cella.Shang\OneDrive - N-Able, Inc\Desktop\Distributed\DTI 6302\Project\credit_fraud_Final\credit_fraud\flask"

docker build -t gcr.io/credit2025/fraud-api .
docker push gcr.io/credit2025/fraud-api

gcloud run deploy fraud-api ^
  --image gcr.io/credit2025/fraud-api ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --port 8080 ^
  --memory 1Gi

:: Test Flask API
curl -X POST https://fraud-api-447240734112.us-central1.run.app/predict ^
     -H "Content-Type: application/json" ^
     -d "{\"instances\": [[0.304692762,-0.512482347,2.030185795,-3.675748235,4.813831933,-0.213454187,0.074391631,-1.913126239,1.079011555,-2.530369216,-4.161691395,4.61006452,-8.83258421,0.990282139,-7.643602478,-1.161835571,-3.880304373,-5.12310899,-0.514663208,2.222097314,1.493742139,0.595879755,-0.957635365,0.475025477,-1.085115667,0.202547814,0.891060127,1.989994019,1.047101095,0.376947773,1.256144943,-1.374342298,-0.303668655]]}"

:: -----------------------------
:: 3. Streamlit UI Deployment
:: -----------------------------
echo Deploying Streamlit UI...
cd "C:\Users\aaron\Desktop\cella_course_exam\credit_fraud\streamlit"

gcloud auth login
gcloud config set project credit2025

gcloud builds submit --tag gcr.io/credit2025/fraud-ui:latest

gcloud run deploy fraud-ui ^
  --image gcr.io/credit2025/fraud-ui:latest ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated ^
  --memory 1Gi ^
  --concurrency 1 ^
  --min-instances 2 ^
  --set-secrets "/secrets/gcs_service_account.json=gcs-service-account-key:latest"

:: -----------------------------
:: 4. TensorBoard Deployment
:: -----------------------------
echo Deploying TensorBoard...
cd "C:\Users\Cella.Shang\OneDrive - N-Able, Inc\Desktop\Distributed\DTI 6302\Project\credit_fraud_Final\credit_fraud\tensorboard"

docker build -t gcr.io/credit2025/tensorboard .
docker push gcr.io/credit2025/tensorboard

gcloud run deploy tensorboard ^
  --image gcr.io/credit2025/tensorboard ^
  --platform managed ^
  --region us-central1 ^
  --allow-unauthenticated

:: =============================================
:: Deployment Complete
:: =============================================
echo All services deployed! Check URLs:
echo TF Serving: https://fraud-serving-447240734112.us-central1.run.app
echo Flask API: https://fraud-api-447240734112.us-central1.run.app
echo Streamlit UI: https://fraud-ui-447240734112.us-central1.run.app
echo TensorBoard: https://tensorboard-447240734112.us-central1.run.app
pause
