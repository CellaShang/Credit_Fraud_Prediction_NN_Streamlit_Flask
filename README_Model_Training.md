# Credit Card Fraud Detection – Model Training

This README documents the **model training pipeline** for the Credit Card Fraud Detection project.  
It covers dataset acquisition, preprocessing, exploratory data analysis (EDA), feature engineering, and training of a TensorFlow/Keras neural network.

---

## 1. Project Setup and Environment

The training workflow is designed for reproducibility and portability across local machines and cloud environments.

**Core libraries:**
- `pathlib`, `os`, `datetime` → file and path management  
- `numpy`, `pandas` → numerical computing and tabular data handling  
- `matplotlib`, `seaborn` → visualization  
- `scikit-learn` → preprocessing, evaluation, class imbalance handling  
- `tensorflow/keras` → neural network modeling  
- `opendatasets` → reproducible dataset download from Kaggle  
- `joblib` → serialization of models and preprocessing artifacts  

**Reproducibility:**
- Global random seed applied to NumPy and TensorFlow.  
- Standardized project structure under `creditcard-fraud-mlops`:
  - `data/raw` → immutable raw data  
  - `data/processed` → cleaned/transformed datasets  
  - `models` → saved checkpoints and final artifacts  
  - `notebooks` → exploratory analysis  
  - `logs` → experiment logs  

---

## 2. Dataset Acquisition

**Dataset:** [Kaggle – Credit Card Fraud Detection](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud)  
**Note** that when running the model_training/model_training.py, you are expected to input your Kaggle account and password.

- 284,807 transactions (European cardholders, September 2013)  
- Features:  
  - `Time` → seconds since first transaction  
  - `V1–V28` → PCA-transformed anonymized features  
  - `Amount` → transaction amount  
  - `Class` → target label (0 = legitimate, 1 = fraud)  

**Characteristics:**
- Highly imbalanced (fraud ≈ 0.17%).  
- Real-world anomaly detection use case.  

**Workflow:**
- `download_creditcard_dataset()` → downloads raw dataset if not present.  
- `load_creditcard_dataframe()` → loads CSV into pandas DataFrame.  

---

## 3. Stratified Subsampling

To enable faster experimentation, a **stratified subsample** of 100,000 transactions is created.  
- Preserves fraud ratio.  
- Ensures reproducibility with fixed seed.  
- Saved to `data/processed/creditcard_subset_100k.csv`.

Function:  
- `stratified_subsample()` → samples fraud and non-fraud proportionally, shuffles, saves subset.

---

## 4. Data Cleaning & Feature Engineering

**Pipeline functions:**
- `load_processed_subset()` → loads subsampled dataset.  
- `remove_duplicates()` → removes duplicate rows.  
- `inspect_numeric_columns()` → validates numeric schema and missing values.  
- `feature_engineering()` → adds:
  - `log_amount` → log-transformed transaction amount  
  - `hour` → hour-of-day derived from `Time`  
  - `is_night` → binary flag for night transactions (00:00–05:59)  

---

## 5. Exploratory Data Analysis (EDA)

Key analyses performed:

- **Class Imbalance:**  
  - Fraud ratio ≈ 0.16%.  
  - Extreme imbalance motivates use of class weighting and PR-AUC metrics.  

- **Transaction Amounts:**  
  - Fraudulent transactions have lower median amounts but wider spread.  
  - Log-transformation stabilizes distribution.  

- **Temporal Patterns:**  
  - Fraud occurs across all times but shows smoother distribution than legitimate transactions.  
  - Temporal features (`hour`, `is_night`) provide useful signal.  

- **Correlation Heatmap:**  
  - PCA features largely decorrelated.  
  - Target variable weakly correlated with individual features → motivates non-linear models.  

- **Fraud Rate by Amount Decile:**  
  - Fraud likelihood varies across bins, non-linear relationship.  

---

## 6. Model Training (Overview)

The TensorFlow/Keras pipeline includes:
- **Preprocessing:** StandardScaler for feature normalization.  
- **Class Imbalance Handling:** `compute_class_weight()` for weighted loss.  
- **Architecture:** Dense feedforward neural network with dropout regularization.  
- **Metrics:** Accuracy, Precision, Recall, F1-score, ROC-AUC, PR-AUC.  
- **Callbacks:** EarlyStopping, ModelCheckpoint, TensorBoard logging.  
- **Serialization:** Models and scalers saved with `joblib` and TensorFlow SavedModel format.  

---

## 7. Outputs

- **Processed dataset:** `data/processed/creditcard_subset_100k.csv`  
- **Engineered features:** `log_amount`, `hour`, `is_night`  
- **EDA visualizations:** class distribution, boxplots, KDE plots, correlation heatmap  
- **Trained models:** stored in `models/`  
- **Logs:** TensorBoard metrics in `logs/`  

