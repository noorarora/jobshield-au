from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np

MODEL_PATH = Path(__file__).parent / "models" / "portable_tfidf_logreg.joblib"
METRICS_PATH = Path(__file__).parent / "models" / "metrics.json"
TOKEN_RE = re.compile(r"(?u)\b\w\w+\b")


def model_available(model_path: Path | str = MODEL_PATH) -> bool:
    return Path(model_path).exists()


def load_bundle(model_path: Path | str = MODEL_PATH) -> dict[str, Any]:
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)


def load_metrics(metrics_path: Path | str = METRICS_PATH) -> dict[str, Any]:
    path = Path(metrics_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _strip_accents_unicode(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _portable_features(bundle: dict[str, Any], text: str) -> dict[int, float]:
    """Reproduce the fitted TF-IDF transform without unpickling sklearn estimators.

    The bundled production model uses lowercase word 1-2 grams, unicode accent stripping,
    English stop-word removal, sublinear TF, fitted IDF weights, and L2 normalisation.
    Keeping inference in plain Python/NumPy avoids scikit-learn pickle-version issues.
    """
    vocabulary: dict[str, int] = bundle["vocabulary"]
    stop_words = set(bundle.get("stop_words", []))
    idf = np.asarray(bundle["idf"], dtype=float)

    cleaned = _strip_accents_unicode(text.lower())
    tokens = [tok for tok in TOKEN_RE.findall(cleaned) if tok not in stop_words]
    terms = list(tokens)
    terms.extend(f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1))

    counts = Counter(term for term in terms if term in vocabulary)
    if not counts:
        return {}

    values: dict[int, float] = {}
    norm_sq = 0.0
    for term, count in counts.items():
        idx = vocabulary[term]
        tf = 1.0 + math.log(float(count))  # sublinear_tf=True
        value = tf * float(idf[idx])
        values[idx] = value
        norm_sq += value * value

    if norm_sq <= 0:
        return {}
    norm = math.sqrt(norm_sq)
    return {idx: value / norm for idx, value in values.items()}


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1.0 / (1.0 + z)
    z = math.exp(value)
    return z / (1.0 + z)


def _portable_predict(bundle: dict[str, Any], text: str, top_k: int) -> tuple[float, list[dict[str, float | str]]]:
    features = _portable_features(bundle, text)
    coef = np.asarray(bundle["coef"], dtype=float)
    intercept = float(bundle["intercept"])

    logit = intercept + sum(value * float(coef[idx]) for idx, value in features.items())
    probability = _sigmoid(logit)

    inverse_vocab = bundle.get("feature_names")
    if inverse_vocab is None:
        inverse_vocab = [None] * len(coef)
        for term, idx in bundle["vocabulary"].items():
            inverse_vocab[idx] = term

    ranked = sorted(
        ((idx, value * float(coef[idx])) for idx, value in features.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    top_terms: list[dict[str, float | str]] = []
    for idx, contribution in ranked:
        if contribution <= 0:
            continue
        top_terms.append(
            {
                "term": str(inverse_vocab[idx]),
                "contribution": round(float(contribution), 4),
            }
        )
        if len(top_terms) >= top_k:
            break
    return probability, top_terms


def _legacy_predict(bundle: dict[str, Any], text: str, top_k: int) -> tuple[float, list[dict[str, float | str]]]:
    """Backward-compatible path for older project bundles.

    Probability is computed directly from learned coefficients instead of calling
    LogisticRegression.predict_proba, which changed across sklearn releases.
    """
    pipeline = bundle["pipeline"]
    vectorizer = pipeline.named_steps.get("tfidf")
    classifier = pipeline.named_steps.get("clf")
    x = vectorizer.transform([text])

    coef = np.asarray(classifier.coef_[0], dtype=float)
    intercept = float(classifier.intercept_[0])
    logit = float(x.dot(coef)[0] + intercept)
    probability = _sigmoid(logit)

    if x.nnz == 0:
        return probability, []
    row = x.tocoo()
    feature_names = vectorizer.get_feature_names_out()
    ranked = sorted(
        zip(row.col, row.data * coef[row.col]),
        key=lambda item: item[1],
        reverse=True,
    )
    top_terms: list[dict[str, float | str]] = []
    for idx, contribution in ranked:
        if contribution <= 0:
            continue
        top_terms.append({"term": str(feature_names[idx]), "contribution": round(float(contribution), 4)})
        if len(top_terms) >= top_k:
            break
    return probability, top_terms


def predict_ml(text: str, model_path: Path | str = MODEL_PATH, top_k: int = 6) -> dict[str, Any]:
    if not model_available(model_path):
        return {
            "available": False,
            "probability": None,
            "label": None,
            "threshold": None,
            "top_terms": [],
            "model_name": None,
            "training_source": None,
            "error": None,
        }

    try:
        bundle = load_bundle(model_path)
        threshold = float(bundle.get("decision_threshold", 0.5))
        if "vocabulary" in bundle and "coef" in bundle:
            probability, top_terms = _portable_predict(bundle, text, top_k)
        elif "pipeline" in bundle:
            probability, top_terms = _legacy_predict(bundle, text, top_k)
        else:
            raise ValueError("Unsupported model bundle format")

        return {
            "available": True,
            "probability": probability,
            "label": "fraudulent" if probability >= threshold else "legitimate",
            "threshold": threshold,
            "top_terms": top_terms,
            "model_name": bundle.get("model_name", "TF-IDF + Logistic Regression"),
            "training_source": bundle.get("training_source", "unknown"),
            "error": None,
        }
    except Exception as exc:
        # Never let a model/runtime compatibility issue crash the user-facing app.
        return {
            "available": False,
            "probability": None,
            "label": None,
            "threshold": None,
            "top_terms": [],
            "model_name": None,
            "training_source": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
