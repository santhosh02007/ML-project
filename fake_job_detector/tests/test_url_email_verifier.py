import pytest
from app.services.url_analyzer import URLAnalyzer
from app.services.company_verifier import CompanyVerifier


def test_url_analyzer_flags_insecure_and_suspicious_tld():
    res = URLAnalyzer.analyze_single_url("http://recruitment-portal.xyz/apply")
    assert res["risk_score"] >= 40
    assert any("Insecure plain HTTP" in s for s in res["signals"])
    assert any(".xyz" in s for s in res["signals"])


def test_url_analyzer_flags_ip_address_host():
    res = URLAnalyzer.analyze_single_url("http://192.168.1.100/jobs/form.php")
    assert res["risk_score"] >= 65
    assert any("raw IP address" in s or "direct IP" in s for s in res["signals"])


def test_url_analyzer_flags_shortener():
    res = URLAnalyzer.analyze_single_url("https://bit.ly/3xJobOffer")
    assert res["risk_score"] >= 40
    assert any("shortening service" in s for s in res["signals"])


def test_company_verifier_detects_brand_impersonation_with_free_email():
    res = CompanyVerifier.evaluate(
        company_name="Google",
        contact_email="google.hiring.manager2026@gmail.com",
        company_website="https://google.com"
    )
    assert res["status"] == "Suspicious"
    assert res["risk_score"] >= 70
    assert any("Impersonation" in r for r in res["reasons"])


def test_company_verifier_verifies_matching_corporate_domain():
    res = CompanyVerifier.evaluate(
        company_name="Microsoft",
        contact_email="careers@microsoft.com",
        company_website="https://microsoft.com"
    )
    assert res["status"] == "Verified"
    assert res["risk_score"] <= 10
