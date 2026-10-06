# The Big Short

## Use case

A curious beginner asks what prediction markets are open, picks one, understands
its settlement rules, and explores a hypothetical trade. This is education using
live Kalshi data, not recommendations or a trading service.

Keep the existing FastAPI, LiteLLM, Gemini and single HTML chat. Preserve tool
disclosures and session behavior. No new dependencies or frameworks.

## Implementation plan

1. Revise discovery and simulation in `tools.py`, reusing `kalshi_get` and
   `walk_book`. Check live discovery and deterministic fill, filter and error cases.
2. Revise `app.py` instructions and `index.html` copy. Check the discovery-to-trade
   conversation, session continuity and unchanged `/chat` response fields.
3. Check desktop/mobile rendering and review changes with `moyu`. Keep the diff
   limited to this behavior. Record verification below.

Lecture guidance: [REFERENCE.md](00_development_only/ocr/REFERENCE.md).

## Four tools

- `search_markets(query="", category="", closing_today=False)`:
  discover currently open contracts by topic, category, or closing date. Empty
  filters browse all topics. Query words are OR-matched against event/market text.
- `explain_resolution(ticker)`: fetch precise YES/NO labels, rules, settlement
  sources and early-close conditions. Never infer rules from the title alone.
- `liquidity_check(ticker, dollars, side="yes")`: walk the opposite-side bids to
  simulate buying, cheapest first. Show displayed ask, best ask, average price,
  slippage, contracts, spent budget and partial fills. No arbitrary quality tier.
- `simulate_trade(ticker, side, dollars, probability=None)`: reuse the liquidity
  calculation, then show payout/profit if right, loss if wrong, unspent budget and
  break-even probability. Optional decimal probability is the user's estimate
  for their chosen side, from 0 to 100. Expected profit = probability / 100 *
  payout - spent. Do not call both simulation and liquidity for the same request.

Both calculations are original-tool candidates; class-wide uniqueness still
requires comparison with classmates. Dollar inputs must be finite and positive.
All simulations exclude fees and approximate fractional fills. Binary settlement
is assumed at $1 for the winning side and $0 otherwise. Nothing places orders.
Average execution cost is not a crowd forecast. Do not use fixed odds analogies.

## Discovery boundaries

- Base: `https://external-api.kalshi.com/trade-api/v2`, public GET requests only.
- General discovery: `/events`, `status=open`, nested markets, cursor pagination.
- Closing today: `/markets`, `status=open`, `mve_filter=exclude`, minimum and
  maximum closing timestamps; fetch event metadata by event tickers for categories.
- Open now differs from closing today. Today means now through the next midnight
  in `America/New_York`. Also check returned status (`active`) and closing times.
- Scan at most five pages of 200 records, stopping once five matching events are
  found. These are latency/context limits, not financial thresholds. Return one
  contract per event, ranked by keyword matches then volume in the scanned pages.
- Always identify results as a sample, not all contracts or the most likely
  outcomes. An empty sample is not proof that no matching market exists. Suggest
  broader keywords.
- Prices are dollar strings. Buying YES consumes complementary NO bids and vice
  versa. Displayed quotes and order books come from separate snapshots.
- Unknown tickers, rate limits, network failures and invalid arguments return
  actionable JSON errors to the model through the existing dispatcher.

## Conversation and UI

Preserve `response`, `session_id`, and `tool_calls` with `name`, `args`, `result`.
Reuse the chosen market, side, budget and rules in follow-ups; ask when ambiguous.
Sessions stay in memory and are isolated by ID, not durable across restarts or
multiple server processes.

Keep the title The Big Short. Use the supplied film stills, Apple system fonts and
a compact use-case strip. A new conversation begins with four fixed questions
covering discovery, contract rules, and simulation instead of free text. After one
is selected, show the regular composer.
New chat restores the fixed choices. Continue rendering user/model/tool text with
`textContent`.

Acceptance conversation: sports or space discovery, select a contract, ask what
YES means, simulate $20 on YES, explain average versus displayed price, show the
loss if wrong, then recalculate using the user's 62.5% probability.

## Verification and submission

Verified locally on October 6, 2026:

- Focused checks cover YES/NO fills, partial fills, decimal probabilities, invalid
  arguments, closed/empty markets, date boundaries, API failures and schema parity.
- Live Kalshi requests return sports, space and closing-today samples. Live Gemini
  conversations cover discovery, rules, $20 YES, price differences, loss and a
  62.5% probability follow-up. A standalone liquidity request selects that tool.
- API checks pass for the response contract, session isolation, retained history,
  clear and tool-call recording. No new test framework or dependency was added.
- Playwright checks and screenshots pass at 1280px and 390px widths. Both supplied
  images load, all initial choices are reachable, New chat restores them, and the
  guided and active chat states have no horizontal overflow or composer overlap.
- `moyu` review retained shared calculations and no new abstractions. Live review
  caught a model conflating close time with the event deadline; prompt/tool notes
  were clarified and rechecked. Model wording is still nondeterministic.
- Scoped `git diff --check` passes. README now documents the four tools and the
  four guided grader queries with the user's explicit consent.

Do not create or edit README.md without explicit consent. README drafts stay in
chat; sample grader starters are the four guided questions above, including one
complete discovery, explanation, and simulation path.
`submission.json` records author `lb3656`; the deployment URL remains unresolved.
Cloud Run deployment/authentication is separate from this local behavior change.
