# Worldwide Weather API

A small FastAPI service that finds a city anywhere in the world and returns its current weather in Celsius or Fahrenheit. It uses [Open-Meteo](https://open-meteo.com/), so no API key is required.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

The interactive API documentation is available at <http://127.0.0.1:8000/docs>.

## Request examples

```bash
curl 'http://127.0.0.1:8000/weather?city=Tokyo&unit=celsius'
curl 'http://127.0.0.1:8000/weather?city=New%20York&unit=fahrenheit'
```

`unit` defaults to `celsius`. Valid values are `celsius` and `fahrenheit`.

## Test

```bash
python -m pytest
```