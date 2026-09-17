"""Tests for the Workstreams API using a locally-signed dev JWT."""
from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app

DEV_SECRET = "dev-shared-secret-do-not-use-in-prod"


def _dev_token(sub: str = "test-user", roles: list[str] | None = None) -> str:
    payload = {
        "sub": sub,
        "aud": "api://wes-api",
        "roles": roles or ["Workstreams.ReadWrite"],
        "iat": time.time(),
        "exp": time.time() + 3600,
    }
    return jwt.encode(payload, DEV_SECRET, algorithm="HS256")


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": f"Bearer {_dev_token()}"}


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_requires_auth(client: TestClient) -> None:
    response = client.get("/api/v1/workstreams")
    assert response.status_code in (401, 403)


def test_create_and_list_workstream(client: TestClient, auth_headers: dict) -> None:
    create_resp = client.post("/api/v1/workstreams", params={"title": "Migrate EKS to AKS"}, headers=auth_headers)
    assert create_resp.status_code == 201
    body = create_resp.json()
    assert body["title"] == "Migrate EKS to AKS"
    assert 0.0 <= body["risk_score"] <= 100.0

    list_resp = client.get("/api/v1/workstreams", headers=auth_headers)
    assert list_resp.status_code == 200
    assert any(w["id"] == body["id"] for w in list_resp.json())


def test_ai_search(client: TestClient, auth_headers: dict) -> None:
    response = client.get("/api/v1/ai/search", params={"q": "risk threshold"}, headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) > 0
