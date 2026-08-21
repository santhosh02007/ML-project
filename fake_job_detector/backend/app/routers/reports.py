import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import ReportRecord, get_db
from app.schemas import AdminVerifyReportRequest, ReportCreateRequest, ReportResponse
from app.services.security import SecuritySanitizer

router = APIRouter(tags=["Reports & Verification"])


@router.post("/report-job", response_model=ReportResponse)
def submit_job_report(req: ReportCreateRequest, db: Session = Depends(get_db)):
    """
    Submits a user report for a suspicious job posting.
    Stored with 'pending' status for admin verification (never directly auto-trained on).
    """
    # Sanitize any PII entered in the user report
    clean_desc = SecuritySanitizer.mask_pii(req.description or "")
    clean_job_desc = SecuritySanitizer.mask_pii(req.job_description or "")

    report = ReportRecord(
        job_id=req.job_id,
        job_title=req.job_title,
        company=req.company,
        job_description=clean_job_desc,
        report_reason=req.report_reason,
        description=clean_desc,
        reporter_email=req.reporter_email,
        status="pending"
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return report


@router.get("/reports", response_model=List[ReportResponse])
def list_reports(
    status: Optional[str] = Query(None, description="Filter by status: pending, verified_fraud, verified_genuine, rejected"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Lists submitted user reports for admin inspection."""
    query = db.query(ReportRecord)
    if status:
        query = query.filter(ReportRecord.status == status)
    reports = query.order_by(ReportRecord.created_at.desc()).limit(limit).all()
    return reports


@router.post("/admin/verify-report", response_model=ReportResponse)
def verify_report(req: AdminVerifyReportRequest, db: Session = Depends(get_db)):
    """
    Admin verification endpoint to approve or reject a reported job posting.
    Verified reports are designated for the continuous retraining pipeline.
    """
    report = db.query(ReportRecord).filter(ReportRecord.id == req.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report ID not found.")

    if req.decision not in ["verified_fraud", "verified_genuine", "rejected"]:
        raise HTTPException(status_code=400, detail="Decision must be 'verified_fraud', 'verified_genuine', or 'rejected'.")

    report.status = req.decision
    report.admin_decision = req.decision
    report.admin_notes = req.admin_notes
    report.resolved_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(report)
    return report
