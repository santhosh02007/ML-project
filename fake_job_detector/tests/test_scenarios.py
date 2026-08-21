import pytest
from app.services.risk_engine import RiskEngine


@pytest.fixture(scope="module")
def risk_engine():
    return RiskEngine.get_instance()


def test_scenario_1_genuine_job(risk_engine):
    """Scenario 1: Genuine job (normal company/salary/corporate email) -> Low risk."""
    job = {
        "title": "Senior Cloud Infrastructure Engineer",
        "company": "Amazon",
        "description": "Architect and deploy distributed backend microservices on AWS. Partner with systems engineers to ensure 99.99% service availability.",
        "requirements": "5+ years software engineering experience. Strong knowledge of Python, Go, and Linux systems.",
        "salary": "$140,000 - $175,000 per year",
        "contact_email": "aws-hiring@amazon.com",
        "application_url": "https://amazon.jobs/careers/cloud",
        "location": "Seattle, WA",
        "experience": "Mid-Senior Level"
    }
    res = risk_engine.analyze_job(job)
    assert res["risk_level"] == "Low"
    assert res["risk_score"] <= 30
    assert "Genuine" in res["verdict_badge"]


def test_scenario_2_registration_fee_scam(risk_engine):
    """Scenario 2: Registration-fee scam -> High risk."""
    job = {
        "title": "Data Entry & Document Processor",
        "company": "Global Processing Hub",
        "description": "Immediate start work from home typing job. Candidate must pay a registration fee of $120 to activate employee account and receive training materials.",
        "requirements": "Basic computer knowledge.",
        "salary": "$35/hr",
        "contact_email": "hr_globalhub@gmail.com",
        "application_url": "http://185.120.45.12/apply.php",
        "experience": "No experience needed"
    }
    res = risk_engine.analyze_job(job)
    assert res["risk_level"] == "High"
    assert res["risk_score"] >= 60
    assert any("Registration" in rf["description"] or "Payment" in rf["layer"] for rf in res["risk_factors"])


def test_scenario_3_unrealistic_salary_no_experience(risk_engine):
    """Scenario 3: Unrealistic salary, no experience -> Medium/High risk."""
    job = {
        "title": "Online Typing Clerk / Form Filler",
        "company": "QuickCash Inc",
        "description": "Start today! Earn $500 daily just typing simple records at home. No experience needed, zero skill requirements.",
        "requirements": "None. Immediate hire.",
        "salary": "$500 per day",
        "contact_email": "jobs@quickcash-portal.top",
        "application_url": "http://quickcash-portal.top/join",
        "experience": "0 years"
    }
    res = risk_engine.analyze_job(job)
    assert res["risk_level"] in ["Medium", "High"]
    assert res["risk_score"] >= 40
    assert any("Salary Anomaly" in rf["layer"] or "salary" in rf["description"].lower() for rf in res["risk_factors"])


def test_scenario_4_company_impersonation(risk_engine):
    """Scenario 4: Company impersonation (real name, suspicious email/URL) -> High risk."""
    job = {
        "title": "Lead Software Architect",
        "company": "Microsoft",
        "description": "Design core cloud architecture components. All interviews conducted exclusively on Telegram: @MicrosoftOfficialHR.",
        "requirements": "Software design skills. Contact recruiter on Telegram.",
        "salary": "$160,000",
        "contact_email": "microsoft.recruitment.team2026@gmail.com",
        "application_url": "https://microsofft-careers.xyz/apply",
        "experience": "5 years"
    }
    res = risk_engine.analyze_job(job)
    assert res["risk_level"] == "High"
    assert res["risk_score"] >= 60
    assert any("Impersonation" in rf["description"] or "Company" in rf["layer"] for rf in res["risk_factors"])


def test_scenario_5_rephrased_scam_wording(risk_engine):
    """Scenario 5: Rephrased scam wording not in the exact training vocabulary -> still flagged."""
    job = {
        "title": "Regional Operations Auditor",
        "company": "Apex Dynamics",
        "description": "Selected candidates must undergo a refundable financial verification before interview clearance. A cashier check will be mailed to your home address.",
        "requirements": "Active personal banking account.",
        "salary": "$2,500/week",
        "contact_email": "recruiter@apex-dynamics.click",
        "application_url": "https://apex-dynamics.click/form",
        "experience": "Entry level"
    }
    res = risk_engine.analyze_job(job)
    assert res["risk_level"] in ["Medium", "High"]
    assert res["risk_score"] >= 50
    assert any("refundable financial verification" in s.lower() or "cashier check" in s.lower() for s in res["matched_snippets"])


def test_scenario_6_legitimate_anti_scam_disclaimer(risk_engine):
    """Scenario 6: Legitimate anti-scam disclaimer -> NOT falsely flagged."""
    job = {
        "title": "Technical Account Manager",
        "company": "Stripe",
        "description": "Manage enterprise accounts and technical onboarding. Notice: We never ask for a registration fee, equipment deposit, or payments from candidates. Beware of recruiters asking for money.",
        "requirements": "4+ years customer-facing technical experience.",
        "salary": "$115,000 - $140,000",
        "contact_email": "careers@stripe.com",
        "application_url": "https://stripe.com/jobs/tam",
        "experience": "Mid Level"
    }
    res = risk_engine.analyze_job(job)
    assert res["risk_level"] == "Low"
    assert res["risk_score"] <= 30
    assert res["disclaimer_found"] is True


def test_scenario_7_tamil_english_code_mixed(risk_engine):
    """Scenario 7: Tamil-English code-mixed scam phrasing -> flagged."""
    job = {
        "title": "Data Entry Executive - Work From Home",
        "company": "Tamil Direct Services",
        "description": "Veettil irundhe sambalam peruga. Daily 3000 rupees direct payment. Urgent velai freshers apply panlam. Joining fee kattavum and send OTP for job confirmation on WhatsApp.",
        "requirements": "Mobile phone with WhatsApp.",
        "salary": "Rs 3000 daily payout",
        "contact_email": "velai.recruiter@gmail.com",
        "application_url": "http://tamil-jobs-online.biz/register",
        "experience": "Freshers welcome"
    }
    res = risk_engine.analyze_job(job)
    assert res["risk_score"] >= 40
    assert any("Code-Mixed" in rf["description"] or "Multilingual" in rf["description"] or "Payment" in rf["description"] for rf in res["risk_factors"])
