import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
STATIC_DIR = BASE_DIR / "static"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
(REPORTS_DIR / "figures").mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Fake Job Posting & Recruitment Scam Detector")
    VERSION: str = os.getenv("VERSION", "2.0.0")
    API_V1_STR: str = os.getenv("API_V1_STR", "/api")
    
    # Storage & DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'app.db'}")
    DATASET_PATH: str = os.getenv("DATASET_PATH", str(DATA_DIR / "fake_job_postings.csv"))
    
    # Model Artifact Paths
    VECTORIZER_PATH: str = os.getenv("VECTORIZER_PATH", str(MODELS_DIR / "tfidf_vectorizer.joblib"))
    LOGISTIC_REGRESSION_PATH: str = os.getenv("LOGISTIC_REGRESSION_PATH", str(MODELS_DIR / "logistic_regression.joblib"))
    RANDOM_FOREST_PATH: str = os.getenv("RANDOM_FOREST_PATH", str(MODELS_DIR / "random_forest.joblib"))
    CHAMPION_MODEL_PATH: str = os.getenv("CHAMPION_MODEL_PATH", str(MODELS_DIR / "champion_model.joblib"))
    MODEL_METADATA_PATH: str = os.getenv("MODEL_METADATA_PATH", str(MODELS_DIR / "model_metadata.json"))
    
    # Risk Score Thresholds
    RISK_THRESHOLD_LOW: int = int(os.getenv("RISK_THRESHOLD_LOW", "30"))     # 0-30: Genuine / Low Risk
    RISK_THRESHOLD_MEDIUM: int = int(os.getenv("RISK_THRESHOLD_MEDIUM", "60"))  # 31-60: Suspicious / Flag for Review
                                                                                # 61-100: High Risk / Likely Fraudulent
    
    # Security & Limits
    MAX_CSV_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_CSV_UPLOAD_SIZE_MB", "15"))
    MAX_BATCH_ROWS: int = int(os.getenv("MAX_BATCH_ROWS", "5000"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "120"))
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "admin-secret-key-change-in-prod")
    
    # External APIs (Optional with local fallback)
    VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    GOOGLE_SAFE_BROWSING_KEY: str = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")


settings = Settings()
