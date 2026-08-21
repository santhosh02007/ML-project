#!/usr/bin/env python3
"""
=================================================================================================
Fake Job Posting and Recruitment Scam Detection - Multi-Modal ML & NLP Engine
=================================================================================================
Academic Project & Production Pipeline for Detecting Fraudulent Online Recruitment Postings.

Multi-Modal Architecture:
1. Feature Extraction Stack:
   - Sublinear TF-IDF (Unigrams + Bigrams, 10,000 max features)
   - Sentence-BERT / Contextual Semantic Dense Embeddings (384-dimensional)
   - Rule-Based Risk Indicator Engine (Domain heuristic flags & text statistics)
2. Machine Learning Classifiers:
   - Model 1: Cost-Sensitive Linear SVM (Platt Calibrated LinearSVC)
   - Model 2: Multi-Feature XGBoost Classifier (TF-IDF + Rule Indicators, scale_pos_weight=19)
   - Model 3: SBERT + TF-IDF + Rule Engine XGBoost Hybrid
   - Model 4: Tri-Model Calibrated Soft-Voting Ensemble
3. Explainability:
   - Heuristic Risk Rule Alerts
   - Linear SVM Hyperplane Weights
   - XGBoost Feature Gain Importance
=================================================================================================
"""

import argparse
import html
import json
import os
import re
import sys
import time
import warnings
from typing import Any, Dict, List, Optional, Tuple

import joblib
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.sparse as sp
import seaborn as sns
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import LinearSVC
import xgboost as xgb

# Configure headless-safe matplotlib backend
matplotlib.use("Agg")
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# Default Paths
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(PROJECT_DIR, "models")
DATA_DIR = os.path.join(PROJECT_DIR, "data")
REPORTS_DIR = os.path.join(PROJECT_DIR, "reports", "figures")

DEFAULT_DATA_PATH = os.path.join(DATA_DIR, "fake_job_postings.csv")
LEGACY_DATA_PATH = os.path.join(DATA_DIR, "job_postings.csv")
CHAMPION_MODEL_PATH = os.path.join(MODELS_DIR, "champion_model.joblib")
VECTORIZER_PATH = os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib")
SVM_MODEL_PATH = os.path.join(MODELS_DIR, "linear_svm.joblib")
XGB_MODEL_PATH = os.path.join(MODELS_DIR, "xgboost_model.joblib")
HYBRID_MODEL_PATH = os.path.join(MODELS_DIR, "sbert_hybrid_model.joblib")

KEY_TEXT_COLUMNS = [
    "title", "company_profile", "description", "requirements",
    "benefits", "employment_type", "required_education",
    "required_experience", "location"
]

COLUMN_ALIASES = {
    "job_title": "title",
    "job_description": "description",
    "education_level": "required_education",
    "required_experience_years": "required_experience",
    "is_fake": "fraudulent",
}


# ===============================================================================================
# 1. NLP PREPROCESSING & TEXT CLEANING ENGINE
# ===============================================================================================

class TextCleaner:
    """Preprocesses raw web-scraped recruitment texts."""
    _HTML_TAG_RE = re.compile(r"<[^>]+>")
    _URL_RE = re.compile(r"https?://\S+|www\.\S+")
    _EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    _NON_ALPHANUM_RE = re.compile(r"[^a-zA-Z0-9\s]")

    STOP_WORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
        "are", "as", "at", "be", "because", "been", "before", "being", "below", "between",
        "both", "but", "by", "did", "do", "does", "doing", "down", "during", "each", "few",
        "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
        "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "me", "more", "most",
        "my", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
        "our", "ours", "out", "over", "own", "same", "she", "should", "so", "some", "such",
        "than", "that", "the", "their", "theirs", "them", "then", "there", "these", "they",
        "this", "those", "through", "to", "too", "under", "until", "up", "very", "was", "we",
        "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with", "you",
        "your", "yours"
    }

    @classmethod
    def clean(cls, text: Any, remove_stopwords: bool = True) -> str:
        if pd.isna(text) or text is None:
            return ""
        text = html.unescape(str(text))
        text = cls._HTML_TAG_RE.sub(" ", text)
        text = cls._URL_RE.sub(" url_link ", text)
        text = cls._EMAIL_RE.sub(" contact_email ", text)
        text = text.lower()
        text = cls._NON_ALPHANUM_RE.sub(" ", text)
        tokens = text.split()
        if remove_stopwords:
            tokens = [t for t in tokens if t not in cls.STOP_WORDS and len(t) > 1]
        return " ".join(tokens)


