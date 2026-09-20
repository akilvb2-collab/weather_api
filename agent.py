import json
import os
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import HTTPException

from rag import retrieve


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city worldwide.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit",
                },
            },
            "required": ["city", "unit"],
        },
    },
}


def call_ollama(
    messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None
) -> dict:
    payload: Dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
    }
    if tools:
        payload["tools"] = tools

    request = Request(
        OLLAMA_BASE_URL.rstrip("/") + "/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=503,
            detail="Ollama is unavailable. Start Ollama and make sure the model is installed.",
        ) from error


def _run_weather_tool(arguments: Dict[str, Any]) -> dict:
    from app import get_weather_data

    city = arguments.get("city")
    unit = arguments.get("unit", "celsius")
    if not isinstance(city, str) or unit not in {"celsius", "fahrenheit"}:
        raise HTTPException(status_code=422, detail="Invalid weather tool arguments.")
    return get_weather_data(city, unit)


def run_agent(message: str) -> dict:
    retrieved = retrieve(message)
    context = "\n\n".join(
        "Source: {source}\n{content}".format(**item) for item in retrieved
    )
    messages: List[Dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful weather learning agent. Use the get_weather tool "
                "for current weather. Use the supplied knowledge context for explanations. "
                "Do not invent live weather data.\n\nKnowledge context:\n" + context
            ),
        },
        {"role": "user", "content": message},
    ]
    first_response = call_ollama(messages, [WEATHER_TOOL])
    assistant_message = first_response.get("message", {})
    tool_calls = assistant_message.get("tool_calls", [])
    tools_used = []

    if tool_calls:
        messages.append(assistant_message)
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            if function.get("name") != "get_weather":
                continue
            result = _run_weather_tool(function.get("arguments", {}))
            tools_used.append("get_weather")
            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                }
            )
        final_response = call_ollama(messages)
    else:
        final_response = first_response

    return {
        "answer": final_response.get("message", {}).get("content", ""),
        "tools_used": tools_used,
        "sources": [item["source"] for item in retrieved] ,
    }