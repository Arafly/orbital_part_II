from __future__ import annotations

import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app, get_http_client

MESSAGES_URL = "https://owpublic.blob.core.windows.net/tech-task/messages/current-period"
REPORT_1124_URL = "https://owpublic.blob.core.windows.net/tech-task/reports/1124"
REPORT_9999_URL = "https://owpublic.blob.core.windows.net/tech-task/reports/9999"

def make_mock_transport():
    report_calls = {"1124": 0, "9999": 0}
    
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == MESSAGES_URL:
            payload = {
                "messages": [
                    {
                        "id": 1,
                        "text": "Can you provide a Short Lease Report?",
                        "timestamp": "2024-05-01T02:37:43.971Z",
                        "report_id": 1124,
                    },
                    {
                        "id": 2,
                        "text": "What is the rent and how is it varied?",
                        "timestamp": "2024-04-30T04:52:41.870Z",
                    },
                    {
                        "id": 3,
                        "text": "Missing report should fall back",
                        "timestamp": "2024-04-30T04:52:41.870Z",
                        "report_id": 9999,
                    },
                    {
                        "id": 4,
                        "text": "Can you provide a Short Lease Report?",
                        "timestamp": "2024-05-01T02:37:43.971Z",
                        "report_id": 1124,
                    },
                ]
            }
            return httpx.Response(200, json=payload)

        if str(request.url) == REPORT_1124_URL:
            report_calls["1124"] += 1
            return httpx.Response(
                200,
                json={"name": "Short Lease Report", "credit_cost": "79.00"},
            )

        if str(request.url) == REPORT_9999_URL:
            report_calls["9999"] += 1
            return httpx.Response(
                404,
                content=(
                    b"<Error><Code>BlobNotFound</Code>"
                    b"<Message>The specified blob does not exist.</Message></Error>"
                ),
                headers={"Content-Type": "application/xml"},
            )
        return httpx.Response(500, json={"error": "unexpected request"})

    return httpx.MockTransport(handler), report_calls

@pytest.fixture
def client():
    transport, report_calls = make_mock_transport()
    mock_http_client = httpx.AsyncClient(transport=transport)

    async def override_http_client():
        return mock_http_client

    app.dependency_overrides[get_http_client] = lambda: mock_http_client

    with TestClient(app) as test_client:
        test_client.report_calls = report_calls
        yield test_client

    app.dependency_overrides.clear()

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_usage_response_shape(client):
    response = client.get("/usage")
    assert response.status_code == 200

    body = response.json()
    assert "usage" in body
    assert len(body["usage"]) == 4

    first = body["usage"][0]
    assert first["message_id"] == 1
    assert first["report_name"] == "Short Lease Report"
    assert first["credits_used"] == 79.0

    second = body["usage"][1]
    assert second["message_id"] == 2
    assert "report_name" not in second
    assert isinstance(second["credits_used"], float)

    third = body["usage"][2]
    assert third["message_id"] == 3
    assert "report_name" not in third

    fourth = body["usage"][3]
    assert fourth["report_name"] == "Short Lease Report"

def test_report_calls_are_cached_per_unique_report_id(client):
    response = client.get("/usage")
    assert response.status_code == 200
    assert client.report_calls["1124"] == 1
    assert client.report_calls["9999"] == 1