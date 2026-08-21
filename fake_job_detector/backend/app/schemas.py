import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class JobAnalyzeRequest(BaseModel):
    title: str = Field(..., description="Job Title, e.g. 'Customer Service Specialist'")
    company: Optional[str] = Field(None, description="Company or Employer Name")
    company_name: Optional[str] = Field(None, description="Alternative alias for Company Name")
    description: str = Field(..., description="Full text description of the job posting")
    requirements: Optional[str] = Field(None, description="Job requirements / qualifications")
    benefits: Optional[str] = Field(None, description="Company perks / benefits")
    company_profile: Optional[str] = Field(None, description="About the company")
    location: Optional[str] = Field(None, description="City, State, Country or 'Remote'")
    salary: Optional[str] = Field(None, description="Salary range, e.g. '$60k-$80k' or '$35/hr'")
    salary_range: Optional[str] = Field(None, description="Alternative alias for Salary")
    contact_email: Optional[str] = Field(None, description="Recruiter email address")
    email: Optional[str] = Field(None, description="Alternative alias for contact email")
    application_url: Optional[str] = Field(None, description="Application link or company website")
    company_website: Optional[str] = Field(None, description="Alternative alias for website")
    experience: Optional[str] = Field(None, description="Required experience level, e.g. 'Entry Level'")
    required_experience: Optional[str] = Field(None, description="Alternative alias for experience")
    model_type: Optional[str] = Field("champion", description="Model choice: 'champion', 'logistic_regression', 'random_forest'")


class RiskFactor(BaseModel):
    layer: str
    severity: str
    description: str
    evidence: List[str] = []


class JobAnalyzeResponse(BaseModel):
    job_id: Optional[int] = None
    risk_level: str # "Low" | "Medium" | "High"
    risk_score: int # 0 - 100
    verdict: str
    verdict_badge: str
    recommendation: str
    risk_factors: List[RiskFactor] = []
    matched_snippets: List[str] = []
    disclaimer_found: bool = False
    breakdown: Dict[str, Any]
    signals: Dict[str, Any]
    claims_policy_notice: str
    analysis_time_ms: float


class BatchAnalyzeItemResult(BaseModel):
    row_index: int
    title: str
    company: Optional[str] = None
    risk_score: int
    risk_level: str
    verdict: str
    top_reason: str


class BatchAnalyzeResponse(BaseModel):
    total_processed: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    results: List[BatchAnalyzeItemResult]
    download_id: str


class ReportCreateRequest(BaseModel):
    job_id: Optional[int] = None
    job_title: str
    company: Optional[str] = None
    job_description: Optional[str] = None
    report_reason: str # asked_for_payment, fake_company, suspicious_recruiter, personal_info_requested, fake_interview, other
    description: Optional[str] = None
    reporter_email: Optional[str] = None


class ReportResponse(BaseModel):
    id: int
    job_id: Optional[int] = None
    job_title: str
    company: Optional[str] = None
    report_reason: str
    description: Optional[str] = None
    reporter_email: Optional[str] = None
    status: str
    admin_decision: Optional[str] = None
    admin_notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    resolved_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class AdminVerifyReportRequest(BaseModel):
    report_id: int
    decision: str # "verified_fraud" | "verified_genuine" | "rejected"
    admin_notes: Optional[str] = None
    admin_api_key: Optional[str] = None


class ModelRetrainRequest(BaseModel):
    admin_api_key: Optional[str] = None
    new_version_tag: Optional[str] = None
    notes: Optional[str] = None


class ModelRetrainResponse(BaseModel):
    status: str
    previous_version: str
    new_version: str
    metrics_comparison: Dict[str, Any]
    promoted_to_champion: bool
    message: str


class DashboardStatsResponse(BaseModel):
    total_analyzed: int
    risk_distribution: Dict[str, int]
    recent_jobs: List[Dict[str, Any]]
    total_reports: int
    pending_reports: int
    active_model: Dict[str, Any]
