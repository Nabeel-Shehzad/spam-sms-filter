"""
Training pipeline for SMS spam classifiers.

Models trained:
  1. Naive Bayes  (MultinomialNB  — fast baseline, works with BoW counts)
  2. SVM          (LinearSVC      — strong classical model with TF-IDF)
  3. LSTM         (Keras          — deep learning, best accuracy)

After training, each model is evaluated on a held-out test set.
The best-performing model (by F1 score) is saved as `best_model.joblib`.
"""

import os
import sys
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    accuracy_score,
)
from sklearn.preprocessing import LabelEncoder

# Resolve project root so imports work from any working directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.nlp.preprocessor import preprocess_batch
from backend.nlp.feature_extractor import fit_and_save_vectorizers, transform

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "SMSSpamCollection.tsv")
PROCESSED_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "sms_processed.csv")

RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# 1. Data Loading
# ---------------------------------------------------------------------------

def load_data(path: str) -> pd.DataFrame:
    """Load the UCI SMS Spam Collection TSV file."""
    df = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=["label", "message"],
        encoding="latin-1",
    )
    df.dropna(subset=["label", "message"], inplace=True)
    df.drop_duplicates(subset=["message"], inplace=True)
    print(f"Dataset loaded: {len(df)} rows")
    print(df["label"].value_counts().to_string())
    return df


