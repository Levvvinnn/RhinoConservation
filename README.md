# Rhino Conservation

This repository contains three focused areas:

- `backend/` — Python Flask API and authentication server
- `frontend/` — React + Vite web application
- `device/` — device firmware and tooling for GPS/telemetry hardware

## Project structure

- `backend/`
  - `app.py` — Flask backend application entrypoint
  - `api.py` — Rhino tracking API routes
  - `db.py` — SQLite database layer
  - `models.py` — shared dataclasses and enums
  - `requirements.txt` — Python dependencies
  - `templates/` — Flask HTML templates

- `frontend/`
  - `package.json` — frontend package definition
  - `vite.config.js` — Vite configuration
  - `src/` — React source files

- `device/`
  - `main.py` — micropython device entrypoint
  - `gps_lora.py`, `gps_wifi.py` — device networking scripts
  - `tools/` — helper scripts for packet tests and decoding

## Local setup

### Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
python app.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Notes

- Backend SQLite databases are stored in `backend/`.
- Frontend assets are contained entirely within `frontend/`.
- Device and hardware scripts live under `device/`.
