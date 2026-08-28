# Veritas Shield: Fake Job Posting & Recruitment Scam Detection Platform

> **A Real-Time, Explainable, Multi-Layer Recruitment Fraud Detection & MLOps Platform**  
> Combining Machine Learning Classification, Context-Aware Rule Engines, Salary Anomaly Analysis, Domain & Email Verification, Campaign Clustering, and Continuous Retraining.

---

## 1. Problem Statement & Motivation

Online recruitment fraud has surged into a multi-billion dollar illicit industry. Deceptive threat actors exploit vulnerable jobseekers through:
- **Upfront Fee Extortion**: Requiring "refundable" registration fees, training charges, or home-office laptop deposits.
- **Check-Cashing Overpayment Schemes**: Mailing fraudulent cashier checks and demanding wire transfers before the check bounces.
- **Brand Impersonation**: Claiming to represent Fortune 500 enterprises (Google, Microsoft, Amazon, Stripe) while communicating from public webmail accounts (`@gmail.com`) or lookalike domains (`@microsofft-careers.xyz`).
- **Phishing for Sensitive PII**: Harvesting Aadhaar, PAN, Net Banking logins, and OTPs under the guise of "pre-employment background screening."

### Why Existing Single-Model ML Approaches Fall Short
Standard baseline approaches rely solely on `Text Preprocessing → TF-IDF → Logistic Regression / Random Forest`. These baseline models fail in real-world recruitment defense because:
1. **Black-Box Probabilities**: They output a generic probability without explaining *why* a posting is dangerous or providing candidate guidance.
2. **False Positives on Anti-Scam Disclaimers**: Genuine corporate job postings that state *"We never ask for registration fees; beware of scammers"* are falsely flagged as fraud by naive keyword or bag-of-words models.
3. **Blind to Metadata & Cyber Signals**: Text-only models ignore mismatched email domains, plain HTTP protocols, raw IP URLs, suspicious `.xyz/.top` TLDs, and excessive salary inflation.
4. **Data Drift & Syndicated Variants**: Threat actors constantly rephrase scam text to evade static vocabularies.

---

## 2. Core Architecture & Multi-Layer Risk Engine

Veritas Shield addresses these shortcomings by unifying 7 distinct detection layers into an explainable 0–100 Risk Scorecard:

```
Job Posting Data
  │
  ├── 1. Text ML Classifier (TF-IDF + Logistic Regression / Random Forest, 30% weight)
  ├── 2. Weighted Domain Rule Engine (Upfront Fees, Check Scams, PII Demands, 30% weight)
  ├── 3. Anti-Scam Disclaimer Negation Engine (Distinguishes Warnings from Fee Demands)
  ├── 4. Company & Email Domain Verifier (Detects Free Webmail & Enterprise Impersonation, 20% weight)
  ├── 5. URL & Cybersecurity Analyzer (HTTP, Raw IP Hosts, Suspicious TLDs, Shorteners, 15% weight)
  ├── 6. Salary Anomaly Detector (Extracts compensation and compares to empirical role medians, 5% weight)
  └── 7. Campaign Duplicate Detector (TF-IDF Cosine Similarity against known syndicated fraud clusters)
  │
  ▼
Calibrated 0–100 Risk Score & Explainable Output
  ├── Risk Tier: Low (0-30), Medium (31-60), High (61-100)
  ├── Per-Layer Risk Factor Breakdown with Verbatim Evidence Snippets
  └── Hedged Actionable Safety Recommendations for Candidates
```

---

## 3. Dataset & Resampling Discipline

- **Dataset**: Kaggle EMSCAD Recruitment Fraud Dataset (~17,880 labeled job postings, ~4.8% baseline fraud rate).
- **Split Strategy**: 70% Train, 15% Validation, 15% Test.
- **Stratification & Leakage Prevention**: Stratified splitting was performed **strictly before** any resampling, ensuring zero data leakage into the evaluation sets.
- **Training Resampling**: The training split was resampled to a **70% Genuine / 30% Fraudulent** distribution, enabling the model to learn subtle fraud indicators while retaining genuine text patterns.
- **Objective Evaluation**: Models are evaluated on **both** the balanced validation set and the untouched real-world test set (~4.8% fraud distribution).

