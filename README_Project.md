# Credit Card Fraud Detection System

This repository contains a cloud-native credit card fraud detection platform built using:

- TensorFlow Neural Network for fraud detection  
- Flask REST API for serving predictions  
- Streamlit Web UI for single and batch transaction predictions  
- TensorFlow Serving for high-performance model inference  
- TensorBoard for monitoring model metrics  
- Docker and *Google Cloud Run for containerized deployment  
- GitHub Actions CI/CD for automated build and deployment  

The system is fully containerized, scalable, and provides real-time prediction and monitoring capabilities.

**Live Services:**  
- Streamlit App: [https://fraud-ui-447240734112.us-central1.run.app](https://fraud-ui-447240734112.us-central1.run.app)  
- Real-time Monitoring: [https://tensorboard-447240734112.us-central1.run.app](https://tensorboard-447240734112.us-central1.run.app)  
- Temporary SQLite Logs (read-only, real-time prediction records): https://fraud-api-447240734112.us-central1.run.app/debug/monitor?table=logs

**Note:**
The data provided to Streamlit is already preprocessed, not raw. This ensures consistency with TensorFlow Serving, where the SavedModel is used directly for predictions.

---

## Project Structure

All files are at the root of the repository:

```text
├── flask/                 # Flask API backend
│   ├── flask_app.py
│   ├── requirements.txt
│   ├── start.sh
│   └── Dockerfile
├── streamlit/             # Streamlit UI
│   ├── app.py
│   ├── requirements.txt
│   ├── start.sh
│   └── Dockerfile
├── tf_serving/            # TensorFlow Serving container
│   ├── Dockerfile
│   └── saved_model/       # Exported TensorFlow SavedModel
├── tensorboard/           # TensorBoard container
│   ├── Dockerfile
├── model_training/        # Neural Network Training scripts
│   └── model_training.py
├── Makefile               # Standardized build and deployment commands
├── .github/workflows/     # CI/CD pipeline
├── pre-commit-config.yaml
├── requirements-dev.txt
└── .gitignore
``` 

---

## Prerequisites

- Python 3.11+
- Docker
- Google Cloud SDK (`gcloud`)
- Git
- Optional: A Google Cloud Project with:
  - Cloud Run enabled
  - Artifact Registry or GCR
  - Service account with Cloud Run and Storage access

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/CellaShang/Credit_Fraud_Prediction_NN_Streamlit_Flask.git
cd Credit_Fraud_Prediction_NN_Streamlit_Flask
``` 
### 2. Create Python Environment and Install Dependencies
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r flask/requirements.txt
pip install -r streamlit/requirements.txt

# Optional dev setup
pip install -r requirements-dev.txt
pre-commit install
```
### 3. Run Services Locally
**Option A: Run manually**
```bash
# Flask API
cd flask
python flask_app.py

# Streamlit UI
cd ../streamlit
streamlit run app.py

# TensorBoard (optional)
cd ../tensorboard
tensorboard --logdir logs --port 6006
```
**Option B: Using Docker (fully reproducible)**
```bash
# Build Docker images locally (OR you can use make following the Makefile helper)
docker build -t fraud-api ./flask
docker build -t fraud-ui ./streamlit
docker build -t fraud-serving ./fraud-serving
docker build -t tensorboard ./tensorboard

# Run containers locally
docker run -p 8080:8080 gcr.io/credit2025/fraud-api
docker run -p 8081:8080 gcr.io/credit2025/fraud-ui
docker run -p 8501:8080 gcr.io/credit2025/fraud-serving
docker run -p 6006:6006 gcr.io/credit2025/tensorboard
```
Works locally, no GCP credentials required.

## Cloud Deployment (Documentation Only)

Important: Cannot be run without your own GCP project and credentials. This is for reference only.

### 1. Set Environment Variables
```bash
export PROJECT_ID=<YOUR_GCP_PROJECT>
export REGION=us-central1
```
### 2. Push Docker Images
```bash
# Flask API
docker tag fraud-api gcr.io/$PROJECT_ID/fraud-api:latest
docker push gcr.io/$PROJECT_ID/fraud-api:latest

# Streamlit UI
docker tag fraud-ui gcr.io/$PROJECT_ID/fraud-ui:latest
docker push gcr.io/$PROJECT_ID/fraud-ui:latest

# TensorFlow Serving
docker tag fraud-serving us-central1-docker.pkg.dev/$PROJECT_ID/fraud-ml/fraud-serving:latest
docker push us-central1-docker.pkg.dev/$PROJECT_ID/fraud-ml/fraud-serving:latest

# TensorBoard
docker tag tensorboard gcr.io/$PROJECT_ID/tensorboard:latest
docker push gcr.io/$PROJECT_ID/tensorboard:latest
```
### 3. Deploy to Cloud Run
```bash
# Flask API
gcloud run deploy fraud-api \
  --image gcr.io/$PROJECT_ID/fraud-api:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi

# Streamlit UI
gcloud run deploy fraud-ui \
  --image gcr.io/$PROJECT_ID/fraud-ui:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-secrets "/secrets/gcs_service_account.json=gcs-service-account-key:latest"

# TensorFlow Serving
gcloud run deploy fraud-serving \
  --image us-central1-docker.pkg.dev/$PROJECT_ID/fraud-ml/fraud-serving:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi

# TensorBoard
gcloud run deploy tensorboard \
  --image gcr.io/$PROJECT_ID/tensorboard:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi
```
The Makefile automates these steps using make pipeline-<service> or make pipeline-all.
Readers cannot execute these pipelines without their own GCP project and credentials.


---

## Usage

### Single Transaction Prediction
- Open the Streamlit UI  
- Paste 33 feature values into the input fields  
- Optionally select the true class  
- Click Predict Single Transaction to get the label and probability  

### Batch Prediction
- Upload a CSV file or provide a GCS path with multiple transaction records  
- Click Predict CSV*
- View results in the UI and optionally download predictions as CSV  

---

## Monitoring and Logging
- Flask API:logs predictions, request latency, and errors  
- TF-Serving:low-latency inference and high-throughput handling  
- Streamlit UI: logs user interactions and API responses  
- TensorBoard: tracks accuracy, precision, recall, F1-score, and latency metrics  
- Cloud Run: monitors CPU, memory, request throughput, and error rates  

## SQLite Logs – Local vs Cloud Deployment

The system uses a **SQLite database** to log predictions, request latency, and evaluation metrics for monitoring purposes. The database stores:

- `logs`: individual prediction requests (`timestamp`, `latency`, `prediction`, `probability`, `true_class`)  
- `batch_metrics`: aggregated performance per batch (`num_samples`, `avg_probability`, `accuracy`, `precision`, `recall`, `f1_score`)  
- `alerts`: metrics that violate predefined thresholds  
- `actions`: recommended follow-up actions for alerts  

#### Local Deployment
When running the system locally, the SQLite file is stored in the Flask project directory:

```text
flask/monitoring.db
```
View results in the UI and optionally download predictions as CSV

#### Cloud Deployment

In a Cloud Run deployment, the filesystem is ephemeral, so any SQLite database created by the Flask container is temporary and disappears when the container restarts. To safely inspect recent predictions without touching the production deployment:

---

## Notes

- For **model training and data science workflow**, see the separate [README_Model_Training](../README.md).  
