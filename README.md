# The Big Short

The Big Short helps you explore what is currently trading on Kalshi, understand
exactly what makes a contract resolve YES or NO, and simulate a hypothetical
position against the live order book. It explains the payout, the possible loss,
and the price you would actually receive. It never places trades.

## Or, just use [the-big-short.cloud.run](https://the-big-short.cloud.run) :)

The agent uses four tools, all defined in [`tools.py`](tools.py):

| Tool | What it does |
| --- | --- |
| `search_markets` | Finds a current sample of open markets by topic, category, or closing date. |
| `explain_resolution` | Retrieves the contract rules and the sources Kalshi uses to settle it. |
| `liquidity_check` | Checks how far a dollar amount would move through the live order book. |
| `simulate_trade` | Calculates the hypothetical payout, profit, loss, unspent budget, and break-even probability. |

The web agent runs on FastAPI, LiteLLM, and Gemini 3.8 Flash through Vertex AI.
Conversation history stays separate for each browser session and tool calls are
shown in the chat.

## Try it

1. "What's live right now?"
2. "Which categories are trading today? Show me today's highest-volume market in each."
3. "Which markets close today?"
4. "Pick one live market, explain its YES and NO rules, then show me what $20 on YES would mean."

Search currently ranks a sample by total volume. It cannot verify today's
highest-volume market across every category; the agent should explain that limit.

## Setup

1. A GCP project with billing and the Agent Platform API enabled
   (older docs and the endpoint itself still call it Vertex AI)
2. Run `gcloud auth application-default login`.
3. `uv run app.py`, then open http://localhost:8000

#### Or, just use the-big-short.cloud.run : )
