"""Demo runner to exercise simulator -> gateway -> backend pipeline.

This script starts the fake gateway (in a thread), then sends a short
sequence of valid and invalid packets from the device simulator to the
gateway, and prints a summary.

It does NOT modify existing backend/auth flows. Use `SIM_BACKEND` to
point to a running backend (default http://127.0.0.1:5000).
"""
from __future__ import annotations
import threading
import time
import requests
import os
from simulator.fake_gateway import app as gateway_app
from simulator.device_simulator import packet_stream, compute_checksum


GATEWAY_PORT = int(os.environ.get("GATEWAY_PORT", 9000))
GATEWAY_URL = f"http://127.0.0.1:{GATEWAY_PORT}/ingest"


def start_gateway():
    # run Flask gateway in background thread
    def run():
        gateway_app.run(host="127.0.0.1", port=GATEWAY_PORT, threaded=True, debug=False, use_reloader=False)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    # give it a second to start
    time.sleep(1.0)
    return t


def send_packet(pkt: dict) -> (bool, str):
    try:
        r = requests.post(GATEWAY_URL, json=pkt, timeout=3)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)


def run_demo(rhino_id: str = "RHINO-001", count_good: int = 5, count_bad: int = 2, interval: float = 0.5):
    print("Starting gateway...")
    start_gateway()

    stream = packet_stream(rhino_id, -1.2921, 36.8219, interval=interval)

    summary = {"sent": 0, "forwarded": 0, "rejected": 0}

    # send good packets
    for _ in range(count_good):
        pkt = next(stream)
        ok, resp = send_packet(pkt)
        summary["sent"] += 1
        if ok:
            summary["forwarded"] += 1
        else:
            summary["rejected"] += 1
        print(f"SENT good -> ok={ok} resp={resp}")

    # send some bad packets (tampered checksum / missing fields)
    for i in range(count_bad):
        pkt = next(stream)
        if i % 2 == 0:
            # tamper checksum
            pkt["checksum"] = "deadbeef"
        else:
            # remove a required field
            pkt.pop("latitude", None)
        ok, resp = send_packet(pkt)
        summary["sent"] += 1
        if ok:
            summary["forwarded"] += 1
        else:
            summary["rejected"] += 1
        print(f"SENT bad  -> ok={ok} resp={resp}")

    print("\nDemo summary:")
    print(summary)

    # attempt to fetch latest location from backend (if available)
    backend_url = os.environ.get("BACKEND_URL", "http://127.0.0.1:5000")
    try:
        q = f"{backend_url}/api/locations/latest"
        r = requests.get(q, timeout=3)
        print("Backend /api/locations/latest ->", r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text)
    except Exception as e:
        print("Could not query backend:", e)


if __name__ == "__main__":
    run_demo()
