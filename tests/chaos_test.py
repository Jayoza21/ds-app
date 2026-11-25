import requests, time, statistics
GW, MS = "http://localhost:8000", "http://localhost:5001"
BODY = {"features": [5.1, 3.5, 1.4, 0.2]}

def chaos(**kw): requests.post(f"{MS}/chaos", json=kw)

def run(name, n=20, **kw):
    chaos(**kw); lat, model, fb = [], 0, 0
    for _ in range(n):
        t = time.time(); r = requests.post(f"{GW}/predict", json=BODY).json()
        lat.append(time.time() - t)
        model += r["source"] == "model"; fb += r["source"] == "fallback"
    st = requests.get(f"{GW}/status").json()["breaker"]
    print(f"{name:<28}| model={model:>2} fallback={fb:>2} | avg={statistics.mean(lat)*1000:6.0f} ms | breaker={st}")

print(f"{'Scenario':<28}| results            | latency    | breaker")
run("1. Healthy",               fail_rate=0, delay=0)
run("2. 50% random failures",   fail_rate=0.5, delay=0)
run("3. Slow (2s > 1s timeout)",fail_rate=0, delay=2)
run("4. Total outage",          fail_rate=1, delay=0)
chaos(fail_rate=0, delay=0); print("...waiting 11s for breaker reset"); time.sleep(11)
run("5. Recovery",              fail_rate=0, delay=0)