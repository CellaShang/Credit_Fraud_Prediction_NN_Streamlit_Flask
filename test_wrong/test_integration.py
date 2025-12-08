import sys, os, json, pytest

# Add flask/ folder to sys.path so Python can find flask_app.py
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "flask"))

import flask_app

# Monkey‑patch infer to avoid loading the real TensorFlow model
def fake_infer(x):
    import tensorflow as tf
    # Simulate a single prediction with fixed probability
    return {"output": tf.constant([[0.7]])}

flask_app.infer = fake_infer
app = flask_app.app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()

def test_valid_request(client):
    payload = {"instances": [[0.1]*33], "true_class": 0}
    resp = client.post("/predict", data=json.dumps(payload), content_type="application/json")

    # Basic response checks
    assert resp.status_code == 200
    body = resp.get_json()

    # Validate keys exist
    assert "predictions" in body
    assert "probabilities" in body
    assert "latency" in body

    # Validate dummy prediction values
    assert isinstance(body["predictions"], list)
    assert isinstance(body["probabilities"], list)
    assert body["predictions"][0] in [0, 1]  # classification output
    assert 0.0 <= body["probabilities"][0] <= 1.0