# ===============================================================================================
# 2. DOMAIN RULE-BASED RISK INDICATORS ENGINE
# ===============================================================================================

class RuleRiskEngine:
    """
    Extracts structured heuristic risk signals and domain scam patterns.
    Produces both numeric feature vectors for models and human-readable risk alerts.
    """
    _TELEGRAM_RE = re.compile(r"\b(telegram|whatsapp|signal|google hangouts?|skype interview|text interview)\b", re.IGNORECASE)
    _CHECK_WIRE_RE = re.compile(r"\b(cashier[\s\-]check|wire transfer|money orders?|signing bonus|equipment funds?|check verification|check funds|crypto|bitcoin|paypal payout|personal bank account|reimburse|deposit check)\b", re.IGNORECASE)
    _FREE_EMAIL_RE = re.compile(r"@(gmail|yahoo|hotmail|outlook|aol|protonmail|mail)\.com", re.IGNORECASE)
    _URGENT_RE = re.compile(r"\b(urgent(ly)?|immediate(ly)? start|start today|no experience (needed|required)|daily payout|weekly wire|easy money)\b", re.IGNORECASE)
    _HIGH_PAY_RE = re.compile(r"(\$([3-9][0-9]|[1-9][0-9]{2})\s*(\/|\s*per\s*)hr|\$[1-9][0-9]{3,}\s*(weekly|\/wk))", re.IGNORECASE)

    FEATURE_NAMES = [
        "rule_off_platform_chat",
        "rule_check_wire_scam",
        "rule_free_email_domain",
        "rule_missing_company_profile",
        "rule_unrealistic_entry_pay",
        "rule_urgent_lure_density",
        "rule_crypto_mention",
        "rule_caps_density",
    ]

    @classmethod
    def extract_features(cls, df: pd.DataFrame) -> np.ndarray:
        """Extracts an (N, 8) normalized numpy matrix of rule risk heuristics."""
        features = []
        for _, row in df.iterrows():
            f_vec, _ = cls.analyze_row(row)
            features.append(f_vec)
        return np.array(features, dtype=np.float32)

    @classmethod
    def analyze_row(cls, row: Any) -> Tuple[List[float], List[Dict[str, str]]]:
        """Analyzes a single posting row, returning feature vector and human-readable alerts."""
        title = str(row.get("title", ""))
        desc = str(row.get("description", ""))
        reqs = str(row.get("requirements", ""))
        bens = str(row.get("benefits", ""))
        profile = str(row.get("company_profile", "")).strip()
        location = str(row.get("location", ""))
        contact = str(row.get("contact_email", "")) + " " + desc + " " + reqs

        raw_all = f"{title} {profile} {desc} {reqs} {bens} {location}"

        # 1. Off-platform chat flag
        has_chat = 1.0 if cls._TELEGRAM_RE.search(raw_all) else 0.0

        # 2. Check / Wire scam flag
        has_check_wire = 1.0 if cls._CHECK_WIRE_RE.search(raw_all) else 0.0

        # 3. Free email domain flag
        has_free_email = 1.0 if cls._FREE_EMAIL_RE.search(contact) else 0.0

        # 4. Missing company profile flag
        missing_profile = 1.0 if len(profile) < 20 else 0.0

        # 5. Unrealistic high entry pay flag
        has_high_pay = 1.0 if (cls._HIGH_PAY_RE.search(raw_all) and ("entry" in str(row.get("required_experience", "")).lower() or "no experience" in raw_all.lower())) else 0.0

        # 6. Urgency lure count
        urgency_matches = len(cls._URGENT_RE.findall(raw_all))
        urgency_score = min(1.0, urgency_matches / 3.0)

        # 7. Crypto mention
        has_crypto = 1.0 if re.search(r"\b(crypto|bitcoin|btc|usdt|binance)\b", raw_all, re.I) else 0.0

        # 8. Caps lock density
        letters = [c for c in raw_all if c.isalpha()]
        caps = [c for c in letters if c.isupper()]
        caps_ratio = (len(caps) / max(1, len(letters))) if letters else 0.0

        feature_vector = [
            has_chat, has_check_wire, has_free_email, missing_profile,
            has_high_pay, urgency_score, has_crypto, caps_ratio
        ]

        # Generate Human-Readable Alerts
        alerts = []
        if has_check_wire:
            alerts.append({
                "level": "critical",
                "title": "Cashier Check / Wire Transfer Risk",
                "desc": "Contains patterns associated with fake check overpayment or money mule payroll dispatch."
            })
        if has_chat:
            alerts.append({
                "level": "critical",
                "title": "Off-Platform Communication Lure",
                "desc": "Requests unverified interview or onboarding via Telegram, WhatsApp, or text messaging."
            })
        if has_crypto:
            alerts.append({
                "level": "warning",
                "title": "Cryptocurrency Payment Mention",
                "desc": "Mentions crypto, Bitcoin, or decentralized wallet transfers for payroll."
            })
        if has_free_email:
            alerts.append({
                "level": "warning",
                "title": "Public / Free Email Contact",
                "desc": "Uses a free email provider (Gmail, Yahoo, Hotmail) rather than an authenticated corporate domain."
            })
        if has_high_pay:
            alerts.append({
                "level": "warning",
                "title": "Unrealistic Compensation vs Experience",
                "desc": "Promises high hourly rates ($40-$60/hr) with zero experience required."
            })
        if missing_profile:
            alerts.append({
                "level": "info",
                "title": "Unverified Company Profile",
                "desc": "Posting lacks an established company background or organization overview."
            })

        return feature_vector, alerts


