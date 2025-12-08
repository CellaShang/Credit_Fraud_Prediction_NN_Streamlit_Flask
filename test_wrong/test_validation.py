import sys, os, json, pytest

# Add flask/ folder to sys.path so Python can find flask_app.py
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "flask"))

import flask_app

# Monkey‑patch infer to avoid loading the real TensorFlow model
def fake_infer(x):
    import tensorflow as tf
    return {"output": tf.constant([[0.9]])}  # fixed probability output

flask_app.infer = fake_infer
app = flask_app.app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_requires_json(client):
    resp = client.post("/predict", data="notjson", content_type="application/json")
    assert resp.status_code == 400
    assert "Request must be JSON" in resp.get_json()["error"]

def test_missing_instances(client):
    resp = client.post("/predict", data=json.dumps({"true_class": 1}), content_type="application/json")
    assert resp.status_code == 400
    assert "Missing 'instances'" in resp.get_json()["error"]