# ---------------------------------------------------------------------------
# 2. Preprocessing
# ---------------------------------------------------------------------------

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply full NLP preprocessing pipeline and save processed CSV."""
    print("\nPreprocessing messages...")
    df = df.copy()
    df["cleaned"] = preprocess_batch(df["message"].tolist())

    # Encode labels: ham=0, spam=1
    le = LabelEncoder()
    df["label_enc"] = le.fit_transform(df["label"])  # ham→0, spam→1

    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Processed data saved → {PROCESSED_PATH}")

    # Show a few adversarial normalization examples
    spam_samples = df[df["label"] == "spam"].head(3)
    print("\nSample spam (original → cleaned):")
    for _, row in spam_samples.iterrows():
        print(f"  ORIG: {row['message'][:80]}")
        print(f"  CLEAN: {row['cleaned'][:80]}\n")

    return df


# ---------------------------------------------------------------------------
# 3. Classical Models — Naive Bayes & SVM
# ---------------------------------------------------------------------------

def train_naive_bayes(X_train_bow, y_train, X_test_bow, y_test) -> dict:
    print("\n--- Naive Bayes (BoW) ---")
    model = MultinomialNB(alpha=0.1)
    model.fit(X_train_bow, y_train)
    y_pred = model.predict(X_test_bow)
    metrics = _evaluate(y_test, y_pred, model_name="Naive Bayes")
    joblib.dump(model, os.path.join(MODELS_DIR, "naive_bayes.joblib"))
    return {"model": model, "name": "Naive Bayes", **metrics}


def train_svm(X_train_tfidf, y_train, X_test_tfidf, y_test) -> dict:
    print("\n--- SVM (TF-IDF) ---")
    model = LinearSVC(C=1.0, max_iter=2000, random_state=RANDOM_STATE)
    model.fit(X_train_tfidf, y_train)
    y_pred = model.predict(X_test_tfidf)
    metrics = _evaluate(y_test, y_pred, model_name="SVM")
    joblib.dump(model, os.path.join(MODELS_DIR, "svm.joblib"))
    return {"model": model, "name": "SVM", **metrics}


# ---------------------------------------------------------------------------
# 4. Deep Learning — LSTM
# ---------------------------------------------------------------------------

def train_lstm(df_train: pd.DataFrame, df_test: pd.DataFrame) -> dict:
    """
    Train a bidirectional LSTM on tokenized sequences.
    Uses Keras Tokenizer (separate from sklearn vectorizers).
    """
    print("\n--- LSTM (Deep Learning) ---")

    try:
        import tensorflow as tf
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import (
            Embedding, Bidirectional, LSTM, Dense, Dropout, GlobalMaxPooling1D
        )
        from tensorflow.keras.preprocessing.text import Tokenizer
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        from tensorflow.keras.callbacks import EarlyStopping
    except ImportError:
        print("TensorFlow not installed — skipping LSTM training.")
        return {"name": "LSTM", "f1": 0.0, "accuracy": 0.0}

    MAX_WORDS = 10_000
    MAX_LEN = 150
    EMBED_DIM = 64

    # Tokenize at word level (no stemming for LSTM — preserves semantics)
    tokenizer = tf.keras.preprocessing.text.Tokenizer(
        num_words=MAX_WORDS, oov_token="<OOV>"
    )
    tokenizer.fit_on_texts(df_train["message"].tolist())
    joblib.dump(tokenizer, os.path.join(MODELS_DIR, "lstm_tokenizer.joblib"))

    X_train = pad_sequences(
        tokenizer.texts_to_sequences(df_train["message"].tolist()),
        maxlen=MAX_LEN, padding="post", truncating="post"
    )
    X_test = pad_sequences(
        tokenizer.texts_to_sequences(df_test["message"].tolist()),
        maxlen=MAX_LEN, padding="post", truncating="post"
    )
    y_train = df_train["label_enc"].values
    y_test = df_test["label_enc"].values

    model = Sequential([
        Embedding(MAX_WORDS, EMBED_DIM, input_length=MAX_LEN),
        Bidirectional(LSTM(64, return_sequences=True)),
        GlobalMaxPooling1D(),
        Dropout(0.3),
        Dense(32, activation="relu"),
        Dropout(0.2),
        Dense(1, activation="sigmoid"),
    ])
    model.compile(
        loss="binary_crossentropy",
        optimizer="adam",
        metrics=["accuracy"],
    )
    model.summary()

    early_stop = EarlyStopping(
        monitor="val_loss", patience=3, restore_best_weights=True
    )
    model.fit(
        X_train, y_train,
        epochs=15,
        batch_size=32,
        validation_split=0.1,
        callbacks=[early_stop],
        verbose=1,
    )

    y_pred_prob = model.predict(X_test).flatten()
    y_pred = (y_pred_prob >= 0.5).astype(int)
    metrics = _evaluate(y_test, y_pred, model_name="LSTM")

    lstm_path = os.path.join(MODELS_DIR, "lstm_model.keras")
    model.save(lstm_path)
    print(f"LSTM model saved → {lstm_path}")

    return {"model": model, "name": "LSTM", **metrics}


# ---------------------------------------------------------------------------
# 5. Evaluation Helper
# ---------------------------------------------------------------------------

def _evaluate(y_true, y_pred, model_name: str) -> dict:
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1)

    print(f"Accuracy : {acc:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(classification_report(y_true, y_pred, target_names=["Ham", "Spam"]))
    cm = confusion_matrix(y_true, y_pred)
    print(f"Confusion Matrix:\n{cm}")

    return {"accuracy": acc, "f1": f1}


# ---------------------------------------------------------------------------
# 6. Main Pipeline
# ---------------------------------------------------------------------------

def run_training():
    os.makedirs(MODELS_DIR, exist_ok=True)

    # Load & preprocess
    df = load_data(DATA_PATH)
    df = preprocess_data(df)

    # Train/test split (stratified to preserve spam ratio)
    df_train, df_test = train_test_split(
        df, test_size=0.2, random_state=RANDOM_STATE, stratify=df["label_enc"]
    )
    print(f"\nTrain: {len(df_train)} | Test: {len(df_test)}")

    # Fit vectorizers on training cleaned texts
    tfidf, bow = fit_and_save_vectorizers(df_train["cleaned"].tolist())

    X_train_tfidf = transform(tfidf, df_train["cleaned"].tolist())
    X_test_tfidf = transform(tfidf, df_test["cleaned"].tolist())
    X_train_bow = transform(bow, df_train["cleaned"].tolist())
    X_test_bow = transform(bow, df_test["cleaned"].tolist())

    y_train = df_train["label_enc"].values
    y_test = df_test["label_enc"].values

    # Train classical models
    results = []
    results.append(train_naive_bayes(X_train_bow, y_train, X_test_bow, y_test))
    results.append(train_svm(X_train_tfidf, y_train, X_test_tfidf, y_test))
    results.append(train_lstm(df_train, df_test))

    # ---------------------------------------------------------------------------
    # 7. Select & save best model
    # ---------------------------------------------------------------------------
    best = max(results, key=lambda r: r["f1"])
    print(f"\n=== Best Model: {best['name']} (F1={best['f1']:.4f}) ===")

    # Save a summary of all results
    summary = pd.DataFrame([
        {"model": r["name"], "accuracy": r["accuracy"], "f1": r["f1"]}
        for r in results
    ])
    summary_path = os.path.join(MODELS_DIR, "training_summary.csv")
    summary.to_csv(summary_path, index=False)
    print(f"\nTraining summary saved → {summary_path}")
    print(summary.to_string(index=False))

    # Save metadata about which model + vectorizer to use for inference
    meta = {
        "best_model_name": best["name"],
        "best_model_f1": best["f1"],
        "best_model_accuracy": best["accuracy"],
    }
    joblib.dump(meta, os.path.join(MODELS_DIR, "training_meta.joblib"))
    print("\nTraining complete.")


if __name__ == "__main__":
    run_training()
