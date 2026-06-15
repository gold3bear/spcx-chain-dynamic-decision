#!/usr/bin/env python3
"""Build webreport JSON from the latest installed SPCX final report.

This script keeps Chinese display text in a UTF-8 source file so PowerShell
command encoding cannot corrupt it into question marks.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def gate(ok: bool) -> str:
    return "pass" if ok else "fail"


def build(final_report_path: Path, evidence_path: Path) -> dict:
    final_report = json.loads(final_report_path.read_text(encoding="utf-8"))
    pack = json.loads(evidence_path.read_text(encoding="utf-8"))
    asof = final_report["analysis_as_of"]
    news_scores = (final_report["narrative"]["news_attention"] or {}).get("group_scores") or {}
    poly_scores = ((final_report["narrative"]["polymarket_attention"] or {}).get("normalized") or {})
    wf = {
        "a": max(news_scores.get("group_a_record_ipo") or 0, poly_scores.get("group_a_record_ipo") or 0),
        "b": max(news_scores.get("group_b_ipo_drain_lockup") or 0, poly_scores.get("group_b_ipo_drain_lockup") or 0),
        "c": max(news_scores.get("group_c_tech_concentration_bubble") or 0, poly_scores.get("group_c_tech_concentration_bubble") or 0),
        "d": max(news_scores.get("group_d_vertical_ai") or 0, poly_scores.get("group_d_vertical_ai") or 0),
        "bc_gt_a_consecutive_days": pack["narrative"].get("bc_gt_a_consecutive_days") or 0,
    }

    spcx = pack["market_data"]["SPCX"]
    macro = pack["macro"]
    merger_prob = pack["narrative"]["polymarket_signals"]["tsla_spacex_merger_2026"]

    cards = [
        {
            "id": "spcx_long",
            "label": "SPCX 条件多头",
            "status": "WATCH",
            "direction": "long",
            "gates": {"data": gate(spcx["close"] is not None), "time": "fail", "structure": "fail", "narrative": "na", "rr": "na"},
            "blocking_field": "FOMC/绿鞋期内，RSI_14 不足，未形成合规入场",
            "distance_to_trigger": f"SPCX {spcx['close']} / RSI {spcx['rsi_14']}",
            "invalidation": "宏观冲击或 xAI/Starlink 硬数据恶化则降级",
            "changed_today": False,
        },
        {
            "id": "spcx_phase2_short",
            "label": "SPCX Phase2 空头",
            "status": "FREEZE",
            "direction": "short",
            "gates": {"data": "pass", "time": "fail", "structure": "fail", "narrative": "na", "rr": "na"},
            "blocking_field": "FOMC freeze + 绿鞋 active + 无实际期权链 / borrow",
            "distance_to_trigger": "需 FOMC 结束、绿鞋退潮、期权/borrow 可验证、叙事转 B/C",
            "invalidation": "继续机械买盘并收复高位，或 borrow/put IV 失去可执行性",
            "changed_today": True,
        },
        {
            "id": "rklb",
            "label": "RKLB",
            "status": "FREEZE",
            "direction": "none",
            "gates": {"data": "pass", "time": "fail", "structure": "na", "narrative": "na", "rr": "na"},
            "blocking_field": "RKLB NDX freeze active",
            "distance_to_trigger": "NDX inclusion 后重评估",
            "invalidation": "纳入后价格未形成可交易错位",
            "changed_today": False,
        },
        {
            "id": "asts",
            "label": "ASTS",
            "status": "FREEZE",
            "direction": "none",
            "gates": {"data": "pass", "time": "fail", "structure": "na", "narrative": "na", "rr": "na"},
            "blocking_field": "BlueBird 8-10 launch freeze active",
            "distance_to_trigger": "发射事件落地后重评估",
            "invalidation": "发射失败或事件波动吞噬链条信号",
            "changed_today": False,
        },
        {
            "id": "sats",
            "label": "SATS",
            "status": "WATCH",
            "direction": "none",
            "gates": {"data": "fail", "time": "na", "structure": "fail", "narrative": "na", "rr": "na"},
            "blocking_field": "lockup / tax / transaction path / Starlink hard data 未核清",
            "distance_to_trigger": "需硬数据字段补齐",
            "invalidation": "交易路径或净值假设被证伪",
            "changed_today": False,
        },
        {
            "id": "tsla_spacex_merger",
            "label": "TSLA / SPCX 合并概念",
            "status": "WATCH",
            "direction": "long",
            "gates": {"data": "pass", "time": "na", "structure": "fail", "narrative": "pass", "rr": "fail"},
            "blocking_field": f"无签署协议、无换股比例；Polymarket Dec31 概率 {merger_prob}",
            "distance_to_trigger": "8-K/S-4、特别委员会、换股比例",
            "invalidation": "董事会否认/搁置、诉讼冻结、不利少数股东条款",
            "changed_today": True,
        },
    ]

    dashboards = {
        "spcx": [
            {"metric": "SPCX close", "threshold": "fresh latest session", "value": str(spcx["close"]), "state": "ok"},
            {"metric": "SPCX volume", "threshold": "non-null", "value": str(spcx["volume"]), "state": "ok"},
            {"metric": "RSI_14", "threshold": "required for RSI cards", "value": str(spcx["rsi_14"]), "state": "stale"},
            {"metric": "Options chain", "threshold": "actual", "value": str(pack["instruments"]["spcx_options_available"]), "state": "stale"},
            {"metric": "Borrow", "threshold": "verified fee", "value": str(pack["instruments"]["spcx_borrow_available"]), "state": "stale"},
        ],
        "macro": [
            {"metric": "US10Y", "threshold": "watch high-rate pressure", "value": str(macro["us10y"]), "state": "watch"},
            {"metric": "Brent", "threshold": "oil/geopolitics watch", "value": str(macro["brent"]), "state": "watch"},
            {"metric": "VIX", "threshold": "risk appetite", "value": str(macro["vix"]), "state": "ok"},
            {"metric": "FOMC tone", "threshold": "post statement", "value": str(macro["fomc_tone"]), "state": "stale"},
        ],
        "mapped_stocks": [
            {"metric": t, "threshold": "close / RSI", "value": f"{pack['market_data'][t]['close']} / {pack['market_data'][t]['rsi_14']}", "state": "ok"}
            for t in ["QQQ", "RKLB", "ASTS", "LUNR", "PL", "RDW", "TSLA"]
        ],
        "fundamental": [
            {"metric": "xAI quarterly loss", "threshold": "hard-data gate", "value": str(pack["hard_data"]["xai_quarterly_loss_usd_bn"]), "state": "stale"},
            {"metric": "Starlink monthly net adds", "threshold": "hard-data gate", "value": str(pack["hard_data"]["starlink_monthly_net_adds_mn"]), "state": "stale"},
            {"metric": "OpenAI/Anthropic S-1", "threshold": "supply narrative", "value": str(pack["hard_data"]["openai_or_anthropic_s1_filed"]), "state": "watch"},
        ],
        "sats_gs_supply": [
            {"metric": "SATS lockup terms", "threshold": "known before action", "value": str(pack["hard_data"]["sats_lockup_terms_known"]), "state": "stale"},
            {"metric": "SATS tax leakage", "threshold": "known before action", "value": str(pack["hard_data"]["sats_tax_leakage_known"]), "state": "stale"},
            {"metric": "SATS transaction path", "threshold": "known before action", "value": str(pack["hard_data"]["sats_transaction_path_known"]), "state": "stale"},
        ],
        "merger": [
            {"metric": "TSLA/SPCX merger Dec31 Polymarket", "threshold": "L3 only", "value": str(merger_prob), "state": "watch"},
            {"metric": "Agreement signed", "threshold": "required", "value": str(pack["hard_data"]["tsla_spacex_merger_agreement_signed"]), "state": "stale"},
            {"metric": "Exchange ratio known", "threshold": "required", "value": str(pack["hard_data"]["tsla_spacex_exchange_ratio_known"]), "state": "stale"},
        ],
        "daily_review": [
            {"q": "Can we ACT?", "answer": "No. FOMC freeze, RSI missing, actual options chain missing, borrow unverified."},
            {"q": "Where is attention?", "answer": "News: IPO/record/market cap. Polymarket: IPO month valuation, Starship technical events, TSLA/SPCX merger."},
            {"q": "What changes the decision?", "answer": "Actual options/borrow, FOMC resolution, enough RSI data, and migration from A to B/C narrative."},
        ],
    }

    return {
        "analysis_as_of": asof,
        "report_title": "SPCX 航天链 · 最终博弈地图",
        "overall_stance": "FREEZE · 有数据但不可执行",
        "active_phase": final_report["active_phase"],
        "phase_note": "FOMC freeze + 绿鞋 active + MSCI/NDX pending；结构上仍由机械/日历流主导。",
        "regime": final_report["agent_judgment"]["dominant_regime"],
        "narrative_cycle": "saturation",
        "narrative_wordfreq": wf,
        "narrative_tree": {
            "days": [
                {"date": "2026-06-12", "wordfreq": {"a": 95, "b": 20, "c": 5, "d": 20}},
                {"date": "2026-06-13", "wordfreq": {"a": 100, "b": 35, "c": 5, "d": 55}},
                {"date": asof, "wordfreq": {"a": wf["a"], "b": wf["b"], "c": wf["c"], "d": wf["d"]}},
            ],
            "now": asof,
            "nodes": [
                {"id": "n_ipo", "label": "IPO / 市值神话", "phase": "a", "tense": "past", "date": "2026-06-12", "intensity": 95, "tickers": ["spcx"], "detail": "新闻和 Polymarket 都围绕 IPO、月末市值、首月涨跌定价。"},
                {"id": "n_now", "label": "机械买盘 + 冻结", "phase": "c", "tense": "present", "date": asof, "intensity": 80, "tickers": ["spcx"], "detail": "FOMC freeze、绿鞋、MSCI/NDX pending 使交易结构仍不可执行。"},
                {"id": "f_starship", "label": "技术兑现分叉", "phase": "d", "tense": "future", "date": "2026-07", "intensity": wf["d"], "prob": 0.55, "prob_source": "polymarket_attention:starship-flight-test", "trigger": "Starship/Starlink/AI data-center narrative overtakes IPO valuation", "invalidation": "IPO market-cap markets remain dominant", "expected_return": "mapped space names relative re-rating", "risk": "launch/event binary risk", "tickers": ["rklb", "asts", "sats"]},
                {"id": "f_phase2", "label": "Phase2 空头窗口", "phase": "b", "tense": "future", "date": "2026-07", "intensity": wf["b"], "prob": 0.30, "prob_source": "agent:structure+narrative", "trigger": "FOMC/绿鞋结束 + borrow/options actual + B/C 叙事增强", "invalidation": "继续机械买盘或 borrow/IV 不可执行", "expected_return": "conditional short only after gates pass", "risk": "squeeze / dealer hedging / index flow", "tickers": ["spcx"]},
                {"id": "f_merger", "label": "TSLA / SPCX 合并概念", "phase": "b", "tense": "future", "date": "2026-12-31", "intensity": 48, "prob": merger_prob, "prob_source": "polymarket:tesla-and-spacex-merger-officially-announced-by-december-31", "trigger": "agreement + exchange ratio", "invalidation": "denial/shelving/litigation freeze", "expected_return": "not computable before terms", "risk": "governance conflict and litigation", "tickers": ["tsla"]},
            ],
            "edges": [
                {"from": "n_ipo", "to": "n_now", "tense": "present"},
                {"from": "n_now", "to": "f_starship", "tense": "future", "prob": 0.55},
                {"from": "n_now", "to": "f_phase2", "tense": "future", "prob": 0.30},
                {"from": "n_now", "to": "f_merger", "tense": "future", "prob": merger_prob},
            ],
        },
        "opponent_model": final_report["opponent_model"],
        "timeline": [
            {"date": "2026-06-17", "event": "FOMC decision / press conference + ASTS BlueBird launch", "status": "upcoming"},
            {"date": "2026-06-29", "event": "MSCI fast-track inclusion watch", "status": "upcoming"},
            {"date": "2026-07-06", "event": "NDX fast-entry watch", "status": "upcoming"},
            {"date": "2026-07-12", "event": "Greenshoe 30-day window ends", "status": "upcoming"},
        ],
        "cards": cards,
        "dashboards": dashboards,
        "disclaimer": "Research workflow output only. Not investment advice. Do not trade without verified executable data.",
        "skill_attribution": "spcx-chain-dynamic-decision",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--final-report", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    data = build(Path(args.final_report), Path(args.evidence))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
