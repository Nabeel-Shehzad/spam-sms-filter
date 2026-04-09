# Spam SMS Filtering System

An intelligent, real-time SMS spam detection system powered by Machine Learning and Natural Language Processing. The system classifies SMS messages as **spam** or **ham (legitimate)** with high accuracy, supports multilingual detection, and adapts to evolving spam patterns through continuous learning.

---

## Features

- **Hybrid ML Classification** — Naive Bayes, SVM, and Bidirectional LSTM ensemble
- **Adversarial Text Normalization** — detects obfuscated spam like `Fr.ee M0ney!!!`
- **Real-time Detection** — classifies messages in under 500ms
- **Multilingual Support** — mBERT for non-English SMS spam
- **User Dashboard** — spam statistics, false positive reporting, model retraining
- **Adaptive Learning** — model updates from user feedback to combat concept drift
- **Secure by Design** — JWT auth, RBAC, end-to-end encryption, GDPR compliant

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Client Layer                                               │
│  React.js (Web)          Flutter (Mobile)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│  API Gateway  (Nginx + Rate Limiting + TLS)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │  Auth Service           │
          │  JWT + OAuth2           │
          └────────────┬────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  Core Service Layer                                         │
│  ┌──────────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │  Spam Filter API  │  │  ML Engine  │  │ NLP Pipeline  │  │
│  │  (FastAPI)        │  │  TF/Sklearn │  │ SpaCy / NLTK  │  │
│  └──────────────────┘  └─────────────┘  └───────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│  Data Layer                                                 │
│  PostgreSQL       Redis Cache        AWS S3 (Logs/Backups)  │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend (Web)** | React.js |
| **Frontend (Mobile)** | Flutter |
| **Backend API** | FastAPI (Python) |
| **ML Models** | Naive Bayes, SVM, Bidirectional LSTM |
| **NLP** | NLTK, SpaCy, TF-IDF, mBERT (multilingual) |
| **Database** | PostgreSQL + Redis |
| **Storage** | AWS S3 |
| **Auth** | JWT + OAuth2 |
| **Deployment** | Docker + Kubernetes (AWS EKS) |
| **CI/CD** | GitHub Actions |
| **Monitoring** | Prometheus + Grafana |

---

## Project Structure

```
spam-filter/
├── backend/
│   ├── api/              # FastAPI routes & endpoints
│   ├── ml/               # Model training & inference
│   │   ├── train.py      # Training pipeline (NB, SVM, LSTM)
│   │   └── predictor.py  # Inference module
│   ├── nlp/              # Text preprocessing
│   │   ├── preprocessor.py     # Clean, tokenize, stem
│   │   └── feature_extractor.py # TF-IDF + BoW vectorizers
│   ├── auth/             # JWT authentication
│   ├── db/               # SQLAlchemy models & migrations
│   └── tests/            # Unit & integration tests
├── frontend/
│   ├── web/              # React.js dashboard
│   └── mobile/           # Flutter mobile app
├── data/
│   ├── download_dataset.py  # UCI dataset downloader
│   ├── raw/              # Raw dataset (gitignored)
│   └── processed/        # Preprocessed data (gitignored)
├── models/               # Trained models (gitignored)
├── infra/
│   ├── docker/           # Dockerfiles
│   ├── k8s/              # Kubernetes manifests
│   └── nginx/            # Nginx config
├── notebooks/            # EDA & experiment notebooks
├── run_training.py       # One-command training entry point
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variable template
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git

### 1. Clone the repository

```bash
git clone https://github.com/Nabeel-Shehzad/spam-sms-filter.git
cd spam-sms-filter
```

### 2. Create and activate virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your database URL, secret key, etc.
```

### 5. Download dataset & train models

```bash
python run_training.py
```

This will:
- Download the UCI SMS Spam Collection dataset
- Preprocess all messages
- Train Naive Bayes, SVM, and LSTM models
- Save the best model to `models/`

### 6. Run the API server

```bash
uvicorn backend.api.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

---

## ML Pipeline

### Preprocessing Steps

1. Unicode normalization
2. Lowercase
3. URL & phone number removal
4. **Adversarial character normalization** (`M0ney` -> `money`, `fr.ee` -> `free`)
5. Special character removal
6. Tokenization
7. Stop word removal
8. Porter stemming

### Models & Performance

| Model | Vectorizer | Accuracy | F1 Score |
|---|---|---|---|
| Naive Bayes | Bag of Words | 97.68% | 0.9084 |
| **SVM** | **TF-IDF (1,2)-gram** | **98.07%** | **0.9213** |
| Bidirectional LSTM | Word Embeddings | 97.10% | 0.8819 |

### Running Tests

```bash
pytest backend/tests/ -v
```

---

## Dataset

**UCI SMS Spam Collection**
- 5,574 SMS messages (4,827 ham + 747 spam)
- Source: UCI Machine Learning Repository
- Automatically downloaded by `data/download_dataset.py`

---

## Security

- Passwords hashed with **bcrypt**
- All communication over **HTTPS (TLS)**
- **JWT tokens** with expiry for session management
- **RBAC** — user / admin / telecom_provider roles
- **Parameterized SQL queries** — SQL injection prevention
- **GDPR compliant** — user consent, data deletion endpoint
- Compliant with **ISO/IEC 27001** and **ISO/IEC 25010**

---

## Roadmap

- [x] Phase 1 — Data & ML Core (preprocessing, training pipeline)
- [ ] Phase 2 — FastAPI Backend (REST API, auth, database)
- [ ] Phase 3 — Frontend (React.js dashboard, Flutter mobile)
- [ ] Phase 4 — Real-time Pipeline (Kafka streaming)
- [ ] Phase 5 — Security Hardening
- [ ] Phase 6 — Testing (unit, integration, load, penetration)
- [ ] Phase 7 — Deployment (Docker, Kubernetes, AWS)

---

## License

MIT License
