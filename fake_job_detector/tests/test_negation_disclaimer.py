import pytest
from app.services.rule_engine import RuleEngine
from app.services.risk_engine import RiskEngine


def test_anti_scam_disclaimer_not_falsely_flagged():
    text = (
        "We are looking for a Senior Product Manager to lead our engineering division. "
        "Important Note: We never ask for any registration fee, deposit, or monetary payment from candidates. "
        "Beware of fraudulent entities requesting money under our name. No application fee is required at any stage."
    )
    res = RuleEngine.evaluate(text)
    
    # Disclaimer must be recognized
    assert res["disclaimer_found"] is True
    # Crucial: The disclaimer must negate the payment rule so rule_score stays 0
    assert res["rule_score"] == 0
    assert len(res["triggered_rules"]) == 0


def test_anti_scam_disclaimer_in_full_job_analysis():
    job_dict = {
        "title": "Lead DevOps Architect",
        "company": "Stripe",
        "description": "Architect scalable payment infrastructure. Note: We never charge any fee or request bank payments during recruitment.",
        "requirements": "7+ years AWS and Kubernetes experience.",
        "salary": "$160,000 - $200,000",
        "contact_email": "careers@stripe.com",
        "application_url": "https://stripe.com/jobs/devops"
    }
    
    risk_res = RiskEngine.get_instance().analyze_job(job_dict)
    
    assert risk_res["risk_level"] == "Low"
    assert risk_res["risk_score"] <= 30
    assert risk_res["disclaimer_found"] is True
