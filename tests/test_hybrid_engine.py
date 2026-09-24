from hybrid_engine import analyse_hybrid


def test_hybrid_falls_back_or_scores_high_for_obvious_scam():
    msg = "Dear candidate, no interview required. Contact us on WhatsApp and deposit $150 in USDT."
    result = analyse_hybrid(msg)
    assert result["hybrid_level"] in {"Medium", "High"}
    assert result["hybrid_score"] >= 35
