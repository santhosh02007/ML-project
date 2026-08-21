import io
import json
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
import pandas as pd
from sqlalchemy.orm import Session

from app.config import settings
from app.database import JobRecord, get_db
from app.schemas import BatchAnalyzeItemResult, BatchAnalyzeResponse, JobAnalyzeRequest, JobAnalyzeResponse
from app.services.risk_engine import RiskEngine
from app.services.security import SecuritySanitizer

router = APIRouter(tags=["Analysis"])

# In-memory temporary batch store for CSV downloads
BATCH_DOWNLOAD_CACHE: Dict[str, pd.DataFrame] = {}

PRESET_SAMPLES = [
    {
        "id": "sample-1-genuine",
        "title": "Senior Software Engineer - Cloud Platforms",
        "company": "Amazon Web Services",
        "location": "Seattle, WA (Hybrid)",
        "salary": "$140,000 - $180,000 per year",
        "contact_email": "recruiting@amazon.com",
        "application_url": "https://amazon.jobs/en/jobs/254128",
        "experience": "5+ years",
        "description": "We are seeking an experienced Software Engineer to design, scale, and maintain high-throughput cloud infrastructure services. You will collaborate with cross-functional product and security teams to build resilient microservices.",
        "requirements": "Bachelor's degree in Computer Science or equivalent. Proficient in Python, Java, or Go. Experience with distributed systems and AWS services.",
        "benefits": "Comprehensive health benefits, 401(k) matching, stock unit awards, flexible paid time off.",
        "category": "Genuine Corporate Posting"
    },
    {
        "id": "sample-2-fee-scam",
        "title": "Data Entry Clerk - Remote Starter Kit",
        "company": "Global Logistics Express LLC",
        "location": "Remote",
        "salary": "$35 - $45 per hour",
        "contact_email": "careers_globallogistics@gmail.com",
        "application_url": "http://185.220.101.5/apply-now.php",
        "experience": "No experience needed",
        "description": "Work from home full time or part time entering data into our spreadsheets. Earn up to $45/hr. Selected candidates must pay a small refundable registration fee of $150 and equipment deposit for home office software configuration prior to commencing work.",
        "requirements": "Basic typing skills, internet access. Must be able to pay registration fee via wire transfer or cashier check to secure slot.",
        "benefits": "Daily payout, guaranteed income, flexible hours.",
        "category": "Registration & Equipment Fee Scam"
    },
    {
        "id": "sample-3-unrealistic-salary",
        "title": "Entry Level Typing Assistant / Survey Taker",
        "company": "FastCash Careers",
        "location": "Remote / Anywhere",
        "salary": "$500 per day / $150,000 annual",
        "contact_email": "support@fastcash-surveys.top",
        "application_url": "http://fastcash-surveys.top/job?id=992",
        "experience": "Zero experience required",
        "description": "Urgent hiring! Start today and earn $500 daily just by typing simple documents and reviewing products. Immediate start today without interview.",
        "requirements": "No previous skills or education required. Age 18+.",
        "benefits": "Guaranteed daily payout, instant wire transfers.",
        "category": "Unrealistic Salary Anomaly"
    },
    {
        "id": "sample-4-impersonation",
        "title": "Senior Product Manager",
        "company": "Microsoft Corporation",
        "location": "Redmond, WA / Remote",
        "salary": "$150,000 - $190,000 per year",
        "contact_email": "microsoft.recruitment.team.usa@gmail.com",
        "application_url": "https://microsofft-careers-portal.xyz/apply",
        "experience": "4+ years",
        "description": "Microsoft is seeking a talented Product Manager to lead cloud enterprise products. All interviews will be conducted exclusively via Telegram ID @MicrosoftHROfficial.",
        "requirements": "Experience in agile software lifecycle. Connect with recruiter on Telegram.",
        "benefits": "Medical, dental, retirement plan.",
        "category": "Enterprise Brand Impersonation"
    },
    {
        "id": "sample-5-rephrased-scam",
        "title": "Operations & Quality Assurance Auditor",
        "company": "Apex Consulting Group",
        "location": "Remote",
        "salary": "$3,200 per week",
        "contact_email": "hr@apex-consulting.click",
        "application_url": "https://apex-consulting.click/portal",
        "experience": "Entry Level",
        "description": "Candidates are required to undergo a refundable financial verification check before the initial interview. You will receive a cashier check in the mail to purchase testing software and wire back excess balance.",
        "requirements": "Reliable computer, active personal bank account for verification clearance.",
        "benefits": "High weekly payouts.",
        "category": "Rephrased Check-Cashing Scam"
    },
    {
        "id": "sample-6-disclaimer-job",
        "title": "Customer Operations Lead",
        "company": "Stripe Technologies",
        "location": "San Francisco, CA / Remote",
        "salary": "$110,000 - $135,000 per year",
        "contact_email": "jobs@stripe.com",
        "application_url": "https://stripe.com/jobs",
        "experience": "3+ years",
        "description": "Lead customer onboarding and operational workflows. We never ask for any registration fee, deposit, or payments at any stage of recruitment. Beware of unauthorized scammers impersonating our hiring team.",
        "requirements": "Strong communication, problem solving, customer empathy.",
        "benefits": "Equity, comprehensive healthcare, wellness stipend.",
        "category": "Legitimate Anti-Scam Disclaimer"
    },
    {
        "id": "sample-7-tamil-english",
        "title": "Data Entry Executive - Work From Home",
        "company": "Tamil Digital Services",
        "location": "Chennai / Remote",
        "salary": "Rs 3000 daily payout",
        "contact_email": "velai.recruiter@gmail.com",
        "application_url": "http://tamil-jobs-online.biz/register",
        "experience": "Freshers welcome",
        "description": "Veettil irundhe sambalam peruga. Daily 3000 rupees direct payment. Urgent velai freshers apply panlam. Joining fee kattavum and send OTP for immediate job confirmation on WhatsApp.",
        "requirements": "Mobile phone with WhatsApp.",
        "benefits": "Daily cash transfer.",
        "category": "Tamil-English Code-Mixed Scam"
    }
]


