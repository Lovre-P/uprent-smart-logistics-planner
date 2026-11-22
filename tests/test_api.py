import inspect
import json

import pytest
from fastapi.testclient import TestClient

from conftest import DEFAULT_PATH
from uprent.api import create_app


@pytest.fixture(scope="module")
def client():
    with TestClient(create_app(static_dir=None)) as session:
        yield session


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_default_scenario(client):
    assert client.get("/api/scenario/default").json() == json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))


def test_solve_default(client, scenario_data):
    answer = client.post("/api/solve", json={"scenario": scenario_data})
    assert answer.status_code == 200
    result = answer.json()
    assert result["status"] == "OPTIMAL" and result["validation"]["passed"]
    assert result["totals"]["km"] == 182.2
    assert len(result["analysis"]["curve"]) == 14


def test_solve_invalid_422(client, scenario_data):
    scenario_data["orders"][0]["pickup"] = "L99"
    response = client.post("/api/solve", json={"scenario": scenario_data})
    assert response.status_code == 422
    assert "nepoznata lokacija" in response.json()["detail"]
    assert "N01" in response.json()["detail"]


def test_validate_bad_plan(client, scenario_data):
    plan = {"routes": {"B": [["PICKUP", "N01"], ["PICKUP", "N01"], ["DELIVERY", "N01"]]}}
    report = client.post("/api/validate", json={"scenario": scenario_data, "plan": plan}).json()
    assert report["passed"] is False
    assert any(c["rule"] == "jednom" and not c["passed"] for c in report["checks"])


def test_compare(client, scenario_data):
    rows = client.post("/api/compare", json={"scenario": scenario_data}).json()
    assert [r["km"] for r in rows] == [182.2, 200.1, 200.1, 182.2, 284.2, 209.0]
    payload = {"scenario": scenario_data, "variants": [{"label": "N03 na A", "overrides": {"pinned_orders": {"N03": "A"}}}]}
    assert client.post("/api/compare", json=payload).json()[0]["km"] == 200.1


def test_solve_runs_in_threadpool():
    endpoints = {r.path: r.endpoint for r in create_app(static_dir=None).routes if hasattr(r, "endpoint")}
    for path in ["/api/solve", "/api/validate", "/api/compare"]:
        assert not inspect.iscoroutinefunction(endpoints[path])


def test_static_fallback(tmp_path):
    with TestClient(create_app(tmp_path / "missing")) as session:
        response = session.get("/")
        assert response.status_code == 200 and "nije izgrađeno" in response.text


def test_static_frontend_and_docs(tmp_path):
    (tmp_path / "index.html").write_text("<title>Planer</title>", encoding="utf-8")
    with TestClient(create_app(tmp_path)) as session:
        assert "Planer" in session.get("/").text
        assert session.get("/docs").status_code == 200
        assert "/api/solve" in session.get("/openapi.json").json()["paths"]


def test_cors_only_for_configured_origin(monkeypatch):
    monkeypatch.setenv("UPRENT_CORS_ORIGIN", "https://planner.example")
    with TestClient(create_app(None)) as session:
        for origin, allowed in [("https://planner.example", True), ("https://other.example", False)]:
            headers = {"Origin": origin, "Access-Control-Request-Method": "POST",
                       "Access-Control-Request-Headers": "Content-Type"}
            response = session.options("/api/solve", headers=headers)
            assert (response.headers.get("access-control-allow-origin") == origin) == allowed


def test_serve_cli_invokes_app_with_selected_address(monkeypatch):
    from uprent.cli import main
    import uvicorn

    called = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **kw: called.update(kw))
    assert main(["serve", "--host", "0.0.0.0", "--port", "8010"]) == 0
    assert (called["host"], called["port"]) == ("0.0.0.0", 8010)
