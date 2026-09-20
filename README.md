# Weather API and Learning AI Agent

This project has two layers:

- `GET /weather` returns live weather from Open-Meteo.
- `POST /agent` uses a local Ollama LLM, a weather tool, and local RAG documents.

No cloud API key is required for the agent.

## 1. Install the project

```bash
cd /home/akil-vb/weather
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Install and prepare Ollama

Install Ollama from <https://ollama.com/download> and make sure it is running. Then download a tool-capable model:

```bash
ollama pull llama3.1:8b
```

You can choose another compatible model:

```bash
export OLLAMA_MODEL=llama3.2:3b
```

The default Ollama address is `http://127.0.0.1:11434`. Override it with `OLLAMA_BASE_URL` if needed.

## 3. Start the API

```bash
source .venv/bin/activate
uvicorn app:app --reload
```

Open the interactive documentation at <http://127.0.0.1:8000/docs>.

## 4. Try the live weather API

```bash
curl 'http://127.0.0.1:8000/weather?city=Tokyo&unit=celsius'
curl 'http://127.0.0.1:8000/weather?city=New%20York&unit=fahrenheit'
```

## 5. Try the AI agent

Use a second terminal while the server is running:

```bash
curl -X POST http://127.0.0.1:8000/agent \
	-H 'Content-Type: application/json' \
	-d '{"message":"What is the weather in London?"}'
```

The response contains the final answer, the tools used, and the RAG source files used:

```json
{
	"answer": "...",
	"tools_used": ["get_weather"],
	"sources": ["weather-basics.md", "weather-advice.md"]
}
```

You can also ask a knowledge question:

```bash
curl -X POST http://127.0.0.1:8000/agent \
	-H 'Content-Type: application/json' \
	-d '{"message":"What does relative humidity mean?"}'
```

## How the agent works

1. `POST /agent` receives the user message.
2. `rag.py` searches the Markdown files in `knowledge/` and selects relevant passages.
3. Ollama receives the user message, retrieved context, and the `get_weather` tool schema.
4. For a live-weather question, the model requests the tool with a city and unit.
5. The application validates the arguments and calls the shared Open-Meteo weather function.
6. The weather result is sent back to Ollama.
7. Ollama writes the final answer using the live result and retrieved context.

The retriever intentionally uses simple word overlap so you can inspect and understand RAG before replacing it with embeddings and a vector database.

## Tests

Tests do not require Ollama or internet access because external calls are mocked:

```bash
python -m pytest
```

## Interview explanation

This is an AI agent because the LLM decides when to use an external tool, the application executes that tool, and the tool result is returned to the LLM for a grounded final response. RAG supplies relevant knowledge from local documents before the answer is generated.