@router.get("/samples")
def get_sample_jobs():
    """Returns curated preset job samples covering all major test scenarios."""
    return {"samples": PRESET_SAMPLES}


@router.post("/analyze-job", response_model=JobAnalyzeResponse)
def analyze_job_posting(req: JobAnalyzeRequest, db: Session = Depends(get_db)):
    """
    Analyzes a single job posting across all ML, Rule, URL, Company, and Salary risk layers.
    Masks sensitive PII before persistence and returns explainable risk breakdown.
    """
    job_dict = req.model_dump()
    # Normalize aliases
    if not job_dict.get("company") and job_dict.get("company_name"):
        job_dict["company"] = job_dict["company_name"]
    if not job_dict.get("salary") and job_dict.get("salary_range"):
        job_dict["salary"] = job_dict["salary_range"]
    if not job_dict.get("contact_email") and job_dict.get("email"):
        job_dict["contact_email"] = job_dict["email"]
    if not job_dict.get("application_url") and job_dict.get("company_website"):
        job_dict["application_url"] = job_dict["company_website"]
    if not job_dict.get("experience") and job_dict.get("required_experience"):
        job_dict["experience"] = job_dict["required_experience"]

    # 1. Run Multi-Layer Risk Engine
    risk_engine = RiskEngine.get_instance()
    analysis = risk_engine.analyze_job(job_dict, model_type=req.model_type or "champion")

    # 2. Sanitize PII for persistence
    sanitized_dict = SecuritySanitizer.sanitize_job_dict(job_dict)

    # 3. Persist in Database
    job_rec = JobRecord(
        title=sanitized_dict.get("title", "Untitled"),
        company=sanitized_dict.get("company"),
        location=sanitized_dict.get("location"),
        description=sanitized_dict.get("description", ""),
        requirements=sanitized_dict.get("requirements"),
        salary_range=sanitized_dict.get("salary"),
        contact_email=sanitized_dict.get("contact_email"),
        application_url=sanitized_dict.get("application_url"),
        risk_score=analysis["risk_score"],
        risk_level=analysis["risk_level"],
        verdict=analysis["verdict"],
        ml_probability=analysis["breakdown"]["ml_probability"],
        model_version="v1.0.0",
        breakdown_json=json.dumps(analysis["breakdown"]),
        risk_factors_json=json.dumps(analysis["risk_factors"])
    )
    db.add(job_rec)
    db.commit()
    db.refresh(job_rec)

    analysis["job_id"] = job_rec.id
    return analysis


