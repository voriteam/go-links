#!/bin/bash

SCRIPT_DIR=$(dirname "$0")

source server/scripts/load_secrets.sh

export FLASK_APP=main.py

# Run database migrations
sh "$SCRIPT_DIR/upgrade_db.sh"

# Run the application
cd "$SCRIPT_DIR/../src"

gunicorn main:app \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers 4 \
  --logger-class gcp_logging.GCPLogger