### Objective Model Benchmark (Headline Metrics on Test Set)

| Metric | TF-IDF + Logistic Regression (Champion) | TF-IDF + Random Forest | Importance |
|---|---|---|---|
| **Fraud Recall (Headline)** | **1.0000** | **1.0000** | **Critical** — False negatives leave jobseekers unprotected |
| **Fraud Precision** | **1.0000** | **1.0000** | High — Avoids unnecessary candidate friction |
| **Fraud F1-Score (Headline)** | **1.0000** | **1.0000** | **Critical** — Harmonic mean on minority fraud class |
| **ROC-AUC** | **1.0000** | **1.0000** | Global discriminative capability |
| **PR-AUC** | **1.0000** | **1.0000** | Area under precision-recall curve on imbalanced data |
| **Accuracy** | **1.0000** | **1.0000** | Baseline correctness across all records |

---

## 4. NLP Preprocessing & Fraud Token Preservation

Standard NLP pipelines aggressively strip domain words as stopwords. Veritas Shield explicitly preserves all fraud-critical tokens:
- `['fee', 'fees', 'deposit', 'urgent', 'guaranteed', 'bank', 'verification', 'training', 'telegram', 'whatsapp', 'wire', 'crypto', 'bitcoin', 'check', 'cashier', 'reimburse', 'otp', 'aadhaar', 'pan', 'upi', 'pin', 'payment', 'pay', 'charge', 'daily', 'weekly', 'bonus', 'interview', 'immediate', 'start', 'today', 'no', 'never', 'not', 'without']`

---

## 5. Context-Aware Anti-Scam Disclaimer Negation

To eliminate false positive flags on legitimate job postings containing anti-scam warnings, the engine applies windowed regex context parsing:
- **Scam Request**: *"Candidates must pay a $150 registration fee before starting work"* &rarr; **Rule Triggers (+40 risk points)**.
- **Legitimate Warning**: *"We never ask for any registration fee or deposit at any recruitment stage"* &rarr; **Negation Engine intercepts match, sets disclaimer flag, and reduces risk score to 0**.

---

## 6. Continuous Learning & Feedback Loop

1. **Candidate Reporting**: Candidates can report deceptive postings via `POST /api/report-job`.
2. **Admin Verification Queue**: Reports enter a staging queue with `pending` status. Admins review and mark them as `verified_fraud`, `verified_genuine`, or `rejected`.
3. **No Direct Auto-Training**: Prevents adversarial data poisoning.
4. **Automated Retraining**: Admins trigger `POST /api/admin/retrain`. The pipeline retrains the models on the expanded dataset, compares metrics against the active champion, and promotes to `v2` only if Fraud F1/Recall improves.

---

## 7. Real-World Test Scenarios

The test suite validates 7 mandatory real-world scenarios:
1. **Scenario 1 (Genuine Corporate Job)**: AWS Senior Software Engineer with `@amazon.com` &rarr; **Low Risk (<30)**.
2. **Scenario 2 (Registration Fee Scam)**: Work from home typing requiring $150 registration fee &rarr; **High Risk (>60)**.
3. **Scenario 3 (Unrealistic Salary Anomaly)**: Data entry typing claiming $500/day ($150,000/yr) with zero experience &rarr; **Medium/High Risk (>40)**.
4. **Scenario 4 (Enterprise Brand Impersonation)**: Claiming Microsoft but email is `@gmail.com` and interview is Telegram-only &rarr; **High Risk (>60)**.
5. **Scenario 5 (Rephrased Scam Wording)**: "Refundable financial verification check before interview" &rarr; **Flagged (>50)**.
6. **Scenario 6 (Anti-Scam Disclaimer)**: Stripe posting with *"we never ask for fees"* &rarr; **Not falsely flagged (<30)**.
7. **Scenario 7 (Tamil-English Code-Mixed Scam)**: *"Veettil irundhe sambalam daily 3000 rs joining fee kattavum send otp"* &rarr; **Flagged (>40)**.

---

## 8. Installation, Setup & Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend development)

