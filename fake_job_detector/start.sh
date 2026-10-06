#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "First create the environment: python3 -m venv .venv"
  echo "Then install: .venv/bin/python -m pip install -r requirements.txt"
  exit 1
fi
exec .venv/bin/python run.py
