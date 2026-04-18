"""
Inference module — loads the best trained model and classifies new SMS messages.

Designed to be imported by the FastAPI layer.
Supports all three model types: Naive Bayes, SVM, LSTM.
"""

import os
import sys
import joblib
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.nlp.preprocessor import preprocess_auto
from backend.nlp.feature_extractor import load_tfidf_vectorizer, load_bow_vectorizer

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# Lazy-loaded singletons — loaded once on first classify() call
_tfidf = None
_bow = None
_svm = None
_nb = None
_lstm_wrapper = None   # _LSTMClassifier instance (PyTorch)
_meta = None


def _load_all():
    global _tfidf, _bow, _svm, _nb, _lstm_wrapper, _meta

    _meta = joblib.load(os.path.join(MODELS_DIR, "training_meta.joblib"))

    _tfidf = load_tfidf_vectorizer()
    _bow = load_bow_vectorizer()

    svm_path = os.path.join(MODELS_DIR, "svm.joblib")
    if os.path.exists(svm_path):
        _svm = joblib.load(svm_path)

    nb_path = os.path.join(MODELS_DIR, "naive_bayes.joblib")
    if os.path.exists(nb_path):
        _nb = joblib.load(nb_path)

    # PyTorch LSTM wrapper (saved by train.py)
    wrapper_path = os.path.join(MODELS_DIR, "lstm_wrapper.joblib")
    if os.path.exists(wrapper_path):
        _lstm_wrapper = joblib.load(wrapper_path)


def _ensure_loaded():
    if _meta is None:
        _load_all()


def classify(text: str) -> dict:
    """
    Classify a single SMS message as spam or ham.

    Returns:
        {
            "label": "spam" | "ham",
            "confidence": float (0-1),
            "model_used": str,
        }
    """
    _ensure_loaded()

    cleaned = preprocess_auto(text)
    best_name = _meta["best_model_name"]

    if best_name == "SVM" and _svm is not None:
        vec = _tfidf.transform([cleaned])
        pred = _svm.predict(vec)[0]
        # LinearSVC has decision_function, not predict_proba
        score = _svm.decision_function(vec)[0]
        confidence = float(1 / (1 + np.exp(-score)))  # sigmoid
        label = "spam" if pred == 1 else "ham"

    elif best_name == "Naive Bayes" and _nb is not None:
        vec = _bow.transform([cleaned])
        pred = _nb.predict(vec)[0]
        proba = _nb.predict_proba(vec)[0]
        confidence = float(proba[1])  # probability of spam class
        label = "spam" if pred == 1 else "ham"

    elif best_name == "LSTM" and _lstm_wrapper is not None:
        confidence = float(_lstm_wrapper.predict_proba([text])[0])
        pred = 1 if confidence >= 0.5 else 0
        label = "spam" if pred == 1 else "ham"

    else:
        # Fallback to SVM if best model unavailable
        vec = _tfidf.transform([cleaned])
        pred = _svm.predict(vec)[0]
        score = _svm.decision_function(vec)[0]
        confidence = float(1 / (1 + np.exp(-score)))
        label = "spam" if pred == 1 else "ham"

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "model_used": best_name,
    }


def classify_batch(texts: list[str]) -> list[dict]:
    """Classify multiple SMS messages at once."""
    return [classify(t) for t in texts]
