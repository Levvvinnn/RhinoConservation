# Simulator: device -> gateway -> backend demo

This folder contains a small, self-contained simulator to exercise the
end-to-end pipeline locally without touching the app's auth/UI flows.

Files:

- `device_simulator.py` — generates realistic telemetry packets (with checksum).
- `fake_gateway.py` — small Flask app that validates packets and forwards them to the backend `/api/rhinos/<rhino_id>/location` endpoint.
- `run_demo.py` — demo runner that starts the gateway and sends a sequence of good and bad packets, then prints a summary.

How to run (local development):

1. Install dependencies in your project venv (if not already):

```bash
pip install -r backend/requirements.txt
pip install requests flask
```

2. Start your backend (Flask) server as you normally do, e.g.:

```bash
# from repo root
cd backend
FLASK_APP=app.py flask run
```

3. In a separate shell, run the demo runner from the repo root:

```bash
python -m simulator.run_demo
```

Notes:
- The gateway forwards to `BACKEND_URL` (default `http://127.0.0.1:5000`).
- The gateway listens on `GATEWAY_PORT` (default `9000`).
- To keep this non-invasive, no existing files were modified. The scripts are optional tools for local testing only.