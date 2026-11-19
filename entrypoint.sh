#!/bin/sh
# Start the web server and reload it when code changes.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
