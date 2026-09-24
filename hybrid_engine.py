from __future__ import annotations

from typing import Any

from ml_model import predict_ml
from risk_engine import analyse as analyse_rules


def _level(score: int) -> str:
    return "High" if score >= 70 else "Medium" if score >= 35 else "Low"


def analyse_hybrid(text: str, claimed_company_domain: str = "") -> dict[str, Any]:
    """Fuse rule-based evidence with the ML score without suppressing either signal.

    The screening score uses probabilistic OR fusion:
        1 - (1 - rule_risk) * (1 - ml_risk)

    This means an independently strong rule signal or strong ML signal can both produce
    a high screening score. The score is a screening indicator, not a calibrated fraud
    probability. If the model is unavailable, the function falls back to rules only.
    """
    rules = analyse_rules(text, claimed_company_domain)
    ml = predict_ml(text)

    if not ml["available"]:
        return {
            **rules,
            "hybrid_score": rules["score"],
            "hybrid_level": rules["level"],
            "rule_score": rules["score"],
            "ml": ml,
            "fusion": "rules-only fallback",
        }

    rule_risk = rules["score"] / 100.0
    ml_risk = float(ml["probability"])
    fused = 1.0 - ((1.0 - rule_risk) * (1.0 - ml_risk))
    hybrid = int(round(max(0.0, min(1.0, fused)) * 100))

    return {
        **rules,
        "hybrid_score": hybrid,
        "hybrid_level": _level(hybrid),
        "rule_score": rules["score"],
        "ml": ml,
        "fusion": "probabilistic OR of rule risk and ML score",
    }
