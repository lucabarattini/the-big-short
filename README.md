![The Big Short: markets without the mystique](assets/banner.png)

The Big Short helps you explore what is currently trading on Kalshi, understand
exactly what makes a contract resolve to "YES" or "NO", and simulate a hypothetical
position against the order book.

It explains the payout, the possible loss, and the price you would actually receive.
However, it never places trades (this is out of scope).

---

To run it locally, you can just:

1. Set up a Google Cloud project.
2. Enable the [Agent Platform API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com).
3. Clone the repository and navigate to the project folder:

   ```
   git clone https://github.com/lucabarattini/the-big-short.git
   cd the-big-short
   ```

4. Run `gcloud auth application-default login`.
5. Run `uv run app.py`, then open http://localhost:8000.

### Or, you could just use [the-big-short.cloud.run](https://the-big-short.cloud.run) :)
---
The agent uses four main tools, all defined in [`tools.py`](tools.py):

| Tool | What it does |
| --- | --- |
| `search_markets` | Finds a current sample of open markets by topic, category, or closing date. |
| `explain_resolution` | Retrieves the contract rules and the sources Kalshi uses to settle it. |
| `liquidity_check` | Checks how far a hypothetical dollar amount would move through the live order book, i.e. the price you would actually land on. |
| `simulate_trade` | Calculates the hypothetical payout, profit, loss, unspent budget, and break-even probability. |

The web agent runs on FastAPI, LiteLLM, and Gemini 3.8 Flash through Vertex AI.
Conversation history is not saved after your session ends, and tool calls are shown
in the chat for debugging.

---
### Try it by asking the following demo questions

1. "What's live right now?"
2. "Which categories are trading today? Show me today's highest-volume market in each."
3. "Which markets close today?"
4. "Pick one live market, explain its YES and NO rules, then show me what $20 on YES would mean."

Search currently ranks a sample of markets by total volume. For example, if you search
for F1 bets, it will return up to five open F1 markets, ranked by volume.
