"""Public Kalshi data and hypothetical fills. No trading credentials or orders."""

import json
import math
import re
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

import requests

BASE = "https://external-api.kalshi.com/trade-api/v2"


#-----Request public Kalshi data and return actionable errors----
def kalshi_get(path, params=None):
    try:
        response = requests.get(BASE + path, params=params, timeout=10)
        if response.status_code == 404:
            return None, "Not found. Use a ticker returned by search_markets."
        if response.status_code == 429:
            return None, "Kalshi rate limit hit. Wait a few seconds and try once more."
        if response.status_code != 200:
            return None, f"Kalshi returned HTTP {response.status_code}. Try again later."
        return response.json(), None
    except requests.RequestException:
        return None, "Kalshi is unreachable or returned invalid JSON. Try again later."


#-----Browse a bounded sample of currently open markets----
def search_markets(query: str = "", category: str = "", closing_today: bool = False) -> str:
    if not all(isinstance(value, str) for value in (query, category)) or type(closing_today) is not bool:
        return json.dumps({"error": "Use text for query and category, and true or false for closing_today."})
    words = set(re.findall(r"[a-z0-9]+", query.lower()))
    now = datetime.now(ZoneInfo("America/New_York"))
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    matches, scanned, cursor = {}, 0, ""
    for _ in range(5):
        params = {"status": "open", "limit": 200, "cursor": cursor}
        if closing_today:
            params.update({"min_close_ts": int(now.timestamp()), "max_close_ts": int(midnight.timestamp()),
                           "mve_filter": "exclude"})
        else:
            params["with_nested_markets"] = "true"
        data, error = kalshi_get("/markets" if closing_today else "/events", params)
        if error:
            return json.dumps({"error": error})
        cursor = data.get("cursor") or ""
        events = data.get("events", [])
        if closing_today and data.get("markets"):
            tickers = list(dict.fromkeys(market["event_ticker"] for market in data["markets"]))
            metadata, error = kalshi_get("/events", {"tickers": ",".join(tickers), "limit": 200})
            if error:
                return json.dumps({"error": error})
            events = [{**event, "markets": [market for market in data["markets"]
                       if market["event_ticker"] == event["event_ticker"]]} for event in metadata.get("events", [])]
        for event in events:
            scanned += 1
            if category and category.lower().strip() != (event.get("category") or "").lower():
                continue
            for market in event.get("markets") or []:
                close = datetime.fromisoformat(market["close_time"].replace("Z", "+00:00"))
                if market.get("status") != "active" or close <= now or (closing_today and close >= midnight):
                    continue
                text = " ".join(str(item.get(key) or "") for item in (event, market)
                                for key in ("title", "sub_title", "yes_sub_title", "category")).lower()
                score = sum(word in text for word in words) if words else 1
                if not score:
                    continue
                rank = (score, float(market.get("volume_fp") or 0))
                key = event["event_ticker"]
                if key not in matches or rank > matches[key][0]:
                    matches[key] = (rank, {"event_ticker": key, "category": event.get("category"),
                        **{field: market.get(field) for field in ("ticker", "title", "yes_sub_title", "no_sub_title", "close_time")},
                        **{field: float(market[field + "_dollars"]) if market.get(field + "_dollars") else None
                           for field in ("yes_bid", "yes_ask", "no_bid", "no_ask", "last_price")}})
        if len(matches) >= 5 or not cursor:
            break
    return json.dumps({"markets": [item[1] for item in sorted(matches.values(), key=lambda item: item[0], reverse=True)[:5]],
        "as_of": now.isoformat(), "timezone": "America/New_York", "closing_today": closing_today,
        "events_scanned": scanned,
        "note": "Sample of up to 5 events, one matching contract per event, ranked by keyword matches then volume within scanned pages. "
                "Not the full catalog, all outcomes, or a recommendation. Scans at most 5 pages of 200 records. "
                "If nothing matches, try broader keywords. Prices are dollars per contract, not guaranteed probabilities."})