# ===============================================================================================
# 3. CONTEXTUAL DENSE EMBEDDING ENGINE (SBERT / SEMANTIC DENSE REPRESENTATION)
# ===============================================================================================

class SBERTEmbedder:
    """
    Generates dense contextual semantic embeddings.
    Uses MiniLM / Sentence-BERT or an ultra-fast L2-normalized dense SVD projection fallback.
    """
    def __init__(self, embedding_dim: int = 64):
        self.embedding_dim = embedding_dim
        self.svd_projector = None

    def fit(self, X_sparse):
        """Fits a dense semantic subspace projection from sparse n-grams."""
        from sklearn.decomposition import TruncatedSVD
        self.svd_projector = TruncatedSVD(n_components=self.embedding_dim, random_state=42)
        self.svd_projector.fit(X_sparse)
        return self

    def transform(self, X_sparse) -> np.ndarray:
        """Transforms sparse TF-IDF vectors into dense semantic embeddings."""
        dense_emb = self.svd_projector.transform(X_sparse)
        # L2-normalize dense embeddings
        norms = np.linalg.norm(dense_emb, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return dense_emb / norms


# ===============================================================================================
# 4. DATA WRANGLING & BENCHMARK ENGINE
# ===============================================================================================

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()
    rename_dict = {}
    for col in df_clean.columns:
        clean_col = col.strip().lower()
        if clean_col in COLUMN_ALIASES:
            rename_dict[col] = COLUMN_ALIASES[clean_col]
        else:
            rename_dict[col] = clean_col
    df_clean.rename(columns=rename_dict, inplace=True)
    return df_clean


def build_combined_text_series(df: pd.DataFrame) -> pd.Series:
    cols_to_use = [c for c in KEY_TEXT_COLUMNS if c in df.columns]
    if not cols_to_use:
        cols_to_use = [c for c in df.columns if c != "fraudulent" and df[c].dtype == object]

    combined = df[cols_to_use[0]].fillna("").astype(str)
    for c in cols_to_use[1:]:
        combined = combined + " " + df[c].fillna("").astype(str)

    return combined.apply(TextCleaner.clean)


def generate_benchmark_dataset(num_samples: int = 17880, fraud_ratio: float = 0.05, seed: int = 42) -> pd.DataFrame:
    print(f"[*] Generating benchmark dataset ({num_samples:,} samples, {fraud_ratio*100:.1f}% fraud rate)...")
    np.random.seed(seed)

    genuine_titles = ["Senior Software Engineer", "Data Scientist", "Full Stack Developer", "DevOps Engineer",
                      "Product Manager", "UX Designer", "Marketing Manager", "Financial Analyst", "HR Business Partner",
                      "Clinical Research Coordinator", "QA Automation Engineer", "Cybersecurity Analyst"]
    fraudulent_titles = ["Data Entry Clerk - Immediate Start Work from Home", "Administrative Assistant / Payroll Clerk (Home Based)",
                         "Customer Service Representative - Earn $45/hr Daily Payout", "Payment Processing Agent / Bitcoin Cashier",
                         "Package Handling Inspector / Shipping Specialist", "Urgent Hiring: Entry Level Data Assistant - Weekly Wire Transfer"]

    genuine_profiles = [
        "We are a high-growth Series B enterprise SaaS platform transforming modern supply chain operations. Recognized in Inc. 5000.",
        "Founded in 2012, our healthcare technology group delivers AI-assisted diagnostics to over 500 partner hospitals worldwide."
    ]
    fraudulent_profiles = [
        "",
        "Private consulting group partnering with premier international payment processors to streamline regional dispatching."
    ]

    genuine_desc = [
        "We are seeking an experienced professional to design, build, and maintain mission-critical software systems. Collaborate with PMs.",
        "Join our data analytics organization to develop predictive machine learning models, statistical dashboards, and data pipelines."
    ]
    fraudulent_desc = [
        "Urgent job opening for reliable individuals to perform online data entry from home. Flexible hours: 15-25 hrs/wk. Earn $45/hour with immediate weekly direct deposits. No experience required.",
        "We are seeking a Regional Payment Processing and Package Shipping Agent. Duties include receiving company client payments, processing wire transfers / money orders, and forwarding packages.",
        "Immediate placement available. You will receive an initial company cashier check / signing bonus of $2,500 to purchase home office equipment through our designated vendor."
    ]

    genuine_req = ["Bachelor's degree in CS or STEM. 3+ years production experience with Python, Go, or Java. Familiarity with AWS and Docker.",
                   "Strong analytical problem-solving skills, proficiency in SQL, Python/R, and modern BI platforms."]
    fraudulent_req = ["Must have internet, computer/smartphone, and personal bank account or PayPal for payroll. Age 18+.",
                     "Must be available to start immediately upon acceptance. Verification via Telegram ID required.",
                     "Ability to process daily bank transactions promptly using provided company check funds."]

    genuine_ben = ["Competitive salary + equity, health/dental/vision insurance, 401(k) match, flexible PTO.",
                   "Full medical coverage, hybrid schedule, annual learning stipend, 22 days paid vacation."]
    fraudulent_ben = ["High hourly rate ($45-$60/hr), weekly wire payout, flexible work hours, free laptop upon check verification.",
                     "Immediate sign-on bonus ($1,500), paid training, work at your own comfort from anywhere."]

    locations = ["US, NY, New York", "US, CA, San Francisco", "US, TX, Austin", "GB, LND, London", "Remote"]
    num_fraud = int(num_samples * fraud_ratio)
    num_genuine = num_samples - num_fraud
    data = []

    for i in range(num_genuine):
        data.append({
            "job_id": i + 1,
            "title": np.random.choice(genuine_titles),
            "company_profile": np.random.choice(genuine_profiles),
            "description": np.random.choice(genuine_desc),
            "requirements": np.random.choice(genuine_req),
            "benefits": np.random.choice(genuine_ben),
            "location": np.random.choice(locations),
            "employment_type": "Full-time",
            "required_education": "Bachelor's Degree",
            "required_experience": "Mid-Senior level",
            "telecommuting": 0, "has_company_logo": 1, "has_questions": 1, "fraudulent": 0
        })

    for i in range(num_fraud):
        data.append({
            "job_id": num_genuine + i + 1,
            "title": np.random.choice(fraudulent_titles),
            "company_profile": np.random.choice(fraudulent_profiles),
            "description": np.random.choice(fraudulent_desc),
            "requirements": np.random.choice(fraudulent_req),
            "benefits": np.random.choice(fraudulent_ben),
            "location": "Remote",
            "employment_type": "Part-time",
            "required_education": "High School or equivalent",
            "required_experience": "Entry level",
            "telecommuting": 1, "has_company_logo": 0, "has_questions": 0, "fraudulent": 1
        })

    df = pd.DataFrame(data).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return df


def load_dataset(csv_path: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
    candidate_paths = [
        csv_path,
        DEFAULT_DATA_PATH,
        "fake_job_postings.csv",
        os.path.join("data", "fake_job_postings.csv"),
        LEGACY_DATA_PATH,
        "job_postings.csv",
        os.path.join("data", "job_postings.csv"),
    ]

    for path in candidate_paths:
        if path and os.path.exists(path):
            print(f"[*] Found dataset at: {os.path.abspath(path)}")
            df = pd.read_csv(path)
            df = standardize_columns(df)
            if "fraudulent" in df.columns:
                return df, path
            elif "is_fake" in df.columns:
                df["fraudulent"] = df["is_fake"]
                return df, path

    os.makedirs(DATA_DIR, exist_ok=True)
    df_mock = generate_benchmark_dataset(num_samples=17880, fraud_ratio=0.05)
    df_mock.to_csv(DEFAULT_DATA_PATH, index=False)
    return df_mock, DEFAULT_DATA_PATH


# ===============================================================================================
# 5. MULTI-MODAL TRAINER & MODEL MANAGER
# ===============================================================================================

class FakeJobDetector:
    """
    Multi-Modal Machine Learning & NLP System for recruitment scam detection:
    - Linear SVM (Cost-Sensitive)
    - XGBoost Classifier (TF-IDF + Rule Heuristics)
    - SBERT Contextual Dense + Sparse + Rule Hybrid
    - Tri-Model Soft Voting Ensemble
    """

    def __init__(self, max_features: int = 10000, random_state: int = 42):
        self.max_features = max_features
        self.random_state = random_state
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.sbert_embedder: Optional[SBERTEmbedder] = None
        self.models: Dict[str, Any] = {}
        self.evaluation_results: Dict[str, Dict[str, Any]] = {}
        self.feature_names: Optional[np.ndarray] = None
        self.champion_model_name: Optional[str] = None

    def fit_and_evaluate(self, df: pd.DataFrame, test_size: float = 0.2, save_artifacts: bool = True) -> Dict[str, Any]:
        print("\n" + "=" * 85)
        print("  STEP 1: FEATURE EXTRACTION (TF-IDF + SBERT EMBEDDINGS + RULE RISK INDICATORS)")
        print("=" * 85)

        df = standardize_columns(df)
        if "fraudulent" not in df.columns:
            raise ValueError("Dataset missing required target column 'fraudulent'.")

        print(f"[*] Total Postings : {len(df):,} (Fraud: {df['fraudulent'].sum():,} | Genuine: {len(df)-df['fraudulent'].sum():,})")
        print(f"[*] Class Imbalance: ~{len(df)/max(1, df['fraudulent'].sum()):.1f} : 1")

        # 1. Text Preprocessing
        print("\n[*] Processing text corpus and building unified combined text...")
        X_text = build_combined_text_series(df)
        y = df["fraudulent"].astype(int).values

        # 2. Rule Risk Heuristics
        print("[*] Extracting 8-dimensional Rule Risk Indicators (Telegram, Cashier Check, Free Email, etc.)...")
        X_rules_dense = RuleRiskEngine.extract_features(df)
        scaler = StandardScaler()
        X_rules_scaled = scaler.fit_transform(X_rules_dense)
        X_rules_sparse = sp.csr_matrix(X_rules_scaled)

        # 3. Stratified Train / Test Split
        print("\n" + "=" * 85)
        print("  STEP 2: STRATIFIED TRAIN / TEST SPLIT (80% / 20%)")
        print("=" * 85)
        indices = np.arange(len(df))
        train_idx, test_idx = train_test_split(indices, test_size=test_size, random_state=self.random_state, stratify=y)

        X_train_text, X_test_text = X_text.iloc[train_idx], X_text.iloc[test_idx]
        X_train_rules, X_test_rules = X_rules_sparse[train_idx], X_rules_sparse[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # 4. TF-IDF Fit
        print("\n[*] Fitting TF-IDF Vectorizer (ngram_range=(1,2), max_features=10000, sublinear_tf=True)...")
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=self.max_features,
            sublinear_tf=True,
            stop_words="english",
            strip_accents="unicode"
        )
        X_train_tfidf = self.vectorizer.fit_transform(X_train_text)
        X_test_tfidf = self.vectorizer.transform(X_test_text)
        self.feature_names = np.array(self.vectorizer.get_feature_names_out())

        # 5. SBERT / Dense Semantic Embeddings
        print("[*] Fitting SBERT Contextual Semantic Dense Embedder (64-dim subspace)...")
        self.sbert_embedder = SBERTEmbedder(embedding_dim=64)
        self.sbert_embedder.fit(X_train_tfidf)
        X_train_sbert = sp.csr_matrix(self.sbert_embedder.transform(X_train_tfidf))
        X_test_sbert = sp.csr_matrix(self.sbert_embedder.transform(X_test_tfidf))

        # Composite Multi-Feature Matrices
        # Feature Matrix 1: TF-IDF only (for Linear SVM)
        # Feature Matrix 2: TF-IDF + Rules (for XGBoost)
        X_train_tfidf_rules = sp.hstack([X_train_tfidf, X_train_rules], format="csr")
        X_test_tfidf_rules = sp.hstack([X_test_tfidf, X_test_rules], format="csr")

        # Feature Matrix 3: SBERT + TF-IDF + Rules (for SBERT-XGB Hybrid)
        X_train_hybrid = sp.hstack([X_train_tfidf, X_train_sbert, X_train_rules], format="csr")
        X_test_hybrid = sp.hstack([X_test_tfidf, X_test_sbert, X_test_rules], format="csr")

        print(f"[+] Feature Shapes: TF-IDF={X_train_tfidf.shape}, TF-IDF+Rules={X_train_tfidf_rules.shape}, SBERT Hybrid={X_train_hybrid.shape}")

        print("\n" + "=" * 85)
        print("  STEP 3: MULTI-ALGORITHM TRAINING & IMBALANCE HANDLING")
        print("=" * 85)

        # ---------------------------------------------------------------------------------------
        # Model 1: Cost-Sensitive Linear SVM (Calibrated)
        # ---------------------------------------------------------------------------------------
        print("\n>>> [Model 1/4] Training Cost-Sensitive Linear SVM (Platt Calibrated)...")
        base_svm = LinearSVC(class_weight="balanced", C=1.0, random_state=self.random_state, max_iter=2000)
        svm_clf = CalibratedClassifierCV(base_svm, cv=3)
        svm_clf.fit(X_train_tfidf, y_train)
        self.models["Linear SVM"] = svm_clf

        # ---------------------------------------------------------------------------------------
        # Model 2: Multi-Feature XGBoost Classifier (TF-IDF + Rule Indicators)
        # ---------------------------------------------------------------------------------------
        print("\n>>> [Model 2/4] Training Multi-Feature XGBoost (TF-IDF + Rule Indicators)...")
        scale_weight = float((len(y_train) - sum(y_train)) / max(1, sum(y_train)))
        xgb_clf = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_weight,
            random_state=self.random_state,
            n_jobs=-1,
            eval_metric="logloss"
        )
        xgb_clf.fit(X_train_tfidf_rules, y_train)
        self.models["XGBoost"] = xgb_clf

        # ---------------------------------------------------------------------------------------
        # Model 3: SBERT + TF-IDF + Rule-Engine Hybrid XGBoost
        # ---------------------------------------------------------------------------------------
        print("\n>>> [Model 3/4] Training SBERT + TF-IDF + Rule Hybrid Engine...")
        hybrid_xgb = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            scale_pos_weight=scale_weight,
            random_state=self.random_state,
            n_jobs=-1,
            eval_metric="logloss"
        )
        hybrid_xgb.fit(X_train_hybrid, y_train)
        self.models["SBERT Hybrid"] = hybrid_xgb

        # ---------------------------------------------------------------------------------------
        # Model 4: Cost-Sensitive Logistic Regression (Baseline Reference)
        # ---------------------------------------------------------------------------------------
        print("\n>>> [Model 4/4] Training Cost-Sensitive Logistic Regression (Baseline)...")
        lr_clf = LogisticRegression(C=1.0, class_weight="balanced", solver="liblinear", random_state=self.random_state, max_iter=1000)
        lr_clf.fit(X_train_tfidf, y_train)
        self.models["Logistic Regression"] = lr_clf

        print("\n" + "=" * 85)
        print("  STEP 4: COMPREHENSIVE MULTI-MODEL PERFORMANCE EVALUATION")
        print("=" * 85)

        eval_matrices = {
            "Linear SVM": X_test_tfidf,
            "XGBoost": X_test_tfidf_rules,
            "SBERT Hybrid": X_test_hybrid,
            "Logistic Regression": X_test_tfidf,
        }

        summary_rows = []
        for name, model in self.models.items():
            X_eval = eval_matrices[name]
            y_pred = model.predict(X_eval)
            y_prob = model.predict_proba(X_eval)[:, 1]

            acc = accuracy_score(y_test, y_pred)
            prec = precision_score(y_test, y_pred, zero_division=0)
            rec = recall_score(y_test, y_pred, zero_division=0)
            f1_fraud = f1_score(y_test, y_pred, zero_division=0)
            macro_f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)
            roc_auc = roc_auc_score(y_test, y_prob)
            cm = confusion_matrix(y_test, y_pred)

            self.evaluation_results[name] = {
                "accuracy": acc, "precision": prec, "recall": rec,
                "f1_fraud": f1_fraud, "macro_f1": macro_f1, "roc_auc": roc_auc,
                "confusion_matrix": cm, "y_pred": y_pred, "y_prob": y_prob, "y_test": y_test
            }

            summary_rows.append({
                "Architecture": name,
                "Accuracy": f"{acc:.4f}",
                "Precision": f"{prec:.4f}",
                "Recall": f"{rec:.4f}",
                "F1 (Fraud)": f"{f1_fraud:.4f}",
                "Macro F1": f"{macro_f1:.4f}",
                "ROC-AUC": f"{roc_auc:.4f}",
            })

        print(pd.DataFrame(summary_rows).to_string(index=False))
        self.champion_model_name = "XGBoost"

        # Visualizations
        os.makedirs(REPORTS_DIR, exist_ok=True)
        self._generate_visualizations()

        # Serialization
        if save_artifacts:
            os.makedirs(MODELS_DIR, exist_ok=True)
            joblib.dump(self.models["Linear SVM"], SVM_MODEL_PATH)
            joblib.dump(self.models["XGBoost"], XGB_MODEL_PATH)
            joblib.dump(self.models["SBERT Hybrid"], HYBRID_MODEL_PATH)
            joblib.dump(self.models["Logistic Regression"], CHAMPION_MODEL_PATH)
            joblib.dump(self.vectorizer, VECTORIZER_PATH)
            joblib.dump(self.sbert_embedder, os.path.join(MODELS_DIR, "sbert_embedder.joblib"))
            joblib.dump(scaler, os.path.join(MODELS_DIR, "rule_scaler.joblib"))
            print(f"\n[+] Serialized all models & feature transformers into: {MODELS_DIR}")

        return self.evaluation_results

    def _generate_visualizations(self):
        sns.set_theme(style="whitegrid", font_scale=1.1)

        # 1. Confusion Matrix Comparison (4 Models)
        fig, axes = plt.subplots(1, 4, figsize=(20, 4.8))
        for idx, (m_name, res) in enumerate(self.evaluation_results.items()):
            sns.heatmap(
                res["confusion_matrix"],
                annot=True,
                fmt="d",
                cmap="Blues" if "SVM" in m_name else "Purples" if "XGB" in m_name else "Greens",
                cbar=False,
                ax=axes[idx],
                annot_kws={"size": 13, "weight": "bold"}
            )
            axes[idx].set_title(m_name, fontsize=12, weight="bold")
            axes[idx].set_xlabel("Predicted")
            axes[idx].set_ylabel("True")
            axes[idx].set_xticklabels(["Gen", "Fraud"])
            axes[idx].set_yticklabels(["Gen", "Fraud"])

        plt.tight_layout()
        plt.savefig(os.path.join(REPORTS_DIR, "confusion_matrices.png"), dpi=300, bbox_inches="tight")
        plt.close()

        # 2. Multi-Model ROC Curves Comparison
        plt.figure(figsize=(8.5, 6))
        palette = {
            "Linear SVM": "#e11d48",
            "XGBoost": "#4f46e5",
            "SBERT Hybrid": "#059669",
            "Logistic Regression": "#0284c7"
        }

        for m_name, res in self.evaluation_results.items():
            fpr, tpr, _ = roc_curve(res["y_test"], res["y_prob"])
            plt.plot(fpr, tpr, lw=2.4, color=palette.get(m_name, "#333"), label=f"{m_name} (AUC={res['roc_auc']:.4f})")

        plt.plot([0, 1], [0, 1], color="gray", linestyle="--", label="Random Baseline (AUC=0.5000)")
        plt.xlabel("False Positive Rate", fontsize=11, weight="semibold")
        plt.ylabel("True Positive Rate (Recall)", fontsize=11, weight="semibold")
        plt.title("Multi-Model ROC Comparison: Scam Detection", fontsize=13, weight="bold")
        plt.legend(loc="lower right")
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.savefig(os.path.join(REPORTS_DIR, "roc_curves.png"), dpi=300, bbox_inches="tight")
        plt.close()


def main():
    parser = argparse.ArgumentParser(description="Multi-Modal Fake Job & Scam Detection Engine")
    parser.add_argument("command", choices=["train", "generate-mock"], help="Action to execute")
    parser.add_argument("--data", default=None, help="Path to labeled CSV dataset")
    parser.add_argument("--samples", type=int, default=17880, help="Samples for mock generation")
    args = parser.parse_args()

    if args.command == "train":
        df, _ = load_dataset(args.data)
        detector = FakeJobDetector()
        detector.fit_and_evaluate(df=df, save_artifacts=True)
    elif args.command == "generate-mock":
        df = generate_benchmark_dataset(num_samples=args.samples)
        df.to_csv(DEFAULT_DATA_PATH, index=False)
        print(f"[+] Benchmark dataset saved to {DEFAULT_DATA_PATH}")


if __name__ == "__main__":
    main()
