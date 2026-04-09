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

from backend.nlp.preprocessor import preprocess
from backend.nlp.feature_extractor import load_tfidf_vectorizer, load_bow_vectorizer

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# Lazy-loaded singletons — loaded once on first classify() call
_tfidf = None
_bow = None
_svm = None
_nb = None
_lstm = None
_lstm_tokenizer = None
_meta = None


def _load_all():
    global _tfidf, _bow, _svm, _nb, _lstm, _lstm_tokenizer, _meta

    _meta = joblib.load(os.path.join(MODELS_DIR, "training_meta.joblib"))

    _tfidf = load_tfidf_vectorizer()
    _bow = load_bow_vectorizer()

    svm_path = os.path.join(MODELS_DIR, "svm.joblib")
    if os.path.exists(svm_path):
        _svm = joblib.load(svm_path)

    nb_path = os.path.join(MODELS_DIR, "naive_bayes.joblib")
    if os.path.exists(nb_path):
        _nb = joblib.load(nb_path)

    lstm_path = os.path.join(MODELS_DIR, "lstm_model.keras")
    tok_path = os.path.join(MODELS_DIR, "lstm_tokenizer.joblib")
    if os.path.exists(lstm_path) and os.path.exists(tok_path):
        try:
            import tensorflow as tf
            _lstm = tf.keras.models.load_model(lstm_path)
            _lstm_tokenizer = joblib.load(tok_path)
        except ImportError:
            pass


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

    cleaned = preprocess(text)
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

    elif best_name == "LSTM" and _lstm is not None:
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        seq = _lstm_tokenizer.texts_to_sequences([text])  # raw text for LSTM
        padded = pad_sequences(seq, maxlen=150, padding="post", truncating="post")
        confidence = float(_lstm.predict(padded, verbose=0)[0][0])
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
