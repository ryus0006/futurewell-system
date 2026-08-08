#!/bin/sh
# --no-access-log: RequestLoggingMiddleware is the access log (adds status + timing).
exec uvicorn app.main:app --host 0.0.0.0 --port 8080 --no-access-log
