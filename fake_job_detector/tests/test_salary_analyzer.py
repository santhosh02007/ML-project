import pytest
from app.services.salary_analyzer import SalaryAnalyzer


def test_salary_standard_within_range():
    res = SalaryAnalyzer.evaluate(
        salary_str="$70k - $90k",
        job_title="Software Developer",
        experience_level="2-4 years"
    )
    assert res["anomaly_level"] == "Low"
    assert res["risk_score"] == 0


def test_salary_exorbitant_entry_level_anomaly():
    res = SalaryAnalyzer.evaluate(
        salary_str="$500 daily",
        job_title="Data Entry Clerk",
        experience_level="No experience",
        full_text="Work from home simple typing jobs earn $500 daily"
    )
    assert res["anomaly_level"] == "High"
    assert res["risk_score"] >= 70


def test_salary_hourly_anomaly_for_typing():
    res = SalaryAnalyzer.evaluate(
        salary_str="$65/hr",
        job_title="Typist / Assistant",
        experience_level="Entry Level"
    )
    assert res["anomaly_level"] == "High"
    assert res["risk_score"] >= 70
