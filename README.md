# HealthFlexx RMR + TDEE Calculator

[![Streamlit App](https://img.shields.io/badge/Streamlit-Launch-FF4B4B?logo=streamlit&logoColor=white)](https://share.streamlit.io)
[![CI](https://github.com/your-org/healthflexx-rmr-tdee-app/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/healthflexx-rmr-tdee-app/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.9%20|%203.10%20|%203.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A lightweight web app to estimate **Resting Metabolic Rate (RMR)** with multiple equations and compute **Total Daily Energy Expenditure (TDEE)**. Built for HealthFlexx.

## Features
- Mifflin–St Jeor, Revised Harris–Benedict, Katch–McArdle, Cunningham
- Activity multipliers (PAL) + optional Thermic Effect of Food (TEF)
- CSV batch processing with downloadable results
- Clean, branded theme

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud
1. Push this repo to GitHub.
2. Go to https://share.streamlit.io → **New app**.
3. Select this repo, branch (e.g., `main`), and `streamlit_app.py` as the app file.
4. Click **Deploy**.