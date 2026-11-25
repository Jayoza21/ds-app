import os, time, logging, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
URL = os.getenv("MODEL_URL", "http://localhost:5001")

class CircuitBreaker:
    def __init__(self, threshold=3, reset_after=10):
        self.threshold, self.reset_after = threshold, reset_after
        self.failures, self.state, self.opened_at = 0, "CLOSED", 0
    def allow(self):
        if self.state == "OPEN":
            if time.time() - self.opened_at >= self.reset_after:
                self.state = "HALF_OPEN"; return True
            return False
        return True
    def success(self):
        self.failures, self.state = 0, "CLOSED"
    def failure(self):
        self.failures += 1
        if self.state == "HALF_OPEN" or self.failures >= self.threshold:
            self.state, self.opened_at = "OPEN", time.time()

breaker = CircuitBreaker()

def call_model(features, retries=3, timeout=1.0, backoff=0.2):
    for attempt in range(1, retries + 1):
        if not breaker.allow():
            raise RuntimeError("circuit OPEN - call blocked")
        try:
            r = requests.post(f"{URL}/predict", json={"features": features}, timeout=timeout)
            r.raise_for_status()
            breaker.success()
            return r.json()
        except requests.RequestException as e:
            breaker.failure()
            app.logger.warning("attempt %d failed (%s) breaker=%s", attempt, type(e).__name__, breaker.state)
            time.sleep(backoff * 2 ** (attempt - 1))     # exponential backoff
    raise RuntimeError("all retries exhausted")

@app.post("/predict")
def predict():
    feats = request.json["features"]
    try:
        out = call_model(feats)
        return jsonify(**out, source="model", breaker=breaker.state)
    except RuntimeError as e:
        # graceful degradation / fallback
        return jsonify(prediction="unknown", source="fallback", reason=str(e), breaker=breaker.state), 200

@app.get("/status")
def status():
    return {"breaker": breaker.state, "failures": breaker.failures}