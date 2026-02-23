"""Streamlit dashboard for discretionary FX monitoring."""

from __future__ import annotations

from typing import Dict

import pandas as pd
import streamlit as st

from ai_model import PairAIPredictor
from alerts import calc_entry_score, score_label, score_to_stars
from config import load_config
from data import load_market_data
from environment import build_environment_summary, detect_market_regime
from indicators import add_indicators, atr_warning, pullback_signal, trend_direction
from strength import compute_currency_strength

st.set_page_config(page_title="FX Monitor", layout="wide")


@st.cache_data(ttl=60 * 20)
def prepare_data() -> Dict[str, Dict[str, pd.DataFrame]]:
    config = load_config()
    market_data = load_market_data(config)
    for name, tf_data in market_data.items():
        market_data[name]["daily"] = add_indicators(tf_data["daily"])
        market_data[name]["h4"] = add_indicators(tf_data["h4"])
    return market_data


def main() -> None:
    config = load_config()
    market_data = prepare_data()
    strength_df = compute_currency_strength(market_data, config)
    predictor = PairAIPredictor()

    score_map = dict(zip(strength_df["currency"], strength_df["score"]))
    market_regime = detect_market_regime(market_data["SP500"]["daily"], score_map.get("JPY", 0.0), score_map.get("CHF", 0.0))

    pair_overview = {}
    detailed_rows = []

    for pair in [p.symbol for p in config.pairs]:
        daily = market_data[pair]["daily"]
        h4 = market_data[pair]["h4"]

        d_trend = trend_direction(daily)
        h4_trend = trend_direction(h4)
        pullback_ok = pullback_signal(h4, d_trend)
        atr_alert = atr_warning(h4)

        base, quote = pair.split("/")
        strength_match = score_map.get(base, 0.0) > score_map.get(quote, 0.0)

        features = {
            "daily_ma_dev": float(daily["ma_deviation"].iloc[-1]),
            "h4_rsi": float(h4["rsi"].iloc[-1]),
            "h4_atr": float(h4["atr"].iloc[-1]),
            "h4_ret_1": float(h4["close"].pct_change(1).iloc[-1]),
            "h4_ret_2": float(h4["close"].pct_change(2).iloc[-1]),
            "h4_ret_3": float(h4["close"].pct_change(3).iloc[-1]),
            "strength_score": float(score_map.get(base, 0.0) - score_map.get(quote, 0.0)),
            "spx_return": float(market_data["SP500"]["daily"]["close"].pct_change(1).iloc[-1]),
            "oil_return": float(market_data["WTI"]["daily"]["close"].pct_change(1).iloc[-1]),
        }
        probs = predictor.predict_proba(features)

        score = calc_entry_score(
            trend_match=(d_trend == h4_trend and d_trend != "中立"),
            pullback_match=pullback_ok,
            strength_match=strength_match,
            ai_prob_up=probs["up"],
        )
        pair_overview[pair] = float(score)

        last = h4.iloc[-1]
        y_high = daily["high"].iloc[-2] if len(daily) >= 2 else daily["high"].iloc[-1]
        y_low = daily["low"].iloc[-2] if len(daily) >= 2 else daily["low"].iloc[-1]

        detailed_rows.append(
            {
                "pair": pair,
                "日足トレンド": d_trend,
                "4Hトレンド": h4_trend,
                "RSI": round(float(last["rsi"]), 1),
                "ATR": round(float(last["atr"]), 3),
                "前日高値距離": round(float((last["close"] - y_high) / y_high * 100), 2),
                "前日安値距離": round(float((last["close"] - y_low) / y_low * 100), 2),
                "AI上昇%": round(probs["up"] * 100, 1),
                "AI下降%": round(probs["down"] * 100, 1),
                "総合評価": score_label(score),
                "エントリー優位性": score_to_stars(score),
                "ATR警告": "⚠️" if atr_alert else "",
            }
        )

    summary = build_environment_summary(strength_df, pair_overview, market_regime)

    st.title("FX 監視ダッシュボード")
    st.caption("1日3回チェック用（朝・昼・夜）")

    st.subheader("① 市場環境サマリー")
    cols = st.columns(5)
    cols[0].metric("市場環境", summary["market"])
    cols[1].metric("円", summary["JPY"])
    cols[2].metric("CHF", summary["CHF"])
    cols[3].metric("CAD", summary["CAD"])
    cols[4].metric("本日優位", summary["focus"])

    st.subheader("② 通貨強弱ヒートマップ")
    styled = strength_df.set_index("currency")[["score_norm"]].style.background_gradient(cmap="RdYlGn")
    st.dataframe(styled, use_container_width=True)
    st.dataframe(strength_df, use_container_width=True)

    st.subheader("③ 通貨ペア詳細")
    detail_df = pd.DataFrame(detailed_rows).sort_values("AI上昇%", ascending=False)
    st.dataframe(detail_df, use_container_width=True)

    st.info("裁量補助ツールです。自動売買は行いません。")


if __name__ == "__main__":
    main()
