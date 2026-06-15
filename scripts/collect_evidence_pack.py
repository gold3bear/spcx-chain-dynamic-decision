#!/usr/bin/env python3
"""Collect a best-effort SPCX evidence pack from public no-key sources.

This collector intentionally does not fabricate unavailable fields. Public
endpoints can cover daily prices, basic technicals, macro proxies, and some
Polymarket probabilities. Borrow availability and full options-chain quality
usually require licensed brokerage or market-data feeds, so they remain missing
unless a downstream collector fills them.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC))

import spcx_decision_pack

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{query}"
POLYMARKET_PUBLIC_SEARCH_URL = "https://gamma-api.polymarket.com/public-search?{query}"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search?{query}"
YAHOO_FINANCE_HOME_URL = "https://finance.yahoo.com"

TICKERS = ["SPCX", "QQQ", "RKLB", "ASTS", "LUNR", "PL", "RDW", "TSLA"]
SPCX_IPO_DATE = date(2026, 6, 12)
SPCX_GREENSHOE_EXPIRY = SPCX_IPO_DATE + timedelta(days=30)
FOMC_FREEZE_WINDOWS = [
    (date(2026, 6, 6), date(2026, 6, 18)),
    (date(2026, 7, 18), date(2026, 7, 30)),
    (date(2026, 9, 5), date(2026, 9, 17)),
    (date(2026, 10, 17), date(2026, 10, 29)),
    (date(2026, 11, 28), date(2026, 12, 10)),
]
ASTS_BLUEBIRD_LAUNCH_DATE = date(2026, 6, 17)
RKLB_NDX_INCLUSION_DATE = date(2026, 6, 22)
SPCX_MSCI_EFFECTIVE_DATE = date(2026, 6, 29)
SPCX_NDX_FAST_ENTRY_EARLIEST = date(2026, 7, 6)
POLYMARKET_QUERIES = {
    "spcx_end_of_month_closing_market_cap_above_current": (
        "SpaceX", [["spacex", "spcx"], ["ipo"], ["closing", "price"], ["up", "down"]], "Up"
    ),
    "spcx_first_month_close_up": (
        "SpaceX", [["spacex", "spcx"], ["ipo"], ["closing", "price"], ["up", "down"]], "Up"
    ),
    "spcx_day2_open_up": (
        "SpaceX", [["spacex", "spcx"], ["day", "2", "two"], ["open"]], "Up"
    ),
    "spcx_day2_close_up": (
        "SpaceX", [["spacex", "spcx"], ["day", "2", "two"], ["close"]], "Up"
    ),
    "spcx_ndx_inclusion_2026": (
        "SpaceX", [["spacex", "spcx"], ["nasdaq", "ndx", "100"], ["inclusion"]], "Yes"
    ),
    "spcx_sp500_inclusion_2026": (
        "SpaceX", [["spacex", "spcx"], ["s&p", "sp500", "500"], ["inclusion"]], "Yes"
    ),
    "spcx_volatility_halt_first_month": (
        "SpaceX", [["spacex", "spcx"], ["halt", "volatility"]], "Yes"
    ),
    "spcx_vs_openai_higher_ipo_marketcap": (
        "SpaceX OpenAI", [["spacex", "spcx"], ["openai"], ["ipo", "market", "cap"]], "Yes"
    ),
    "openai_or_anthropic_s1_filed": (
        "OpenAI Anthropic", [["openai", "anthropic"], ["s-1", "s1", "ipo"]], "Yes"
    ),
    "google_x_spacex_space_data_center": (
        "Google SpaceX", [["google"], ["spacex", "spcx"], ["data", "center"]], "Yes"
    ),
    "tsla_spacex_merger_2026": (
        "Tesla SpaceX merger", [["tesla", "tsla"], ["spacex", "spcx"], ["merger", "merge"], ["december"], ["31"]], "Yes"
    ),
}
NARRATIVE_KEYWORDS = {
    "group_a_record_ipo": [
        "ipo", "market cap", "closing price", "up/down", "first month", "trillion", "record",
    ],
    "group_b_ipo_drain_lockup": [
        "merger", "tesla", "announced", "lockup", "unlock", "sell", "offering", "s-1", "s1",
    ],
    "group_c_tech_concentration_bubble": [
        "halt", "volatility", "bubble", "valuation", "nasdaq", "s&p", "sp500", "index", "inclusion",
    ],
    "group_d_vertical_ai": [
        "google", "data center", "starship", "starlink", "flight test", "dock", "ai",
    ],
}
FRONTPAGE_KEYWORDS = {
    **NARRATIVE_KEYWORDS,
    "macro_market": [
        "fed", "fomc", "rates", "yields", "inflation", "oil", "vix", "tariff", "jobs",
        "recession", "market", "stocks", "nasdaq", "s&p", "dow",
    ],
}


def fetch_json(url: str, timeout: float = 12.0) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "spcx-chain-dynamic-decision/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url: str, timeout: float = 12.0) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "spcx-chain-dynamic-decision/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_outcome_probability(market: dict[str, Any], target_outcome: str) -> float | None:
    outcomes = market.get("outcomes")
    prices = market.get("outcomePrices")
    if isinstance(outcomes, str):
        try:
            outcomes = json.loads(outcomes)
        except ValueError:
            return None
    if isinstance(prices, str):
        try:
            prices = json.loads(prices)
        except ValueError:
            return None
    if not isinstance(outcomes, list) or not isinstance(prices, list):
        return None
    target = target_outcome.strip().lower()
    for outcome, price in zip(outcomes, prices):
        if str(outcome).strip().lower() == target:
            try:
                return float(price)
            except (TypeError, ValueError):
                return None
    return None


def market_matches(market: dict[str, Any], required_groups: list[list[str]]) -> bool:
    text = " ".join(
        str(market.get(key) or "")
        for key in ("question", "title", "slug", "description", "eventSlug")
    ).lower()
    return all(any(term in text for term in group) for group in required_groups)


def iter_public_search_markets(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    markets: list[dict[str, Any]] = []
    for event in payload.get("events") or []:
        if not isinstance(event, dict):
            continue
        for market in event.get("markets") or []:
            if isinstance(market, dict):
                markets.append(market)
    for market in payload.get("markets") or []:
        if isinstance(market, dict):
            markets.append(market)
    return markets


def fetch_polymarket_probability(
    search: str, required_groups: list[list[str]], target_outcome: str
) -> tuple[float | None, str | None]:
    query = urllib.parse.urlencode({"q": search, "limit": 20})
    payload = fetch_json(POLYMARKET_PUBLIC_SEARCH_URL.format(query=query))
    markets = iter_public_search_markets(payload)
    if not markets:
        return None, None
    for market in markets:
        if not market_matches(market, required_groups):
            continue
        prob = parse_outcome_probability(market, target_outcome)
        if prob is not None:
            return round(prob, 4), str(market.get("slug") or market.get("question") or search)
    return None, None


def fetch_polymarket_public_search(query_text: str, limit: int = 20) -> Any:
    query = urllib.parse.urlencode({"q": query_text, "limit": limit})
    return fetch_json(POLYMARKET_PUBLIC_SEARCH_URL.format(query=query))


def collect_polymarket_texts(payload: Any) -> list[dict[str, str]]:
    if not isinstance(payload, dict):
        return []
    rows: list[dict[str, str]] = []
    for event in payload.get("events") or []:
        if not isinstance(event, dict):
            continue
        event_title = str(event.get("title") or event.get("slug") or "")
        event_slug = str(event.get("slug") or "")
        rows.append({
            "kind": "event",
            "title": event_title,
            "slug": event_slug,
            "created_at": str(event.get("createdAt") or event.get("creationDate") or ""),
            "updated_at": str(event.get("updatedAt") or ""),
        })
        for market in event.get("markets") or []:
            if isinstance(market, dict):
                rows.append({
                    "kind": "market",
                    "title": str(market.get("question") or market.get("title") or market.get("slug") or ""),
                    "slug": str(market.get("slug") or ""),
                    "created_at": str(market.get("createdAt") or market.get("creationDate") or ""),
                    "updated_at": str(market.get("updatedAt") or ""),
                })
    return rows


def score_narrative_attention(rows: list[dict[str, str]]) -> dict[str, Any]:
    return score_attention(rows, NARRATIVE_KEYWORDS, require_spacex=True)


def score_attention(rows: list[dict[str, str]], keyword_groups: dict[str, list[str]], require_spacex: bool) -> dict[str, Any]:
    raw_scores = {key: 0 for key in keyword_groups}
    matched_terms: dict[str, list[str]] = {key: [] for key in keyword_groups}
    carrier_titles: list[str] = []
    for row in rows:
        text_parts = [row.get("title", ""), row.get("source", "")]
        if row.get("kind") != "news":
            text_parts.append(row.get("slug", ""))
        text = " ".join(text_parts).lower()
        if require_spacex and "spacex" not in text and "spcx" not in text:
            continue
        if len(carrier_titles) < 8:
            carrier_titles.append(row.get("title", ""))
        for group, keywords in keyword_groups.items():
            for keyword in keywords:
                if keyword in text:
                    raw_scores[group] += 1
                    if keyword not in matched_terms[group]:
                        matched_terms[group].append(keyword)
    max_score = max(raw_scores.values()) if raw_scores else 0
    normalized = {
        key: (round((value / max_score) * 100) if max_score else None)
        for key, value in raw_scores.items()
    }
    if "group_b_ipo_drain_lockup" in raw_scores and "group_c_tech_concentration_bubble" in raw_scores:
        bc_score = raw_scores["group_b_ipo_drain_lockup"] + raw_scores["group_c_tech_concentration_bubble"]
        bc_gt_a = 1 if bc_score > raw_scores["group_a_record_ipo"] and raw_scores["group_a_record_ipo"] > 0 else 0
    else:
        bc_gt_a = 0
    return {
        "raw_scores": raw_scores,
        "normalized": normalized,
        "matched_terms": matched_terms,
        "carrier_titles": carrier_titles,
        "bc_gt_a_consecutive_days_proxy": bc_gt_a,
    }


def collect_google_news_rows(query_text: str = "SpaceX SPCX IPO", limit: int = 30) -> list[dict[str, str]]:
    query = urllib.parse.urlencode({"q": query_text, "hl": "en-US", "gl": "US", "ceid": "US:en"})
    xml_text = fetch_text(GOOGLE_NEWS_RSS_URL.format(query=query))
    root = ET.fromstring(xml_text)
    rows: list[dict[str, str]] = []
    for item in root.findall(".//item")[:limit]:
        title = html.unescape(item.findtext("title") or "")
        link = item.findtext("link") or ""
        pub_date = item.findtext("pubDate") or ""
        source_el = item.find("source")
        source = source_el.text if source_el is not None and source_el.text else ""
        rows.append({
            "kind": "news",
            "title": title,
            "slug": link,
            "created_at": pub_date,
            "updated_at": pub_date,
            "source": source,
        })
    return rows


def extract_yahoo_finance_frontpage_rows(limit: int = 80) -> list[dict[str, str]]:
    text = fetch_text(YAHOO_FINANCE_HOME_URL, timeout=20)
    candidates: list[str] = []
    patterns = [
        r'<h[1-4][^>]*>(.*?)</h[1-4]>',
        r'aria-label="([^"]{20,180})"',
        r'"title"\s*:\s*"([^"]{20,180})"',
        r'"headline"\s*:\s*"([^"]{20,180})"',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I | re.S):
            value = re.sub(r"<[^>]+>", " ", match.group(1))
            value = html.unescape(value)
            value = re.sub(r"\s+", " ", value).strip()
            if len(value) < 20:
                continue
            candidates.append(value)
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for title in candidates:
        lowered = title.lower()
        if title in seen:
            continue
        if any(skip in lowered for skip in ("cookie", "privacy", "advertisement", "sign in")):
            continue
        seen.add(title)
        rows.append({"kind": "frontpage", "title": title, "slug": YAHOO_FINANCE_HOME_URL, "source": "Yahoo Finance"})
        if len(rows) >= limit:
            break
    return rows


def collect_google_news_rows_many(queries: list[str], per_query_limit: int = 15) -> list[dict[str, str]]:
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    for query_text in queries:
        for row in collect_google_news_rows(query_text, limit=per_query_limit):
            key = row.get("title") or row.get("slug") or ""
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def collect_news_attention(pack: dict[str, Any], warnings: list[str], sources: dict[str, str]) -> None:
    try:
        rows = collect_google_news_rows()
        attention = score_narrative_attention(rows)
    except Exception as exc:
        warnings.append(f"narrative.news_attention: {exc}")
        return
    pack["computed"]["news_attention"] = attention
    pack["narrative"]["news_attention"] = {
        "status": "loaded",
        "source": "Google News RSS search",
        "query": "SpaceX SPCX IPO",
        "group_scores": attention["normalized"],
        "matched_terms": attention["matched_terms"],
        "carrier_titles": attention["carrier_titles"],
    }
    sources["narrative.news_attention"] = "Google News RSS search q='SpaceX SPCX IPO'"


def collect_frontpage_attention(pack: dict[str, Any], warnings: list[str], sources: dict[str, str]) -> None:
    try:
        rows = extract_yahoo_finance_frontpage_rows()
        attention = score_attention(rows, FRONTPAGE_KEYWORDS, require_spacex=False)
    except Exception as exc:
        warnings.append(f"narrative.frontpage_attention: {exc}")
        return
    pack["computed"]["frontpage_attention"] = attention
    pack["narrative"]["frontpage_attention"] = {
        "status": "loaded",
        "source": "Yahoo Finance front page",
        "group_scores": attention["normalized"],
        "matched_terms": attention["matched_terms"],
        "carrier_titles": attention["carrier_titles"],
    }
    sources["narrative.frontpage_attention"] = "Yahoo Finance homepage headline/metadata extraction"


def collect_instrument_research(pack: dict[str, Any], warnings: list[str], sources: dict[str, str]) -> None:
    """Collect public instrument-status signals without promoting them to actual tradability."""
    try:
        options_rows = collect_google_news_rows_many([
            "SpaceX options trading Cboe Tuesday",
            "SPCX options chain Cboe OCC",
            "SpaceX stock options begin trading",
        ])
    except Exception as exc:
        warnings.append(f"instruments.options_research: {exc}")
        options_rows = []
    try:
        borrow_rows = collect_google_news_rows_many([
            "SPCX borrow fee short availability",
            "SpaceX short borrow fee Fintel",
            "SPCX IBorrowDesk borrow available",
        ])
    except Exception as exc:
        warnings.append(f"instruments.borrow_research: {exc}")
        borrow_rows = []

    def relevant_titles(rows: list[dict[str, str]], topic_terms: tuple[str, ...]) -> list[str]:
        titles: list[str] = []
        for row in rows:
            title = row["title"]
            text = title.lower()
            if not ("spacex" in text or "spcx" in text):
                continue
            if not any(term in text for term in topic_terms):
                continue
            titles.append(title)
        return titles

    option_titles = relevant_titles(options_rows, ("option", "cboe", "occ", "contract"))
    borrow_titles = relevant_titles(borrow_rows, ("borrow", "short", "loan", "availability", "fee"))
    options_expected = any(
        any(term in title.lower() for term in ("option", "cboe", "occ"))
        for title in option_titles
    )
    borrow_public_page_found = any(
        any(term in title.lower() for term in ("borrow", "short interest", "short sale", "fintel", "iborrow"))
        for title in borrow_titles
    )

    pack["computed"]["instrument_research"] = {
        "options_expected_from_public_news": options_expected,
        "options_status": (
            "Public news/search indicates SPCX options may list or are expected, but collector did not verify an actual option chain."
            if options_expected
            else "No public options-listing signal found in news search."
        ),
        "options_carriers": option_titles[:8],
        "borrow_public_page_found": borrow_public_page_found,
        "borrow_status": (
            "Public search found borrow/short-interest references, but collector did not verify executable borrow availability or fee."
            if borrow_public_page_found
            else "No public borrow-fee signal found in news search."
        ),
        "borrow_carriers": borrow_titles[:8],
        "actionability": "research_only_not_ACT_grade",
    }
    sources["computed.instrument_research"] = "Google News RSS searches for SPCX options and borrow availability"


def parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def recent_polymarket_rows(
    rows: list[dict[str, str]], today: date, days: int = 3, mode: str = "created"
) -> list[dict[str, str]]:
    recent: list[dict[str, str]] = []
    for row in rows:
        created = parse_iso_datetime(row.get("created_at", ""))
        updated = parse_iso_datetime(row.get("updated_at", ""))
        event_time = created if mode == "created" else (updated or created)
        if event_time is None:
            continue
        age_days = (today - event_time.date()).days
        if 0 <= age_days <= days:
            recent.append({
                "kind": row.get("kind", ""),
                "title": row.get("title", ""),
                "slug": row.get("slug", ""),
                "created_at": row.get("created_at", ""),
                "updated_at": row.get("updated_at", ""),
                "age_days": str(age_days),
                "mode": mode,
            })
    return recent[:20]


def rsi_14(closes: list[float]) -> float | None:
    if len(closes) < 15:
        return None
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    seed = deltas[:14]
    avg_gain = sum(max(delta, 0.0) for delta in seed) / 14
    avg_loss = sum(max(-delta, 0.0) for delta in seed) / 14
    for delta in deltas[14:]:
        gain = max(delta, 0.0)
        loss = max(-delta, 0.0)
        avg_gain = ((avg_gain * 13) + gain) / 14
        avg_loss = ((avg_loss * 13) + loss) / 14
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def fetch_yahoo_daily(symbol: str, range_: str = "3mo") -> tuple[dict[str, Any] | None, str | None]:
    query = urllib.parse.urlencode({"range": range_, "interval": "1d"})
    url = YAHOO_CHART_URL.format(symbol=urllib.parse.quote(symbol), query=query)
    payload = fetch_json(url)
    result = (((payload or {}).get("chart") or {}).get("result") or [None])[0]
    if not isinstance(result, dict):
        return None, "missing chart result"
    timestamps = result.get("timestamp") or []
    quote = (((result.get("indicators") or {}).get("quote") or [None])[0]) or {}
    meta = result.get("meta") or {}
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []
    valid: list[tuple[int, float, int | None]] = []
    for ts, close, volume in zip(timestamps, closes, volumes):
        if close is None:
            continue
        try:
            valid.append((int(ts), float(close), None if volume is None else int(volume)))
        except (TypeError, ValueError):
            continue
    if not valid:
        return None, "no daily closes"
    ts, close, volume = valid[-1]
    close_series = [row[1] for row in valid]
    regular_price = meta.get("regularMarketPrice")
    try:
        last_price = float(regular_price) if regular_price is not None else close
    except (TypeError, ValueError):
        last_price = close
    return {
        "last_price": round(last_price, 4),
        "close": round(close, 4),
        "rsi_14": rsi_14(close_series),
        "volume": volume,
        "vwap": None,
        "data_timestamp": datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat(),
    }, None


def collect_prices(pack: dict[str, Any], warnings: list[str], sources: dict[str, str]) -> None:
    for ticker in TICKERS:
        try:
            block, error = fetch_yahoo_daily(ticker)
        except Exception as exc:
            block, error = None, str(exc)
        if block:
            pack["market_data"][ticker].update(block)
            sources[f"market_data.{ticker}"] = "Yahoo Finance chart endpoint"
        else:
            warnings.append(f"market_data.{ticker}: {error}")


def collect_macro(pack: dict[str, Any], warnings: list[str], sources: dict[str, str]) -> None:
    macro_specs = {
        "us10y": ("^TNX", lambda value: round(value, 4)),
        "vix": ("^VIX", lambda value: round(value, 4)),
        "brent": ("BZ=F", lambda value: round(value, 4)),
    }
    timestamps: list[str] = []
    for field, (symbol, transform) in macro_specs.items():
        try:
            block, error = fetch_yahoo_daily(symbol)
        except Exception as exc:
            block, error = None, str(exc)
        if not block:
            warnings.append(f"macro.{field}: {error}")
            continue
        value = block.get("last_price")
        if isinstance(value, (int, float)) and math.isfinite(float(value)):
            pack["macro"][field] = transform(float(value))
            timestamps.append(str(block["data_timestamp"]))
            sources[f"macro.{field}"] = f"Yahoo Finance chart endpoint ({symbol})"
    if timestamps:
        pack["macro"]["data_timestamp"] = max(timestamps)


def collect_market_session(pack: dict[str, Any]) -> None:
    timestamps = [
        block.get("data_timestamp")
        for block in pack.get("market_data", {}).values()
        if isinstance(block, dict) and block.get("data_timestamp")
    ]
    if timestamps:
        last_close = max(str(ts) for ts in timestamps)
        pack["market_session"]["last_close_date"] = last_close
        pack["market_session"]["is_trading_day"] = last_close == pack.get("analysis_as_of")


def in_window(day: date, start: date, end: date) -> bool:
    return start <= day <= end


def collect_calendar(pack: dict[str, Any], sources: dict[str, str]) -> None:
    analysis_day = date.fromisoformat(pack["analysis_as_of"])
    fomc_freeze = any(in_window(analysis_day, start, end) for start, end in FOMC_FREEZE_WINDOWS)
    greenshoe_active = SPCX_IPO_DATE <= analysis_day <= SPCX_GREENSHOE_EXPIRY
    msci_pending = analysis_day < SPCX_MSCI_EFFECTIVE_DATE
    ndx_pending = analysis_day < SPCX_NDX_FAST_ENTRY_EARLIEST
    rklb_freeze = analysis_day < RKLB_NDX_INCLUSION_DATE
    asts_freeze = analysis_day <= ASTS_BLUEBIRD_LAUNCH_DATE

    if fomc_freeze:
        phase_hint = "phase_0"
    elif greenshoe_active or msci_pending or ndx_pending:
        phase_hint = "phase_1"
    elif analysis_day <= date(2026, 8, 31):
        phase_hint = "phase_2"
    else:
        phase_hint = "post_august_reassessment"

    pack["calendar"].update({
        "fomc_freeze_active": fomc_freeze,
        "greenshoe_active": greenshoe_active,
        "msci_inclusion_pending": msci_pending,
        "ndx_inclusion_pending": ndx_pending,
        "rklb_ndx_freeze_active": rklb_freeze,
        "asts_launch_freeze_active": asts_freeze,
        "phase_hint": phase_hint,
    })
    sources.update({
        "calendar.fomc_freeze_active": "Chicago Fed 2026 FOMC blackout windows; June 6-18 active around June 16-17 FOMC",
        "calendar.greenshoe_active": "SPCX IPO date 2026-06-12 plus standard 30-day greenshoe window",
        "calendar.msci_inclusion_pending": "MSCI large-IPO fast-track effective-date watch; configured SPCX effective date 2026-06-29",
        "calendar.ndx_inclusion_pending": "Nasdaq-100 fast-entry watch; configured earliest SPCX date 2026-07-06",
        "calendar.rklb_ndx_freeze_active": "Configured RKLB NDX inclusion watch date 2026-06-22",
        "calendar.asts_launch_freeze_active": "AST SpaceMobile BlueBird 8-10 launch scheduled 2026-06-17",
        "calendar.phase_hint": "Derived from FOMC freeze, greenshoe, MSCI/NDX pending, and post-greenshoe phase rules",
    })


def collect_polymarket(pack: dict[str, Any], warnings: list[str], sources: dict[str, str]) -> None:
    pm = pack["narrative"]["polymarket_signals"]
    loaded: list[str] = []
    search_payload = None
    try:
        search_payload = fetch_polymarket_public_search("SpaceX")
        rows = collect_polymarket_texts(search_payload)
        attention = score_narrative_attention(rows)
        normalized = attention["normalized"]
        for field in NARRATIVE_KEYWORDS:
            if normalized.get(field) is not None:
                pack["narrative"][field] = normalized[field]
        pack["narrative"]["bc_gt_a_consecutive_days"] = attention["bc_gt_a_consecutive_days_proxy"]
        pack["narrative"]["high_quality_carriers"] = [
            f"Polymarket: {title}" for title in attention["carrier_titles"] if title
        ]
        pack["computed"]["polymarket_attention"] = attention
        pack["computed"]["polymarket_new_markets"] = recent_polymarket_rows(rows, date.today(), days=3, mode="created")
        pack["computed"]["polymarket_recent_markets"] = recent_polymarket_rows(rows, date.today(), days=3, mode="updated")
        sources["narrative.polymarket_attention"] = "Polymarket Gamma public-search q=SpaceX titles/questions"
        sources["computed.polymarket_new_markets"] = "Polymarket Gamma public-search q=SpaceX createdAt/updatedAt"
        sources["computed.polymarket_recent_markets"] = "Polymarket Gamma public-search q=SpaceX updatedAt"
    except Exception as exc:
        warnings.append(f"narrative.polymarket_attention: {exc}")
    for field, (search, required_groups, target_outcome) in POLYMARKET_QUERIES.items():
        try:
            if search == "SpaceX" and search_payload is not None:
                markets = iter_public_search_markets(search_payload)
                prob, source = None, None
                for market in markets:
                    if not market_matches(market, required_groups):
                        continue
                    prob = parse_outcome_probability(market, target_outcome)
                    if prob is not None:
                        prob = round(prob, 4)
                        source = str(market.get("slug") or market.get("question") or search)
                        break
            else:
                prob, source = fetch_polymarket_probability(search, required_groups, target_outcome)
        except Exception as exc:
            warnings.append(f"narrative.polymarket_signals.{field}: {exc}")
            continue
        if prob is not None:
            pm[field] = prob
            if source:
                loaded.append(f"{field}={source}")
    if loaded:
        pm["data_timestamp"] = pack["analysis_as_of"]
        pm["tldr"] = "; ".join(loaded[:5])
        sources["narrative.polymarket_signals"] = "Polymarket Gamma API public market search"
    else:
        warnings.append("narrative.polymarket_signals: no matching active markets found")


def collect() -> dict[str, Any]:
    pack = spcx_decision_pack.template()
    pack["analysis_as_of"] = date.today().isoformat()
    warnings: list[str] = []
    sources: dict[str, str] = {}
    collect_prices(pack, warnings, sources)
    collect_macro(pack, warnings, sources)
    collect_market_session(pack)
    collect_calendar(pack, sources)
    collect_polymarket(pack, warnings, sources)
    collect_news_attention(pack, warnings, sources)
    collect_frontpage_attention(pack, warnings, sources)
    collect_instrument_research(pack, warnings, sources)
    pack["computed"]["collector_warnings"] = warnings
    pack["computed"]["data_sources"] = sources
    return pack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/SPCX_chain_evidence_latest.json")
    parser.add_argument("--validate", action="store_true", help="validate after writing")
    args = parser.parse_args()

    pack = collect()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(pack, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(out)}, ensure_ascii=False))
    if args.validate:
        result = spcx_decision_pack.validate(pack)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["valid"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
