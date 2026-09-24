from ml_model import MODEL_PATH, predict_ml


def test_bundled_portable_model_loads_and_scores_text():
    scam = predict_ml(
        "Remote data entry. No interview. Pay a verification fee in USDT and contact us on WhatsApp.",
        model_path=MODEL_PATH,
    )
    legit = predict_ml(
        "Apply through our official careers page. Shortlisted candidates will complete interviews and reference checks.",
        model_path=MODEL_PATH,
    )

    assert scam["available"] is True
    assert legit["available"] is True
    assert 0.0 <= scam["probability"] <= 1.0
    assert 0.0 <= legit["probability"] <= 1.0
    assert scam["probability"] > legit["probability"]
