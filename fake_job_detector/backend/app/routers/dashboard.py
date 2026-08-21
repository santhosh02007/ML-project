import json
import os
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.database import JobRecord, ModelVersionRecord, ReportRecord, get_db
from app.schemas import DashboardStatsResponse

router = APIRouter(tags=["Dashboard & Analytics"])


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_statistics(db: Session = Depends(get_db)):
    """
    Returns high-level platform telemetry, risk distribution, and threat analytics.
    """
    total_jobs = db.query(JobRecord).count()
    high_risk_count = db.query(JobRecord).filter(JobRecord.risk_level == "High").count()
    medium_risk_count = db.query(JobRecord).filter(JobRecord.risk_level == "Medium").count()
    low_risk_count = db.query(JobRecord).filter(JobRecord.risk_level == "Low").count()

    total_reports = db.query(ReportRecord).count()
    pending_reports = db.query(ReportRecord).filter(ReportRecord.status == "pending").count()

    recent_jobs_recs = db.query(JobRecord).order_by(JobRecord.created_at.desc()).limit(8).all()
    recent_jobs = [
        {
            "id": j.id,
            "title": j.title,
            "company": j.company or "Unspecified",
            "risk_score": j.risk_score,
            "risk_level": j.risk_level,
            "verdict": j.verdict,
            "created_at": j.created_at.isoformat() if j.created_at else None
        }
        for j in recent_jobs_recs
    ]

    # Active model metadata
    active_model = {
        "version": "v1.0.0",
        "champion_model": "Logistic Regression",
        "training_date": "2026-08-19"
    }
    if os.path.exists(settings.MODEL_METADATA_PATH):
        try:
            with open(settings.MODEL_METADATA_PATH, "r") as f:
                meta = json.load(f)
                active_model = {
                    "version": meta.get("version", "v1.0.0"),
                    "champion_model": meta.get("champion_model", "Logistic Regression"),
                    "training_date": meta.get("training_timestamp", "").split("T")[0] if "T" in meta.get("training_timestamp", "") else meta.get("training_timestamp", ""),
                    "dataset_version": meta.get("dataset_version", "Kaggle_EMSCAD_17880"),
                    "fraud_recall": meta.get("models", {}).get("logistic_regression", {}).get("test_metrics", {}).get("fraud_recall", 1.0),
                    "fraud_f1": meta.get("models", {}).get("logistic_regression", {}).get("test_metrics", {}).get("fraud_f1", 1.0)
                }
        except Exception:
            pass

    return DashboardStatsResponse(
        total_analyzed=total_jobs,
        risk_distribution={
            "High": high_risk_count,
            "Medium": medium_risk_count,
            "Low": low_risk_count
        },
        recent_jobs=recent_jobs,
        total_reports=total_reports,
        pending_reports=pending_reports,
        active_model=active_model
    )


@router.get("/threat-insights")
def get_threat_insights():
    """
    Returns threat trends, scam categories frequency, and common trigger keywords.
    """
    return {
        "top_scam_categories": [
            {"category": "Registration & Upfront Fee Scams", "share_pct": 38, "risk_level": "High"},
            {"category": "Brand Impersonation & Free Webmail", "share_pct": 27, "risk_level": "High"},
            {"category": "Check Cashing & Wire Transfer Overpayment", "share_pct": 18, "risk_level": "High"},
            {"category": "Unrealistic Salary & No Experience", "share_pct": 11, "risk_level": "Medium"},
            {"category": "Chat-Only Interviews (Telegram/WhatsApp)", "share_pct": 6, "risk_level": "High"}
        ],
        "top_threat_keywords": [
            {"keyword": "registration fee", "threat_weight": 40, "frequency": "Frequent"},
            {"keyword": "wire transfer", "threat_weight": 45, "frequency": "Frequent"},
            {"keyword": "cashier check", "threat_weight": 45, "frequency": "Frequent"},
            {"keyword": "telegram interview", "threat_weight": 30, "frequency": "Very Frequent"},
            {"keyword": "equipment deposit", "threat_weight": 35, "frequency": "Moderate"},
            {"keyword": "otp verification", "threat_weight": 35, "frequency": "Moderate"},
            {"keyword": "daily payout $500", "threat_weight": 25, "frequency": "Frequent"},
            {"keyword": "pay before joining", "threat_weight": 38, "frequency": "Frequent"},
            {"keyword": "pan / aadhaar copy", "threat_weight": 35, "frequency": "Regional (India)"}
        ]
    }
