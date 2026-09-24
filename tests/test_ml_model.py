from pathlib import Path

from scripts.generate_demo_data import build_rows
from scripts.train_model import train
from ml_model import predict_ml


def test_training_and_prediction(tmp_path: Path):
    data_path = tmp_path / "demo.csv"
    model_path = tmp_path / "model.joblib"
    metrics_path = tmp_path / "metrics.json"

    rows = build_rows(120, seed=7)
    import pandas as pd
    pd.DataFrame(rows).to_csv(data_path, index=False)

    metrics = train(data_path, model_path, metrics_path, test_size=0.25, seed=7)
    assert metrics["rows"] == 120
    assert model_path.exists()
    assert metrics_path.exists()

    result = predict_ml(
        "Dear candidate, no interview. Contact us on WhatsApp and pay a registration fee in USDT.",
        model_path=model_path,
    )
    assert result["available"] is True
    assert 0.0 <= result["probability"] <= 1.0
    assert result["probability"] > 0.5
