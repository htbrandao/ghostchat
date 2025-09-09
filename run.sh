#!/bin/bash

# gunicorn -w 3 -b :8000 -k uvicorn.workers.UvicornWorker -t 90 --preload --max-requests=500 ghostchat.app.main:app
uvicorn ghostchat.app.main:app --reload --host 0.0.0.0 --port 8000
