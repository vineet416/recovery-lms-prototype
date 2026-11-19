#!/bin/sh
# Fill the database on first start (does nothing if users exist), then start the web server.
python -m scripts.seed --if-empty
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
