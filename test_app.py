from fastapi.testclient import TestClient

import app


client = TestClient(app.app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_weather_rejects_invalid_unit() -> None:
    response = client.get("/weather", params={"city": "London", "unit": "kelvin"})

    assert response.status_code == 422


def test_weather_returns_not_found(monkeypatch) -> None:
    monkeypatch.setattr(app, "fetch_json", lambda url, params: {})

    response = client.get("/weather", params={"city": "NotARealCity"})

    assert response.status_code == 404
    assert response.json()["detail"] == "City not found."