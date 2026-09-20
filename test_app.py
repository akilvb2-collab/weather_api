from fastapi.testclient import TestClient

import app
import agent
from rag import retrieve


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


def test_rag_retrieves_relevant_knowledge() -> None:
    results = retrieve("What does relative humidity mean?")

    assert results
    assert results[0]["source"] == "weather-basics.md"


def test_agent_calls_weather_tool_and_returns_final_answer(monkeypatch) -> None:
    responses = iter(
        [
            {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_weather",
                                "arguments": {"city": "London", "unit": "celsius"},
                            }
                        }
                    ]
                }
            },
            {"message": {"content": "London is currently 18 degrees Celsius."}},
        ]
    )
    monkeypatch.setattr(
        agent, "call_ollama", lambda messages, tools=None: next(responses)
    )
    monkeypatch.setattr(
        app,
        "fetch_json",
        lambda url, params: (
            {
                "results": [
                    {
                        "name": "London",
                        "country": "United Kingdom",
                        "latitude": 51.5,
                        "longitude": -0.1,
                    }
                ]
            }
            if "geocoding" in url
            else {
                "current": {
                    "time": "2026-09-20T12:00",
                    "temperature_2m": 18,
                    "temperature_2m_units": "°C",
                    "relative_humidity_2m": 70,
                    "relative_humidity_2m_units": "%",
                    "weather_code": 1,
                    "wind_speed_10m": 10,
                    "wind_speed_10m_units": "km/h",
                }
            }
        ),
    )

    result = agent.run_agent("What is the weather in London?")

    assert result["answer"] == "London is currently 18 degrees Celsius."
    assert result["tools_used"] == ["get_weather"]