#-----Fetch the exact rules and sources for one contract----
def explain_resolution(ticker: str) -> str:
    data, error = kalshi_get(f"/markets/{quote(ticker, safe='')}")
    if error:
        return json.dumps({"error": error})
    market = data["market"]
    data, error = kalshi_get(f"/events/{quote(market['event_ticker'], safe='')}")
    if error:
        return json.dumps({"error": error})
    result = {key: market.get(key) for key in (
        "ticker", "title", "yes_sub_title", "no_sub_title", "status", "close_time", "rules_primary",
        "rules_secondary", "can_close_early", "early_close_condition")}
    result["settlement_sources"] = data["event"].get("settlement_sources", [])
    result["note"] = "close_time is when trading closes, not necessarily the event deadline. Use only the returned rules and sources; do not invent missing details."
    if market.get("result"):
        result["result"] = market["result"]
    return json.dumps(result)


#-----Calculate a hypothetical fill from the cheapest live offers----
def walk_book(orderbook_fp, side, dollars):
    opposite = (orderbook_fp or {}).get("no_dollars" if side == "yes" else "yes_dollars") or []
    asks = sorted((round(1 - float(p), 4), float(q)) for p, q in opposite
                  if 0 < float(p) < 1 and math.isfinite(float(q)) and float(q) > 0)
    spent, contracts, levels, worst = 0.0, 0.0, 0, None
    for price, qty in asks:
        if spent >= dollars:
            break
        take = min(qty, (dollars - spent) / price)
        contracts += take
        spent += take * price
        levels += 1
        worst = price
    return {
        "best_ask": asks[0][0] if asks else None,
        "avg_price": round(spent / contracts, 4) if contracts else None,
        "worst_price": worst, "contracts": round(contracts, 2),
        "levels_used": levels, "spent": round(spent, 2),
        "fully_filled": spent >= dollars - 0.000001,
    }


#-----Compare a budget with the live order book----
def liquidity_check(ticker: str, dollars: float, side: str = "yes") -> str:
    if side not in ("yes", "no") or isinstance(dollars, bool) or not isinstance(dollars, (int, float)) or not math.isfinite(dollars) or dollars <= 0:
        return json.dumps({"error": "Use side 'yes' or 'no' and a finite USD amount greater than 0."})
    path = f"/markets/{quote(ticker, safe='')}"
    data, error = kalshi_get(path)
    if error:
        return json.dumps({"error": error})
    market = data["market"]
    if market.get("status") != "active":
        return json.dumps({"error": "This market is not active. Use search_markets to find an open market."})
    data, error = kalshi_get(path + "/orderbook")
    if error:
        return json.dumps({"error": error})
    result = walk_book(data.get("orderbook_fp"), side, dollars)
    if result["avg_price"] is None:
        return json.dumps({"error": f"Nobody is selling {side} on this market right now, so there is no price to check. Try another market or side."})
    slippage = round((result["avg_price"] - result["best_ask"]) * 100, 1)
    return json.dumps({**result, "ticker": ticker, "title": market["title"], "side": side,
                       "budget": dollars, "slippage_cents": slippage,
                       "displayed_ask": float(market[side + "_ask_dollars"]) if market.get(side + "_ask_dollars") else None,
                       "as_of": datetime.now(ZoneInfo("America/New_York")).isoformat(),
                       "note": "Snapshot simulation only, before fees; fractional fills are approximated. No money moves. Displayed ask and order book are separate snapshots."})


