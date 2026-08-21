import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_api_health():
    with TestClient(app) as client:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["models_loaded"] is True


def test_api_samples():
    with TestClient(app) as client:
        response = client.get("/api/samples")
        assert response.status_code == 200
        data = response.json()
        assert "samples" in data
        assert len(data["samples"]) >= 6


def test_api_analyze_job():
    with TestClient(app) as client:
        payload = {
            "title": "Senior Backend Developer",
            "company": "Amazon",
            "description": "Build high availability systems using Go and AWS.",
            "requirements": "5+ years backend systems experience.",
            "salary": "$150,000",
            "contact_email": "jobs@amazon.com",
            "application_url": "https://amazon.jobs"
        }
        response = client.post("/api/analyze-job", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "risk_level" in data
        assert "risk_score" in data
        assert "recommendation" in data
        assert "breakdown" in data
        assert "signals" in data
        assert data["risk_level"] == "Low"


def test_api_report_job_and_verify():
    with TestClient(app) as client:
        # 1. Report job
        report_payload = {
            "job_title": "Fake Data Typist",
            "company": "ScamCo",
            "job_description": "Pay $100 registration fee to get job",
            "report_reason": "asked_for_payment",
            "description": "Recruiter asked me to send wire transfer before interview.",
            "reporter_email": "candidate@example.com"
        }
        rep_res = client.post("/api/report-job", json=report_payload)
        assert rep_res.status_code == 200
        rep_data = rep_res.json()
        report_id = rep_data["id"]
        assert rep_data["status"] == "pending"

        # 2. List reports
        list_res = client.get("/api/reports?status=pending")
        assert list_res.status_code == 200
        assert any(r["id"] == report_id for r in list_res.json())

        # 3. Admin verify report
        verify_payload = {
            "report_id": report_id,
            "decision": "verified_fraud",
            "admin_notes": "Confirmed upfront payment request."
        }
        ver_res = client.post("/api/admin/verify-report", json=verify_payload)
        assert ver_res.status_code == 200
        assert ver_res.json()["status"] == "verified_fraud"


def test_api_model_info_and_dashboard():
    with TestClient(app) as client:
        info_res = client.get("/api/model-info")
        assert info_res.status_code == 200
        assert "active_version" in info_res.json()

        dash_res = client.get("/api/dashboard/stats")
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert "total_analyzed" in dash_data
        assert "risk_distribution" in dash_data