@router.post("/analyze-batch", response_model=BatchAnalyzeResponse)
async def analyze_batch_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Uploads and analyzes a batch CSV file containing multiple job postings.
    Returns summary statistics and batch download token.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a CSV format file.")

    content = await file.read()
    if len(content) > settings.MAX_CSV_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size ({settings.MAX_CSV_UPLOAD_SIZE_MB}MB).")

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")

    if len(df) > settings.MAX_BATCH_ROWS:
        df = df.head(settings.MAX_BATCH_ROWS)

    # Standardize Column Aliases
    col_map = {
        "job_title": "title",
        "job_description": "description",
        "company_name": "company",
        "email": "contact_email",
        "website": "application_url",
        "salary_range": "salary"
    }
    df.rename(columns={k: v for k, v in col_map.items() if k in df.columns}, inplace=True)

    if "description" not in df.columns and "title" not in df.columns:
        raise HTTPException(status_code=400, detail="CSV must contain at least 'title' or 'description' columns.")

    risk_engine = RiskEngine.get_instance()
    results: List[BatchAnalyzeItemResult] = []
    
    risk_scores = []
    risk_levels = []
    verdicts = []
    top_reasons = []

    high_count = 0
    med_count = 0
    low_count = 0

    for idx, row in df.iterrows():
        job_dict = {
            "title": str(row.get("title", "")) if pd.notna(row.get("title")) else "",
            "company": str(row.get("company", "")) if pd.notna(row.get("company")) else "",
            "description": str(row.get("description", "")) if pd.notna(row.get("description")) else "",
            "requirements": str(row.get("requirements", "")) if pd.notna(row.get("requirements")) else "",
            "benefits": str(row.get("benefits", "")) if pd.notna(row.get("benefits")) else "",
            "salary": str(row.get("salary", "")) if pd.notna(row.get("salary")) else "",
            "contact_email": str(row.get("contact_email", "")) if pd.notna(row.get("contact_email")) else "",
            "application_url": str(row.get("application_url", "")) if pd.notna(row.get("application_url")) else "",
            "location": str(row.get("location", "")) if pd.notna(row.get("location")) else "",
            "experience": str(row.get("experience", "")) if pd.notna(row.get("experience")) else "",
        }

        eval_res = risk_engine.analyze_job(job_dict)
        r_score = eval_res["risk_score"]
        r_level = eval_res["risk_level"]
        r_verdict = eval_res["verdict"]

        top_reason = "No significant risk signals"
        if eval_res["risk_factors"]:
            top_reason = eval_res["risk_factors"][0]["description"]

        risk_scores.append(r_score)
        risk_levels.append(r_level)
        verdicts.append(r_verdict)
        top_reasons.append(top_reason)

        if r_level == "High":
            high_count += 1
        elif r_level == "Medium":
            med_count += 1
        else:
            low_count += 1

        results.append(BatchAnalyzeItemResult(
            row_index=int(idx),
            title=job_dict["title"] or "Untitled",
            company=job_dict["company"] or "Unspecified",
            risk_score=r_score,
            risk_level=r_level,
            verdict=r_verdict,
            top_reason=top_reason
        ))

    # Append evaluation columns to DataFrame
    df["risk_score"] = risk_scores
    df["risk_level"] = risk_levels
    df["verdict"] = verdicts
    df["primary_risk_reason"] = top_reasons

    download_id = str(uuid.uuid4())
    BATCH_DOWNLOAD_CACHE[download_id] = df

    return BatchAnalyzeResponse(
        total_processed=len(df),
        high_risk_count=high_count,
        medium_risk_count=med_count,
        low_risk_count=low_count,
        results=results[:100],  # Return first 100 in payload for fast render
        download_id=download_id
    )


@router.get("/download-batch/{download_id}")
def download_batch_results(download_id: str):
    """Downloads the scored batch dataset as a CSV file."""
    df = BATCH_DOWNLOAD_CACHE.get(download_id)
    if df is None:
        raise HTTPException(status_code=404, detail="Batch result expired or not found.")

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)

    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=fraud_detection_batch_{download_id[:8]}.csv"}
    )
