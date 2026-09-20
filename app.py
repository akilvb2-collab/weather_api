from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


app = FastAPI(
    title="Worldwide Weather API",
    description="Look up current weather for a city using Open-Meteo.",
    version="1.0.0",
)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_json(url: str, params: dict) -> dict:
    request_url = "{}?{}".format(url, urlencode(params))
    request = Request(request_url, headers={"User-Agent": "worldwide-weather-api/1.0"})

    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=502,
            detail="The weather provider is temporarily unavailable.",
        ) from error


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def get_weather_data(city: str, unit: Literal["celsius", "fahrenheit"]) -> dict:
    city = city.strip()
    if not city:
        raise HTTPException(status_code=422, detail="City name cannot be empty.")

    location = fetch_json(
        GEOCODING_URL,
        {"name": city, "count": 1, "language": "en", "format": "json"},
    )
    results = location.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail="City not found.")

    place = results[0]
    temperature_unit = "fahrenheit" if unit == "fahrenheit" else "celsius"
    forecast = fetch_json(
        FORECAST_URL,
        {
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "temperature_unit": temperature_unit,
            "wind_speed_unit": "mph" if unit == "fahrenheit" else "kmh",
            "timezone": "auto",
        },
    )
    current = forecast.get("current")
    if not current:
        raise HTTPException(status_code=502, detail="Weather data was incomplete.")

    return {
        "location": {
            "city": place["name"],
            "country": place.get("country"),
            "country_code": place.get("country_code"),
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "timezone": place.get("timezone"),
        },
        "current": {
            "time": current.get("time"),
            "temperature": current.get("temperature_2m"),
            "temperature_unit": current.get("temperature_2m_units"),
            "humidity": current.get("relative_humidity_2m"),
            "humidity_unit": current.get("relative_humidity_2m_units"),
            "weather_code": current.get("weather_code"),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_speed_unit": current.get("wind_speed_10m_units"),
        },
        "source": "Open-Meteo",
    }


@app.get("/weather")
def weather(
    city: str = Query(..., min_length=1, description="City name, for example London"),
    unit: Literal["celsius", "fahrenheit"] = Query(
        "celsius", description="Temperature unit"
    ),
) -> dict:
    return get_weather_data(city, unit)


class AgentRequest(BaseModel):
    message: str


@app.post("/agent")
def agent(request: AgentRequest) -> dict:
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    from agent import run_agent

    return run_agent(request.message)