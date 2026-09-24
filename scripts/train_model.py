from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

TEXT_COLUMNS = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits",
    "employment_type",
    "required_experience",
    "required_education",
    "industry",
    "function",
]


def load_dataset(path: Path) -> tuple[pd.DataFrame, str]:
    df = pd.read_csv(path)

    if {"text", "fraudulent"}.issubset(df.columns):
        out = pd.DataFrame(
            {
                "text": df["text"].fillna("").astype(str),
                "fraudulent": df["fraudulent"].astype(int),
            }
        )
        source = str(df.get("source", pd.Series(["custom"])).iloc[0])
        return out, source

    if "fraudulent" not in df.columns:
        raise ValueError("Dataset must contain a 'fraudulent' target column.")

    available = [col for col in TEXT_COLUMNS if col in df.columns]
    if not available:
        raise ValueError(
            "No supported text columns found. Add a 'text' column or EMSCAD/Kaggle text fields."
        )

    text = df[available].fillna("").astype(str).agg(" \n ".join, axis=1)
    out = pd.DataFrame({"text": text, "fraudulent": df["fraudulent"].astype(int)})
    return out, "EMSCAD/Kaggle-compatible"


def _metrics(y_true: pd.Series, probabilities: np.ndarray, threshold: float) -> dict:
    predictions = (probabilities >= threshold).astype(int)
    return {
        "threshold": round(float(threshold), 4),
        "precision_fraud": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall_fraud": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1_fraud": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
        "f2_fraud": round(float(fbeta_score(y_true, predictions, beta=2, zero_division=0)), 4),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "pr_auc": round(float(average_precision_score(y_true, probabilities)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
        "confusion_matrix": confusion_matrix(y_true, predictions).tolist(),
        "classification_report": classification_report(
            y_true, predictions, output_dict=True, zero_division=0
        ),
    }


def _select_threshold(y_true: pd.Series, probabilities: np.ndarray) -> tuple[float, dict]:
    """Choose the threshold on validation data only, maximising fraud-class F1.

    The test set remains untouched until the threshold is locked.
    """
    best_threshold = 0.5
    best = None
    for threshold in np.linspace(0.10, 0.90, 161):
        current = _metrics(y_true, probabilities, float(threshold))
        key = (current["f1_fraud"], current["precision_fraud"], current["recall_fraud"])
        if best is None or key > best[0]:
            best = (key, current)
            best_threshold = float(threshold)
    return best_threshold, best[1]


def train(
    dataset_path: Path,
    model_path: Path,
    metrics_path: Path,
    test_size: float = 0.15,
    validation_size: float = 0.15,
    seed: int = 42,
):
    raw, source = load_dataset(dataset_path)
    raw_counts = raw["fraudulent"].value_counts().to_dict()
    if set(raw_counts) != {0, 1}:
        raise ValueError("Target must contain both 0 (legitimate) and 1 (fraudulent).")

    # Exact duplicate postings with identical labels can leak near-identical examples
    # across random train/test splits. Remove exact combined-text duplicates before split.
    conflicts = raw.groupby("text")["fraudulent"].nunique()
    conflicting_groups = int((conflicts > 1).sum())
    if conflicting_groups:
        raise ValueError(
            f"Found {conflicting_groups} exact-text groups with conflicting labels; resolve them before training."
        )

    dedup = raw.drop_duplicates(subset=["text"], keep="first").reset_index(drop=True)
    counts = dedup["fraudulent"].value_counts().to_dict()

    if test_size <= 0 or validation_size <= 0 or test_size + validation_size >= 1:
        raise ValueError("validation_size and test_size must be > 0 and sum to less than 1.")

    x_train, x_temp, y_train, y_temp = train_test_split(
        dedup["text"],
        dedup["fraudulent"],
        test_size=test_size + validation_size,
        random_state=seed,
        stratify=dedup["fraudulent"],
    )
    relative_test_size = test_size / (test_size + validation_size)
    x_val, x_test, y_val, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=relative_test_size,
        random_state=seed,
        stratify=y_temp,
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    max_df=0.98,
                    max_features=30000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=1200,
                    class_weight="balanced",
                    random_state=seed,
                ),
            ),
        ]
    )

    pipeline.fit(x_train, y_train)
    val_probabilities = pipeline.predict_proba(x_val)[:, 1]
    test_probabilities = pipeline.predict_proba(x_test)[:, 1]

    threshold, validation_metrics = _select_threshold(y_val, val_probabilities)
    test_metrics = _metrics(y_test, test_probabilities, threshold)
    default_test_metrics = _metrics(y_test, test_probabilities, 0.5)

    trained_at = datetime.now(timezone.utc).isoformat()
    metrics = {
        "model": "TF-IDF (1-2 grams) + Logistic Regression",
        "training_source": source,
        "raw_rows": int(len(raw)),
        "rows": int(len(raw)),
        "unique_rows_after_exact_dedup": int(len(dedup)),
        "exact_duplicate_rows_removed": int(len(raw) - len(dedup)),
        "raw_class_distribution": {
            "legitimate": int(raw_counts.get(0, 0)),
            "fraudulent": int(raw_counts.get(1, 0)),
        },
        "unique_class_distribution": {
            "legitimate": int(counts.get(0, 0)),
            "fraudulent": int(counts.get(1, 0)),
        },
        "split": {
            "train_rows": int(len(x_train)),
            "validation_rows": int(len(x_val)),
            "test_rows": int(len(x_test)),
            "train_fraud": int(y_train.sum()),
            "validation_fraud": int(y_val.sum()),
            "test_fraud": int(y_test.sum()),
            "random_seed": seed,
        },
        "threshold_selection": {
            "objective": "Maximise fraud-class F1 on validation split",
            "selected_threshold": round(float(threshold), 4),
            "validation": validation_metrics,
        },
        "test": test_metrics,
        "test_at_default_0_5": default_test_metrics,
        # Convenience fields used by the Streamlit UI.
        "selected_threshold": round(float(threshold), 4),
        "precision_fraud": test_metrics["precision_fraud"],
        "recall_fraud": test_metrics["recall_fraud"],
        "f1_fraud": test_metrics["f1_fraud"],
        "f2_fraud": test_metrics["f2_fraud"],
        "accuracy": test_metrics["accuracy"],
        "pr_auc": test_metrics["pr_auc"],
        "roc_auc": test_metrics["roc_auc"],
        "confusion_matrix": test_metrics["confusion_matrix"],
        "trained_at_utc": trained_at,
        "warning": (
            "Synthetic/demo metrics are smoke-test metrics only and must not be presented as real-world performance."
            if source == "synthetic_demo"
            else "Held-out metrics are specific to this historical dataset and split; they do not guarantee performance on current real-world scams."
        ),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["clf"]
    feature_names = vectorizer.get_feature_names_out().tolist()
    bundle = {
        "format": "jobshield-portable-tfidf-logreg-v1",
        "vocabulary": dict(vectorizer.vocabulary_),
        "feature_names": feature_names,
        "idf": vectorizer.idf_.astype(float),
        "coef": classifier.coef_[0].astype(float),
        "intercept": float(classifier.intercept_[0]),
        "stop_words": sorted(vectorizer.get_stop_words() or []),
        "model_name": metrics["model"],
        "training_source": source,
        "trained_at_utc": trained_at,
        "decision_threshold": round(float(threshold), 4),
        "deduplicated_training": True,
        "inference_note": "Portable inference avoids sklearn pickle-version coupling.",
    }
    joblib.dump(bundle, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(json.dumps(metrics, indent=2))
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train JobShield AU baseline text classifier.")
    parser.add_argument("--data", default="data/fake_job_postings.csv")
    parser.add_argument("--model", default="models/portable_tfidf_logreg.joblib")
    parser.add_argument("--metrics", default="models/metrics.json")
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--validation-size", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    train(
        dataset_path=Path(args.data),
        model_path=Path(args.model),
        metrics_path=Path(args.metrics),
        test_size=args.test_size,
        validation_size=args.validation_size,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
