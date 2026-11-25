import os, time, random
from flask import Flask, request, jsonify
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
X, y = load_iris(return_X_y=True)
model = RandomForestClassifier(n_estimators=50, random_state=42).fit(X, y)
NAMES = ["setosa", "versicolor", "virginica"]
chaos = {"fail_rate": float(os.getenv("FAIL_RATE", 0)),
         "delay": float(os.getenv("DELAY_SEC", 0))}

@app.post("/chaos")                      # change failure mode at runtime
def set_chaos():
    chaos.update({k: float(v) for k, v in request.json.items() if k in chaos})
    return jsonify(chaos)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict():
    time.sleep(chaos["delay"])           # simulated latency
    if random.random() < chaos["fail_rate"]:
        return jsonify(error="simulated failure"), 500
    f = request.json["features"]
    return jsonify(prediction=NAMES[int(model.predict([f])[0])])