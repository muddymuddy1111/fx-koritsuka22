"""Currency strength scoring and ranking."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Tuple

import pandas as pd

from config import AppConfig


def _pair_to_ccy(pair: str) -> Tuple[str, str]:
    base, quote = pair.split("/")
    return base, quote


def pair_strength_features(daily_df: pd.DataFrame, h4_df: pd.DataFrame) -> Dict[str, float]:
    return {
        "h4_return": float(h4_df["close"].pct_change(1).iloc[-1]),
        "daily_return": float(daily_df["close"].pct_change(1).iloc[-1]),
        "rsi_slope": float(h4_df["rsi_slope"].iloc[-1]),
        "ma_deviation": float(h4_df["ma_deviation"].iloc[-1]),
    }


def compute_currency_strength(
    pair_data: Dict[str, Dict[str, pd.DataFrame]], config: AppConfig, currencies: Iterable[str] = ("USD", "JPY", "CHF", "CAD")
) -> pd.DataFrame:
    scores = defaultdict(float)
    counts = defaultdict(int)

    for pair in [p.symbol for p in config.pairs]:
        base, quote = _pair_to_ccy(pair)
        feats = pair_strength_features(pair_data[pair]["daily"], pair_data[pair]["h4"])
        weighted = sum(feats[k] * w for k, w in config.strength_weights.items())
        scores[base] += weighted
        scores[quote] -= weighted
        counts[base] += 1
        counts[quote] += 1

    rows = []
    for ccy in currencies:
        norm = scores[ccy] / counts[ccy] if counts[ccy] else 0.0
        rows.append({"currency": ccy, "score": norm})

    df = pd.DataFrame(rows).sort_values("score", ascending=False).reset_index(drop=True)
    min_v, max_v = df["score"].min(), df["score"].max()
    if max_v - min_v > 0:
        df["score_norm"] = (df["score"] - min_v) / (max_v - min_v)
    else:
        df["score_norm"] = 0.5
    return df
