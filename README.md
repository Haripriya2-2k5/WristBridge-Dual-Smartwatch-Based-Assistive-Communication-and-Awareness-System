# WristBridge — Streamlit Prototype

This repository contains a **prototype** Streamlit web app for the WristBridge assistive system.
It simulates Tapface mode switching, TTS/STT, SOS with GPS simulation and a caregiver dashboard.

## Files
- `app.py` — main Streamlit app (single-file UI)
- `database.py` — small SQLite helper
- `requirements.txt` — Python deps

## How to run locally
1. Clone repo
2. Create virtual env and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
