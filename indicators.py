"""Technical indicator calculations."""

from __future__ import annotations

import pandas as pd
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from ta.trend import SMAIndicator


def add_indicators(df: pd.DataFrame, ma_fast: int = 20, ma_slow: int = 75, rsi_window: int = 14, atr_window: int = 14) -> pd.DataFrame:
    out = df.copy()
    out["ma_fast"] = SMAIndicator(close=out["close"], window=ma_fast).sma_indicator()
    out["ma_slow"] = SMAIndicator(close=out["close"], window=ma_slow).sma_indicator()
    out["rsi"] = RSIIndicator(close=out["close"], window=rsi_window).rsi()
    out["atr"] = AverageTrueRange(
        high=out["high"], low=out["low"], close=out["close"], window=atr_window
    ).average_true_range()
    out["ret_1"] = out["close"].pct_change(1)
    out["ret_3"] = out["close"].pct_change(3)
    out["ma_deviation"] = (out["close"] - out["ma_fast"]) / out["ma_fast"]
    out["rsi_slope"] = out["rsi"].diff(3)
    return out


def trend_direction(df: pd.DataFrame) -> str:
    latest = df.iloc[-1]
    if latest["ma_fast"] > latest["ma_slow"]:
        return "上昇"
    if latest["ma_fast"] < latest["ma_slow"]:
        return "下降"
    return "中立"


def pullback_signal(h4_df: pd.DataFrame, daily_trend: str) -> bool:
    latest = h4_df.iloc[-1]
    in_zone = 40 <= latest["rsi"] <= 60
    trend_ok = (daily_trend == "上昇" and latest["ma_fast"] > latest["ma_slow"]) or (
        daily_trend == "下降" and latest["ma_fast"] < latest["ma_slow"]
    )
    return bool(in_zone and trend_ok)


def atr_warning(h4_df: pd.DataFrame) -> bool:
    latest = h4_df["atr"].iloc[-1]
    baseline = h4_df["atr"].rolling(20).mean().iloc[-1]
    return bool(latest > baseline * 1.35 if pd.notna(baseline) and baseline > 0 else False)
