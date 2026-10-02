# gemini-web-tool-calling

`qwen-tool-calling` behind a web server, pointed at Gemini.

- The harness loop is the same one from `qwen-tool-calling`, wrapped in `run_agent()`.
- The session store and `/chat` endpoint are the ones from `qwen-web-chat`.
- Only the model changed: `vertex_ai/gemini-3.5-flash-lite` in the `global` location.
- `/chat` also returns the tool calls the harness made, and the page shows them
  above the assistant's answer.

## Setup

1. A GCP project with billing and the Agent Platform API enabled
   (older docs and the endpoint itself still call it Vertex AI)
2. `gcloud auth application-default login`. The app uses your gcloud default
   project, so run `gemini-hello-world` first to check it.
3. `uv run app.py`, then open http://localhost:8000

Try: "Is it nice enough to go for a walk in New York?"

The weather comes from Open-Meteo, which needs no API key.
