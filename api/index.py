import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

app = FastAPI()

# CORS: allow POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry data once at cold start
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "q-vercel-latency.json")
with open(DATA_PATH) as f:
    TELEMETRY = json.load(f)


@app.get("/")
def root():
    return {"status": "ok", "endpoint": "POST /api/metrics"}


@app.post("/api/metrics")
async def metrics(payload: dict):
    regions = payload.get("regions", [])
    threshold = float(payload.get("threshold_ms", 180))

    results = {}
    for region in regions:
        records = [r for r in TELEMETRY if r.get("region") == region]
        if not records:
            results[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
                "error": "no data for region",
            }
            continue

        latencies = np.array([r["latency_ms"] for r in records], dtype=float)
        uptimes = np.array([r["uptime_pct"] for r in records], dtype=float)

        results[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 3),
            "breaches": int(np.sum(latencies > threshold)),
        }

    return results