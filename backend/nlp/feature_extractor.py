"""
Feature extraction for SMS spam detection.

Provides two vectorizers:
  - TF-IDF  (default, best for SVM and classical ML)
  - Bag of Words / CountVectorizer (for Naive Bayes)

Both are fitted on training data and can transform new messages at inference time.
Fitted vectorizers are saved to disk so the API can load them without retraining.
"""

import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

MODELS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "models"
)
TFIDF_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib")
BOW_PATH = os.path.join(MODELS_DIR, "bow_vectorizer.joblib")


def build_tfidf_vectorizer(
    max_features: int = 10_000,
    ngram_range: tuple = (1, 2),
    sublinear_tf: bool = True,
) -> TfidfVectorizer:
    """
    Create a TF-IDF vectorizer.

    Args:
        max_features: Vocabulary size cap.
        ngram_range:  (1,2) captures unigrams + bigrams.
        sublinear_tf: Apply log normalization to term frequencies.
    """
    return TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        sublinear_tf=sublinear_tf,
        strip_accents="unicode",
        analyzer="word",
        min_df=2,          # ignore terms that appear in fewer than 2 docs
    )


def build_bow_vectorizer(
    max_features: int = 10_000,
    ngram_range: tuple = (1, 1),
) -> CountVectorizer:
    """
    Create a Bag-of-Words (CountVectorizer).

    Args:
        max_features: Vocabulary size cap.
        ngram_range:  (1,1) unigrams only (standard BoW).
    """
    return CountVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        strip_accents="unicode",
        analyzer="word",
        min_df=2,
    )


def fit_and_save_vectorizers(train_texts: list[str]) -> tuple:
    """
    Fit both TF-IDF and BoW vectorizers on training texts.
    Saves fitted vectorizers to the models/ directory.

    Returns:
        (tfidf_vectorizer, bow_vectorizer)
    """
    os.makedirs(MODELS_DIR, exist_ok=True)

    tfidf = build_tfidf_vectorizer()
    tfidf.fit(train_texts)
    joblib.dump(tfidf, TFIDF_PATH)
    print(f"TF-IDF vectorizer saved → {TFIDF_PATH}")

    bow = build_bow_vectorizer()
    bow.fit(train_texts)
    joblib.dump(bow, BOW_PATH)
    print(f"BoW vectorizer saved    → {BOW_PATH}")

    return tfidf, bow


def load_tfidf_vectorizer() -> TfidfVectorizer:
    """Load a previously fitted TF-IDF vectorizer from disk."""
    if not os.path.exists(TFIDF_PATH):
        raise FileNotFoundError(
            f"TF-IDF vectorizer not found at {TFIDF_PATH}. "
            "Run the training pipeline first."
        )
    return joblib.load(TFIDF_PATH)


def load_bow_vectorizer() -> CountVectorizer:
    """Load a previously fitted BoW vectorizer from disk."""
    if not os.path.exists(BOW_PATH):
        raise FileNotFoundError(
            f"BoW vectorizer not found at {BOW_PATH}. "
            "Run the training pipeline first."
        )
    return joblib.load(BOW_PATH)


def transform(vectorizer, texts: list[str]):
    """Transform a list of preprocessed texts using a fitted vectorizer."""
    return vectorizer.transform(texts)
