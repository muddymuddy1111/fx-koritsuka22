"""Entry scoring and alert helpers."""

from __future__ import annotations


def calc_entry_score(
    trend_match: bool,
    pullback_match: bool,
    strength_match: bool,
    ai_prob_up: float,
) -> int:
    score = 0
    score += 30 if trend_match else 0
    score += 25 if pullback_match else 0
    score += 25 if strength_match else 0
    score += 20 if ai_prob_up >= 0.60 else 0
    return score


def score_to_stars(score: int) -> str:
    stars = max(1, min(5, round(score / 20)))
    return "★" * stars + "☆" * (5 - stars)


def score_label(score: int) -> str:
    if score >= 80:
        return "優位"
    if score >= 60:
        return "やや優位"
    if score >= 40:
        return "様子見"
    return "見送り"
