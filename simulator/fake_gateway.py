"""Fake gateway that accepts simulator packets and forwards to backend.

Run this as a small Flask app. It validates packet shape, checksum and
forwards normalized data to the backend telemetry endpoint.

This file is intentionally self-contained and will not modify existing
backend code. Configure backend URL with `BACKEND_URL` env var.
"""
from __future__ import annotations
from flask import Flask, request, jsonify
import os
import requests
import json
from typing import Dict

from simulator.device_simulator import compute_checksum

app = Flask(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:5000")


def validate_packet(pkt: Dict) -> (bool, str):
    required = ["rhino_id", "device_id", "timestamp", "latitude", "longitude", "battery", "checksum"]
    for k in required:
        if k not in pkt:
            return False, f"missing field: {k}"
    # verify checksum
    provided = pkt.get("checksum")
    copy = {k: v for k, v in pkt.items() if k != "checksum"}
    expected = compute_checksum(copy)
    if provided != expected:
        return False, f"checksum mismatch (expected {expected} got {provided})"
    # basic ranges
    lat = float(pkt["latitude"])
    lon = float(pkt["longitude"])
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return False, "lat/lon out of range"
    return True, "ok"


@app.route("/ingest", methods=["POST"])
def ingest():
    pkt = request.get_json(silent=True)
    if not isinstance(pkt, dict):
        return jsonify({"success": False, "error": "invalid json"}), 400

    ok, reason = validate_packet(pkt)
    if not ok:
        print(f"[gateway] INVALID packet: {reason} -> {pkt}")
        return jsonify({"success": False, "error": reason}), 400

    rhino_id = pkt["rhino_id"]
    # map to backend location API
    url = f"{BACKEND_URL}/api/rhinos/{rhino_id}/location"
    payload = {
        "latitude": pkt["latitude"],
        "longitude": pkt["longitude"],
        "altitude": pkt.get("altitude"),
        "accuracy": pkt.get("accuracy"),
        "battery": pkt.get("battery"),
        "sats": pkt.get("sats"),
    }

    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.ok:
            print(f"[gateway] forwarded packet for {rhino_id} -> backend: {resp.status_code}")
            return jsonify({"success": True}), 200
        else:
            print(f"[gateway] backend error for {rhino_id}: {resp.status_code} {resp.text}")
            return jsonify({"success": False, "error": "backend rejected"}), 502
    except Exception as e:
        print(f"[gateway] error forwarding to backend: {e}")
        return jsonify({"success": False, "error": str(e)}), 502


if __name__ == "__main__":
    port = int(os.environ.get("GATEWAY_PORT", 9000))
    print(f"Starting fake gateway on http://127.0.0.1:{port} (BACKEND_URL={BACKEND_URL})")
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False)
