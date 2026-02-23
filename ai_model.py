"""Simple ML-based directional probability estimator."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = Path("models/random_forest.joblib")

FEATURE_COLUMNS = [
    "daily_ma_dev",
    "h4_rsi",
    "h4_atr",
    "h4_ret_1",
    "h4_ret_2",
    "h4_ret_3",
    "strength_score",
    "spx_return",
    "oil_return",
]


class PairAIPredictor:
    def __init__(self) -> None:
        self.model = self._load_or_init_model()

    def _load_or_init_model(self):
        if MODEL_PATH.exists():
            return joblib.load(MODEL_PATH)

        model = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
        X_seed, y_seed = self._synthetic_seed_data(800)
        model.fit(X_seed, y_seed)
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, MODEL_PATH)
        return model

    @staticmethod
    def _synthetic_seed_data(n: int):
        rng = np.random.default_rng(42)
        X = rng.normal(size=(n, len(FEATURE_COLUMNS)))
        y = (X[:, 0] * 0.6 + X[:, 1] * 0.25 - X[:, 2] * 0.15 + X[:, 6] * 0.2 + rng.normal(0, 0.5, n) > 0).astype(int)
        return X, y

    def predict_proba(self, feature_row: Dict[str, float]) -> Dict[str, float]:
        x = pd.DataFrame([{k: feature_row.get(k, 0.0) for k in FEATURE_COLUMNS}], columns=FEATURE_COLUMNS)
        probs = self.model.predict_proba(x)[0]
        up = float(probs[1])
        return {"up": up, "down": 1 - up}
