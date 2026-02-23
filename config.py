"""Application configuration for the FX monitoring dashboard."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PairConfig:
    symbol: str
    oanda_instrument: str


@dataclass(frozen=True)
class AppConfig:
    pairs: List[PairConfig]
    timeframes: Dict[str, str]
    indicator_windows: Dict[str, int]
    oanda_base_url: str
    oanda_api_token: str
    strength_weights: Dict[str, float]


def load_config() -> AppConfig:
    return AppConfig(
        pairs=[
            PairConfig("USD/JPY", "USD_JPY"),
            PairConfig("CHF/JPY", "CHF_JPY"),
            PairConfig("CAD/JPY", "CAD_JPY"),
            PairConfig("USD/CHF", "USD_CHF"),
            PairConfig("USD/CAD", "USD_CAD"),
        ],
        timeframes={"daily": "D", "h4": "H4"},
        indicator_windows={"ma_fast": 20, "ma_slow": 75, "rsi": 14, "atr": 14},
        oanda_base_url=os.getenv("OANDA_BASE_URL", "https://api-fxpractice.oanda.com/v3"),
        oanda_api_token=os.getenv("OANDA_API_TOKEN", ""),
        strength_weights={
            "h4_return": 0.35,
            "daily_return": 0.30,
            "rsi_slope": 0.20,
            "ma_deviation": 0.15,
        },
    )


WATCHLIST_INSTRUMENTS = {
    "WTI": "WTICO_USD",
    "SP500": "SPX500_USD",
}