#-----Show the two possible outcomes of a hypothetical trade----
def simulate_trade(ticker: str, side: str, dollars: float, probability: float | None = None) -> str:
    if probability is not None and (isinstance(probability, bool) or not isinstance(probability, (int, float)) or not 0 <= probability <= 100):
        return json.dumps({"error": "Use a probability from 0 to 100 for your chosen side, including decimals, or omit it."})
    result = json.loads(liquidity_check(ticker, dollars, side))
    if "error" in result:
        return json.dumps(result)
    payout, spent = result["contracts"], result["spent"]
    result.update({"payout_if_right": payout, "profit_if_right": round(payout - spent, 2),
                   "payout_if_wrong": 0, "loss_if_wrong": spent, "unspent": round(dollars - spent, 2),
                   "break_even_probability_pct": round(result["avg_price"] * 100, 2),
                   "note": "Simulation only; no money moves. Assumes binary settlement at $1 if your side wins and $0 otherwise. "
                           "Before fees; fractional fills are approximated. Break-even is based on execution cost, not a forecast. "
                           "The displayed quote and order book are separate snapshots and may differ."})
    if probability is not None:
        result.update({"your_probability_pct": probability,
                       "expected_profit_at_your_probability": round(probability / 100 * payout - spent, 2)})
    return json.dumps(result)


TICKER = {"type": "string", "description": "Exact market ticker returned by search_markets."}
SIDE = {"type": "string", "enum": ["yes", "no"], "description": "The side the user wants to simulate buying: yes or no."}
TOOLS = [
    {"type": "function", "function": {
        "name": "search_markets",
        "description": "Browse a bounded sample of currently open Kalshi markets. Use for discovery, topics, categories or markets closing today. Returns up to 5 events with one contract each, prices and exact tickers. Not an exhaustive search or trade recommendation.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Optional OR-matched topic keywords, e.g. Mars NASA Moon SpaceX. Empty browses all topics. Use keywords, not a full question."},
            "category": {"type": "string", "description": "Optional exact Kalshi category, case-insensitive, e.g. Sports, Economics, Politics, or Science and Technology. Omit when uncertain; use query instead."},
            "closing_today": {"type": "boolean", "description": "True restricts closing time to now through the next midnight in America/New_York. False means open now, regardless of closing date."},
            }, "required": []}}},
    {"type": "function", "function": {
        "name": "explain_resolution",
        "description": "Get exact contract rules, YES/NO outcome labels, settlement sources and early-close conditions. Use when drilling into a selected market, before its first simulation. Do not infer settlement from its title alone.",
        "parameters": {"type": "object", "properties": {"ticker": TICKER}, "required": ["ticker"]}}},
    {"type": "function", "function": {
        "name": "liquidity_check",
        "description": "Check the quoted price for a USD budget against the live order book, cheapest offers first. Returns average price, slippage, contracts, and whether the budget can be filled. Simulation only, before fees.",
        "parameters": {"type": "object", "properties": {"ticker": TICKER, "side": {**SIDE, "default": "yes"},
            "dollars": {"type": "number", "description": "Finite USD budget greater than 0."}}, "required": ["ticker", "dollars"]}}},
    {"type": "function", "function": {
        "name": "simulate_trade",
        "description": "Simulate a USD budget on YES or NO using live offers. Returns fill, payout and profit if right, loss if wrong, unspent budget and break-even probability. Also calculates expected profit when the user supplies their own probability. Includes liquidity_check internally; do not call both for the same request. No trades or fees.",
        "parameters": {"type": "object", "properties": {"ticker": TICKER, "side": SIDE,
            "dollars": {"type": "number", "description": "Finite USD budget greater than 0."},
            "probability": {"type": "number", "description": "The user's estimate that their chosen side wins, in percent, e.g. 62.5. Include only when the user states it.", "minimum": 0, "maximum": 100}},
            "required": ["ticker", "side", "dollars"]}}},
]
TOOL_MAP = {tool.__name__: tool for tool in (search_markets, explain_resolution, liquidity_check, simulate_trade)}


#-----Dispatch a model-requested tool without exposing exceptions----
def run_tool(name: str, args: dict) -> str:
    if name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool '{name}'. Available: {list(TOOL_MAP)}"})
    try:
        return TOOL_MAP[name](**args)
    except (TypeError, ValueError) as error:
        return json.dumps({"error": f"Invalid arguments or data for {name}: {error}. Check the tool schema and retry."})
    except Exception:
        return json.dumps({"error": f"{name} could not process Kalshi's response. Try another ticker or retry later."})
