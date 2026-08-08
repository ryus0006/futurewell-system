"""Test that RequestLoggingMiddleware logs each request with its bodies."""

import logging

from fastapi.testclient import TestClient

from app.main import app


def _request_log(caplog) -> str:
    lines = [r.getMessage() for r in caplog.records if r.name == "app.request"]
    assert lines, "no app.request log emitted"
    return lines[-1]


def test_get_is_logged(caplog):
    with caplog.at_level(logging.INFO, logger="app.request"):
        response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    line = _request_log(caplog)
    assert "GET /api/health -> 200" in line
    assert "healthy" in line  # response body included


def test_post_logs_request_and_response_bodies(caplog):
    payload = {
        "age": 53,
        "sex": "male",
        "systolic_bp": 140,
        "total_cholesterol": 6.2,
        "hdl_cholesterol": 1.1,
        "smoking": False,
        "diabetes": False,
        "bp_treated": False,
    }
    with caplog.at_level(logging.INFO, logger="app.request"):
        response = TestClient(app).post("/api/risk", json=payload)

    assert response.status_code == 200
    line = _request_log(caplog)
    assert "POST /api/risk -> 200" in line
    assert "systolic_bp" in line  # request body
    assert "percent" in line  # response body
