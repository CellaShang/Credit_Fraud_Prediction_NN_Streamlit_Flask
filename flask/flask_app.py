import sqlite3
import threading
import time
import traceback
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import tensorflow as tf
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score)

from flask import Flask, jsonify, request

# -----------------------------
# TF Serving endpoint
# -----------------------------
TF_SERVING_URL = "https://fraud-serving-447240734112.us-central1.run.app/v1/models/fraud_model:predict"

app = Flask(__name__)

# -----------------------------
# TensorBoard setup
# -----------------------------
LOGDIR = "gs://credit2025-tensorboard-logs/tensorboard"
writer = tf.summary.create_file_writer(LOGDIR)

global_step = 0
step_lock = threading.Lock()  # ensures thread-safe increments

# -----------------------------
# Initialize SQLite DB
# -----------------------------
conn = sqlite3.connect("monitoring.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    latency REAL,
    prediction TEXT,
    probability REAL,
    true_class INTEGER
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS batch_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    num_samples INTEGER,
    avg_probability REAL,
    accuracy REAL,
    precision REAL,
    recall REAL,
    f1_score REAL
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric TEXT,
    value REAL,
    threshold REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric TEXT,
    action TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
"""
)

conn.commit()

# -----------------------------
# Thresholds
# -----------------------------
ACCURACY_THRESHOLD = 0.90
PRECISION_THRESHOLD = 0.75
RECALL_THRESHOLD = 0.35
LATENCY_THRESHOLD = 0.50  # seconds


# -----------------------------
# Prediction endpoint
# -----------------------------
@app.route("/predict", methods=["POST"])
def predict():
    global global_step
    try:
        # -----------------------------
        # Input validation
        # -----------------------------
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        payload = request.get_json(silent=True)
        if payload is None:
            return jsonify({"error": "Invalid JSON payload"}), 400

        if "instances" not in payload:
            return jsonify({"error": "Missing 'instances' field"}), 400

        data = payload.get("instances", [])
        true_class = payload.get("true_class", None)

        if not isinstance(data, (list, tuple)):
            return jsonify({"error": "'instances' must be a list"}), 400
        if len(data) == 0:
            return jsonify({"error": "'instances' cannot be empty"}), 400

        # Convert to numpy
        data = np.array(data, dtype=np.float32)
        data = np.nan_to_num(data)

        # Ensure 2D
        if data.ndim == 1:
            data = data.reshape(1, -1)

        # -----------------------------
        # Call TF Serving
        # -----------------------------
        start = time.time()
        response = requests.post(
            TF_SERVING_URL, json={"instances": data.tolist()}, timeout=10
        )
        latency = time.time() - start

        if response.status_code != 200:
            return (
                jsonify({"error": f"TF Serving request failed: {response.text}"}),
                500,
            )

        probs = np.array(response.json().get("predictions", [])).flatten()
        labels = ["Fraud" if p > 0.5 else "Not Fraud" for p in probs]

        # -----------------------------
        # Log predictions into SQLite
        # -----------------------------
        for i, p in enumerate(probs):
            lbl = labels[i]
            tc = None
            if true_class is not None:
                tc = (
                    int(true_class[i])
                    if isinstance(true_class, list)
                    else int(true_class)
                )

            cursor.execute(
                """
                INSERT INTO logs (
                    timestamp, latency, prediction, probability, true_class
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (datetime.utcnow().isoformat(), latency, lbl, float(p), tc),
            )
        conn.commit()

        # -----------------------------
        # Compute aggregate metrics
        # -----------------------------
        df = pd.read_sql_query(
            """
            SELECT prediction, true_class, latency
            FROM logs
            WHERE true_class IS NOT NULL
            """,
            conn,
        )

        if len(df) > 0:
            df["y_true"] = df["true_class"].astype(int)
            df["y_pred"] = df["prediction"].map({"Not Fraud": 0, "Fraud": 1})

            acc = accuracy_score(df["y_true"], df["y_pred"])
            prec = precision_score(df["y_true"], df["y_pred"])
            rec = recall_score(df["y_true"], df["y_pred"])
            f1 = f1_score(df["y_true"], df["y_pred"])
            avg_latency = df["latency"].mean()

            cursor.execute(
                """
                INSERT INTO batch_metrics (
                    num_samples, avg_probability, accuracy, precision, recall, f1_score
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (len(data), float(np.mean(probs)), acc, prec, rec, f1),
            )
            conn.commit()

            # Alerts & actions
            alerts = []
            actions = []

            if acc < ACCURACY_THRESHOLD:
                alerts.append(("accuracy", acc, ACCURACY_THRESHOLD))
                actions.append("Flag model as degraded due to low accuracy.")
            if prec < PRECISION_THRESHOLD:
                alerts.append(("precision", prec, PRECISION_THRESHOLD))
                actions.append("Investigate false positives (precision issue).")
            if rec < RECALL_THRESHOLD:
                alerts.append(("recall", rec, RECALL_THRESHOLD))
                actions.append("Investigate false negatives (recall issue).")
            if latency > LATENCY_THRESHOLD:
                alerts.append(("latency", latency, LATENCY_THRESHOLD))
                actions.append("Check system performance / optimize latency.")

            for (metric, value, threshold), action in zip(alerts, actions):
                cursor.execute(
                    "INSERT INTO alerts (metric, value, threshold) VALUES (?, ?, ?)",
                    (metric, float(value), float(threshold)),
                )
                cursor.execute(
                    "INSERT INTO actions (metric, action) VALUES (?, ?)",
                    (metric, action),
                )
            conn.commit()

            # TensorBoard logging
            with step_lock:
                step = global_step
                global_step += 1
            with writer.as_default():
                tf.summary.scalar("accuracy", acc, step=step)
                tf.summary.scalar("precision", prec, step=step)
                tf.summary.scalar("recall", rec, step=step)
                tf.summary.scalar("f1_score", f1, step=step)
                tf.summary.scalar("avg_latency", avg_latency, step=step)
            writer.flush()

        return jsonify(
            {"predictions": labels, "probabilities": probs.tolist(), "latency": latency}
        )

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# -----------------------------
# Run Flask
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
