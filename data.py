"""Market data access layer (OANDA + deterministic fallback)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict

import numpy as np
import pandas as pd
import requests

from config import AppConfig, WATCHLIST_INSTRUMENTS


class OandaClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.session = requests.Session()
        if config.oanda_api_token:
            self.session.headers.update({"Authorization": f"Bearer {config.oanda_api_token}"})

    def get_candles(self, instrument: str, granularity: str, count: int = 300) -> pd.DataFrame:
        if not self.config.oanda_api_token:
            return self._fallback_series(instrument, granularity, count)

        url = f"{self.config.oanda_base_url}/instruments/{instrument}/candles"
        params = {"granularity": granularity, "count": count, "price": "M"}
        try:
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            payload = response.json()
            candles = payload.get("candles", [])
            if not candles:
                return self._fallback_series(instrument, granularity, count)

            rows = []
            for c in candles:
                if not c.get("complete", False):
                    continue
                mid = c["mid"]
                rows.append(
                    {
                        "time": pd.to_datetime(c["time"]),
                        "open": float(mid["o"]),
                        "high": float(mid["h"]),
                        "low": float(mid["l"]),
                        "close": float(mid["c"]),
                        "volume": float(c.get("volume", 0)),
                    }
                )
            df = pd.DataFrame(rows)
            if df.empty:
                return self._fallback_series(instrument, granularity, count)
            return df.sort_values("time").reset_index(drop=True)
        except requests.RequestException:
            return self._fallback_series(instrument, granularity, count)

    @staticmethod
    def _fallback_series(instrument: str, granularity: str, count: int) -> pd.DataFrame:
        seed = abs(hash(f"{instrument}-{granularity}")) % (2**32)
        rng = np.random.default_rng(seed)
        end = datetime.now(timezone.utc)
        freq = "4h" if granularity == "H4" else "1D"
        idx = pd.date_range(end=end, periods=count, freq=freq)

        base = 100.0 + rng.uniform(-10, 10)
        noise = rng.normal(0, 0.3, size=count).cumsum()
        close = base + noise
        high = close + np.abs(rng.normal(0.2, 0.05, size=count))
        low = close - np.abs(rng.normal(0.2, 0.05, size=count))
        open_ = close + rng.normal(0, 0.1, size=count)

        return pd.DataFrame(
            {
                "time": idx,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": rng.integers(100, 1000, size=count),
            }
        ).reset_index(drop=True)


def load_market_data(config: AppConfig, bars: int = 300) -> Dict[str, Dict[str, pd.DataFrame]]:
    client = OandaClient(config)
    result: Dict[str, Dict[str, pd.DataFrame]] = {}

    for pair in config.pairs:
        result[pair.symbol] = {
            "daily": client.get_candles(pair.oanda_instrument, config.timeframes["daily"], bars),
            "h4": client.get_candles(pair.oanda_instrument, config.timeframes["h4"], bars),
        }

    for name, instrument in WATCHLIST_INSTRUMENTS.items():
        result[name] = {
            "daily": client.get_candles(instrument, config.timeframes["daily"], bars),
            "h4": client.get_candles(instrument, config.timeframes["h4"], bars),
        }

    return result
