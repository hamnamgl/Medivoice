#!/usr/bin/env bash
set -e

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Medivoice setup complete."
echo "Run with: streamlit run app/main.py"
