"""Market regime and high-level summary generation."""

from __future__ import annotations

from typing import Dict

import pandas as pd


def _latest_return(df: pd.DataFrame, bars: int = 3) -> float:
    if len(df) <= bars:
        return 0.0
    return float(df["close"].iloc[-1] / df["close"].iloc[-(bars + 1)] - 1)


def classify_strength(score: float, threshold: float = 0.0) -> str:
    if score > threshold:
        return "強い"
    if score < -threshold:
        return "弱い"
    return "中立"


def detect_market_regime(sp500_daily: pd.DataFrame, jpy_score: float, chf_score: float) -> str:
    spx_momentum = _latest_return(sp500_daily, bars=3)
    safe_haven_pressure = (jpy_score + chf_score) / 2
    if spx_momentum > 0 and safe_haven_pressure < 0:
        return "リスクオン"
    if spx_momentum < 0 and safe_haven_pressure > 0:
        return "リスクオフ"
    return "中立"


def build_environment_summary(strength_df: pd.DataFrame, pair_signals: Dict[str, str], market_regime: str) -> Dict[str, str]:
    score_map = dict(zip(strength_df["currency"], strength_df["score"]))
    top_pair = max(pair_signals, key=pair_signals.get) if pair_signals else "候補なし"
    return {
        "market": market_regime,
        "JPY": classify_strength(score_map.get("JPY", 0.0)),
        "CHF": classify_strength(score_map.get("CHF", 0.0)),
        "CAD": classify_strength(score_map.get("CAD", 0.0)),
        "focus": top_pair,
    }
