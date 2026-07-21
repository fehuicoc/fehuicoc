from fastapi.testclient import TestClient

from exercise_routine.app import create_app


def test_health_ok():
    client = TestClient(create_app())
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["service"] == "exercise-routine"


def test_template_routes_200():
    client = TestClient(create_app())
    for path in ("/", "/session", "/library", "/author"):
        res = client.get(path)
        assert res.status_code == 200
        assert "Exercise" in res.text
        assert "Routine Coach" in res.text
