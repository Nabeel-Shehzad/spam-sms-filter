"""
Training pipeline for SMS spam classifiers.

Models trained:
  1. Naive Bayes  (MultinomialNB  — fast baseline, works with BoW counts)
  2. SVM          (LinearSVC      — strong classical model with TF-IDF)
  3. LSTM         (PyTorch        — deep learning, best accuracy)

After training, each model is evaluated on a held-out test set.
The best-performing model (by F1 score) is saved as best_model.
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

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

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
    df["label_enc"] = le.fit_transform(df["label"])  # ham->0, spam->1

    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"Processed data saved -> {PROCESSED_PATH}")

    # Show a few adversarial normalization examples
    spam_samples = df[df["label"] == "spam"].head(3)
    print("\nSample spam (original -> cleaned):")
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
# 4. Deep Learning — LSTM (PyTorch)
# ---------------------------------------------------------------------------

class _LSTMClassifier:
    """Simple wrapper so the LSTM fits the same interface as sklearn models."""
    def __init__(self, model, tokenizer, max_len, device):
        self.model = model
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.device = device

    def predict(self, texts):
        seqs = self.tokenizer.texts_to_sequences(texts)
        seqs = _pad_sequences(seqs, self.max_len)
        tensor = torch.tensor(seqs, dtype=torch.long).to(self.device)
        self.model.eval()
        with torch.no_grad():
            probs = self.model(tensor).squeeze(1).cpu().numpy()
        return (probs >= 0.5).astype(int)

    def predict_proba(self, texts):
        seqs = self.tokenizer.texts_to_sequences(texts)
        seqs = _pad_sequences(seqs, self.max_len)
        tensor = torch.tensor(seqs, dtype=torch.long).to(self.device)
        self.model.eval()
        with torch.no_grad():
            probs = self.model(tensor).squeeze(1).cpu().numpy()
        return probs


def _pad_sequences(seqs, max_len):
    """Pad / truncate list of token-id lists to fixed length."""
    out = np.zeros((len(seqs), max_len), dtype=np.int64)
    for i, s in enumerate(seqs):
        s = s[:max_len]
        out[i, :len(s)] = s
    return out


class _SimpleTokenizer:
    """Minimal word tokenizer — maps words to integer IDs."""
    def __init__(self, num_words=10_000):
        self.num_words = num_words
        self.word_index = {}
        self.oov_token = 1   # 0 = padding, 1 = OOV

    def fit_on_texts(self, texts):
        from collections import Counter
        counts = Counter()
        for t in texts:
            counts.update(t.lower().split())
        # Keep top (num_words - 2) words; 0=pad, 1=oov
        most_common = [w for w, _ in counts.most_common(self.num_words - 2)]
        self.word_index = {w: i + 2 for i, w in enumerate(most_common)}

    def texts_to_sequences(self, texts):
        return [
            [self.word_index.get(w, self.oov_token) for w in t.lower().split()]
            for t in texts
        ]


if TORCH_AVAILABLE:
    class BiLSTM(nn.Module):
        """Bidirectional LSTM spam classifier. Defined at module level for pickling."""
        def __init__(self, vocab_size, embed_dim, hidden_dim, num_layers):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
            self.lstm = nn.LSTM(
                embed_dim, hidden_dim,
                num_layers=num_layers,
                batch_first=True,
                bidirectional=True,
                dropout=0.3 if num_layers > 1 else 0.0,
            )
            self.dropout = nn.Dropout(0.3)
            self.fc = nn.Linear(hidden_dim * 2, 1)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x):
            emb = self.dropout(self.embedding(x))
            out, _ = self.lstm(emb)
            pooled = out.max(dim=1).values
            return self.sigmoid(self.fc(self.dropout(pooled)))


def _build_pytorch_lstm(vocab_size, embed_dim, hidden_dim, num_layers):
    return BiLSTM(vocab_size, embed_dim, hidden_dim, num_layers)


def train_lstm(df_train: pd.DataFrame, df_test: pd.DataFrame) -> dict:
    """Train a Bidirectional LSTM using PyTorch."""
    print("\n--- LSTM (PyTorch Bidirectional) ---")

    if not TORCH_AVAILABLE:
        print("PyTorch not installed - skipping LSTM training.")
        return {"name": "LSTM", "f1": 0.0, "accuracy": 0.0}

    from torch.utils.data import DataLoader, TensorDataset

    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {DEVICE}")

    MAX_WORDS = 10_000
    MAX_LEN = 150
    EMBED_DIM = 64
    HIDDEN_DIM = 64
    NUM_LAYERS = 2
    EPOCHS = 15
    BATCH_SIZE = 32
    PATIENCE = 3

    # Build vocabulary from raw (un-stemmed) text for better embeddings
    tokenizer = _SimpleTokenizer(num_words=MAX_WORDS)
    tokenizer.fit_on_texts(df_train["message"].tolist())
    joblib.dump(tokenizer, os.path.join(MODELS_DIR, "lstm_tokenizer.joblib"))

    X_train = torch.tensor(
        _pad_sequences(tokenizer.texts_to_sequences(df_train["message"].tolist()), MAX_LEN),
        dtype=torch.long
    )
    X_test = torch.tensor(
        _pad_sequences(tokenizer.texts_to_sequences(df_test["message"].tolist()), MAX_LEN),
        dtype=torch.long
    )
    y_train_t = torch.tensor(df_train["label_enc"].values, dtype=torch.float32)
    y_test_np = df_test["label_enc"].values

    train_ds = TensorDataset(X_train, y_train_t)
    train_dl = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)

    # Validation split (last 10% of training)
    val_size = max(1, int(0.1 * len(train_ds)))
    train_size = len(train_ds) - val_size
    train_sub, val_sub = torch.utils.data.random_split(
        train_ds, [train_size, val_size],
        generator=torch.Generator().manual_seed(RANDOM_STATE)
    )
    train_dl = DataLoader(train_sub, batch_size=BATCH_SIZE, shuffle=True)
    val_dl = DataLoader(val_sub, batch_size=BATCH_SIZE)

    model = _build_pytorch_lstm(MAX_WORDS, EMBED_DIM, HIDDEN_DIM, NUM_LAYERS).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.BCELoss()

    best_val_loss = float("inf")
    epochs_no_improve = 0
    best_state = None

    for epoch in range(EPOCHS):
        # Train
        model.train()
        train_loss = 0.0
        for xb, yb in train_dl:
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            preds = model(xb).squeeze(1)
            loss = criterion(preds, yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item() * len(xb)
        train_loss /= train_size

        # Validate
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for xb, yb in val_dl:
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                preds = model(xb).squeeze(1)
                val_loss += criterion(preds, yb).item() * len(xb)
        val_loss /= val_size

        print(f"Epoch {epoch+1:02d}/{EPOCHS} — train_loss: {train_loss:.4f}  val_loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= PATIENCE:
                print(f"Early stopping at epoch {epoch+1}")
                break

    # Restore best weights
    if best_state:
        model.load_state_dict(best_state)

    # Evaluate on test set
    model.eval()
    with torch.no_grad():
        probs = model(X_test.to(DEVICE)).squeeze(1).cpu().numpy()
    y_pred = (probs >= 0.5).astype(int)
    metrics = _evaluate(y_test_np, y_pred, model_name="LSTM")

    # Save model
    lstm_path = os.path.join(MODELS_DIR, "lstm_model.pt")
    torch.save(model.state_dict(), lstm_path)
    print(f"LSTM model saved -> {lstm_path}")

    # Save wrapper for predictor.py
    wrapper = _LSTMClassifier(model, tokenizer, MAX_LEN, DEVICE)
    joblib.dump(wrapper, os.path.join(MODELS_DIR, "lstm_wrapper.joblib"))

    return {"model": wrapper, "name": "LSTM", **metrics}


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
    print(f"\nTraining summary saved -> {summary_path}")
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
