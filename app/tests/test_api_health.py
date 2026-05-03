"""API smoke tests using FastAPI TestClient (no CUDA-Q required)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.main import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert "project_version" in payload
    assert "backends_available" in payload
    assert "cpu" in payload["backends_available"]


def test_runs_list_empty_initially() -> None:
    client = TestClient(create_app())
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_unknown_run_returns_404() -> None:
    client = TestClient(create_app())
    resp = client.get("/api/runs/does-not-exist")
    assert resp.status_code == 404


def test_comparison_endpoint_works() -> None:
    client = TestClient(create_app())
    resp = client.get("/api/comparison")
    assert resp.status_code == 200
    payload = resp.json()
    assert "by_molecule" in payload
    assert "totals" in payload


def test_home_page_renders() -> None:
    client = TestClient(create_app())
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"hybrid" in resp.content.lower() or b"cudaq" in resp.content.lower()


def test_run_page_renders() -> None:
    client = TestClient(create_app())
    resp = client.get("/run")
    assert resp.status_code == 200
    assert b"Run an experiment" in resp.content


def test_results_page_renders() -> None:
    client = TestClient(create_app())
    resp = client.get("/results")
    assert resp.status_code == 200


def test_compare_page_renders() -> None:
    client = TestClient(create_app())
    resp = client.get("/compare")
    assert resp.status_code == 200


def test_unknown_run_detail_page_returns_404() -> None:
    client = TestClient(create_app())
    resp = client.get("/results/no-such-run")
    assert resp.status_code == 404


def test_openapi_schema_includes_routes() -> None:
    client = TestClient(create_app())
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/health" in paths
    assert "/api/runs/h2" in paths
    assert "/api/runs/lih" in paths
    assert "/api/comparison" in paths
