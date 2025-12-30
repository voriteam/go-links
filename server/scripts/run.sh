#!/bin/bash

source server/scripts/load_secrets.sh

export FLASK_APP=main.py
cd server/src

sh ../scripts/upgrade_db.sh

gunicorn main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 4 \
  --logger-class gcp_logging.GCPLogger

