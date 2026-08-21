import datetime
import json
import os
from typing import Any, Dict, Generator, Optional
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class JobRecord(Base):
    """Stores analyzed job postings and risk assessment records."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), index=True, nullable=False)
    company = Column(String(255), index=True, nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    salary_range = Column(String(100), nullable=True)
    contact_email = Column(String(255), nullable=True)
    application_url = Column(String(500), nullable=True)
    
    # Risk Engine Outputs
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(50), nullable=False)
    verdict = Column(String(100), nullable=False)
    ml_probability = Column(Float, nullable=False)
    model_version = Column(String(50), default="v1.0.0")
    
    # Signals JSON
    breakdown_json = Column(Text, nullable=True)
    risk_factors_json = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class ReportRecord(Base):
    """Stores user scam reports awaiting admin review."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    job_id = Column(Integer, nullable=True, index=True)
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    job_description = Column(Text, nullable=True)
    
    # Report details
    report_reason = Column(String(100), nullable=False) # asked_for_payment, fake_company, suspicious_recruiter, personal_info_requested, fake_interview, other
    description = Column(Text, nullable=True)
    reporter_email = Column(String(255), nullable=True)
    
    # Verification workflow: "pending" | "verified_fraud" | "verified_genuine" | "rejected"
    status = Column(String(50), default="pending", index=True)
    admin_decision = Column(String(50), nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    resolved_at = Column(DateTime, nullable=True)


class ModelVersionRecord(Base):
    """Tracks model versions, lineage, training datasets, and performance metrics."""
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version_tag = Column(String(50), unique=True, index=True, nullable=False)
    model_name = Column(String(100), nullable=False)
    training_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    total_samples = Column(Integer, default=0)
    fraud_samples = Column(Integer, default=0)
    metrics_json = Column(Text, nullable=False) # Store evaluation metrics dictionary as JSON
    is_active = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)


def init_db():
    """Initializes database schema and populates initial model record if missing."""
    Base.metadata.create_all(bind=engine)
    
    # Ensure default v1 model record exists if model_metadata.json is available
    db = SessionLocal()
    try:
        existing = db.query(ModelVersionRecord).filter_by(version_tag="v1.0.0").first()
        if not existing and os.path.exists(settings.MODEL_METADATA_PATH):
            with open(settings.MODEL_METADATA_PATH, "r") as f:
                meta = json.load(f)
                
            champ = meta.get("champion_model", "Logistic Regression")
            v1_rec = ModelVersionRecord(
                version_tag="v1.0.0",
                model_name=f"TF-IDF + {champ}",
                total_samples=meta.get("total_dataset_rows", 17880),
                fraud_samples=meta.get("training_distribution", {}).get("train_resampled_fraud", 5095),
                metrics_json=json.dumps(meta.get("models", {})),
                is_active=True,
                notes="Initial production champion model trained on Kaggle EMSCAD dataset with 70/30 stratified balanced training split."
            )
            db.add(v1_rec)
            db.commit()
    except Exception as e:
        print(f"[!] Note on DB init: {e}")
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency injection helper for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