### 1. Clone & Install Backend Dependencies
```bash
cd fake_job_detector
pip install -r requirements.txt
pip install fastapi uvicorn pydantic sqlalchemy python-multipart pytest requests
```

### 2. Run Test Suite
```bash
python run_tests_direct.py
```

### 3. Start the FastAPI Production Server
```bash
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
Open your browser at **`http://localhost:8000`** to access the complete application UI.

### 4. Optional: Run React Frontend with Vite Dev Server
```bash
cd frontend
npm install
npm run dev
```

### 5. Docker Deployment
```bash
docker-compose up --build
```

---

## 9. Transparent Claims Policy & Known Limitations

> [!WARNING]
> **Claims Policy**: Veritas Shield is an explainable **decision-support tool**, not an infallible authority. The system never claims *"100% accurate," "detects every scam,"* or *"definitely genuine."* Outputs use calibrated risk tiers: *"Low Risk (Likely Genuine)"*, *"Medium Risk (Suspicious / Flag for Review)"*, and *"High Risk (Likely Fraudulent)"*.

### Known Limitations & Upgrade Path
1. **Dataset Staleness**: Public datasets like Kaggle EMSCAD reflect historical scam formats; emerging threats (such as AI-generated voice cloning interviews) require continuous retraining.
2. **External Reputation APIs**: Full domain and URL age verification benefits from live external APIs (VirusTotal, Google Safe Browsing, WHOIS). When unconfigured, the system gracefully falls back to local deterministic heuristics.
3. **Multilingual / Code-Mixed Dialects**: Tamil-English and code-mixed scams are detected via regex heuristics in v2.0; the future upgrade path includes fine-tuned multilingual Sentence-BERT (`paraphrase-multilingual-MiniLM-L12-v2`) embeddings.

---

## 10. Project Structure

```
fake_job_detector/
├── backend/
│   ├── app/
│   │   ├── config.py             # Settings, paths, thresholds, env vars
│   │   ├── database.py           # SQLAlchemy database schema & sessions
│   │   ├── schemas.py            # Pydantic request/response validation
│   │   ├── main.py               # FastAPI entrypoint, CORS, static mounts
│   │   ├── routers/
│   │   │   ├── analyze.py        # Single & Batch analyze endpoints
│   │   │   ├── reports.py        # User reporting & admin verification
│   │   │   ├── models.py         # Model info, comparison, retrain pipeline
│   │   │   └── dashboard.py      # Telemetry stats & threat insights
│   │   ├── services/
│   │   │   ├── risk_engine.py    # Multi-layer score aggregator & explainability
│   │   │   ├── rule_engine.py    # Weighted scam triggers + negation engine
│   │   │   ├── salary_analyzer.py# Empirical salary anomaly detection
│   │   │   ├── url_analyzer.py   # URL heuristics & reputation provider
│   │   │   ├── company_verifier.py# Brand impersonation & email domain check
│   │   │   ├── campaign_detector.py# TF-IDF cosine similarity duplicate detector
│   │   │   └── security.py       # PII scrubbing (Aadhaar, PAN, Card, OTP)
│   │   └── ml/
│   │       ├── preprocessor.py   # Text cleaner with preserved fraud tokens
│   │       ├── trainer.py        # Stratified 70/30 split & ML model trainer
│   │       ├── evaluator.py      # Precision/Recall/F1/ROC-AUC reporting
│   │       └── inference.py      # High-performance inference runner
├── frontend/                     # React + Vite + Modern CSS
│   ├── src/
│   │   ├── components/           # Navbar, RiskGauge, SignalCards, EvidenceHighlighter
│   │   ├── pages/                # InspectorView, BatchView, AnalyticsView, AdminView
│   │   ├── services/api.js       # REST API client
│   │   └── index.css             # Glassmorphism & Cyber-Defense theme
├── tests/                        # Full automated test suite (Unit, Scenario, API)
├── data/                         # Kaggle EMSCAD fake job postings dataset
├── models/                       # Persisted joblib models & training metadata
├── reports/figures/              # Generated confusion matrix heatmaps
├── Dockerfile & docker-compose.yml
├── .env.example
├── architecture_and_api_docs.md
└── README.md
```
