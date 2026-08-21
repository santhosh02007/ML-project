import time
from typing import Any, Dict, List, Optional

from app.config import settings
from app.ml.inference import MLInferenceEngine
from app.ml.preprocessor import build_combined_text_from_dict
from app.services.campaign_detector import CampaignDetector
from app.services.company_verifier import CompanyVerifier
from app.services.rule_engine import RuleEngine
from app.services.salary_analyzer import SalaryAnalyzer
from app.services.url_analyzer import URLAnalyzer


class RiskEngine:
    """
    Unified Multi-Layer Recruitment Fraud Risk Aggregator & Explainability Engine.
    Aggregates ML predictions, weighted rules, salary anomalies, URL heuristics,
    company authenticity, and syndicated campaign detection into an explainable result.
    """

    _instance: Optional["RiskEngine"] = None

    def __init__(self):
        self.ml_engine = MLInferenceEngine.get_instance()
        self.campaign_detector = CampaignDetector.get_instance()

    @classmethod
    def get_instance(cls) -> "RiskEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def analyze_job(self, job_dict: Dict[str, Any], model_type: str = "champion") -> Dict[str, Any]:
        """
        Executes end-to-end multi-layer fraud analysis on a structured job posting.
        """
        t0 = time.perf_counter()

        # Extract Fields
        title = job_dict.get("title", "")
        company_name = job_dict.get("company_name", "") or job_dict.get("company", "")
        description = job_dict.get("description", "")
        requirements = job_dict.get("requirements", "")
        benefits = job_dict.get("benefits", "")
        company_profile = job_dict.get("company_profile", "")
        location = job_dict.get("location", "")
        salary = job_dict.get("salary_range", "") or job_dict.get("salary", "")
        contact_email = job_dict.get("contact_email", "") or job_dict.get("email", "")
        application_url = job_dict.get("application_url", "") or job_dict.get("company_website", "")
        experience_level = job_dict.get("required_experience", "") or job_dict.get("experience", "")

        # 1. Build Combined Text
        combined_text = build_combined_text_from_dict(job_dict)

        # 2. Layer 1: ML Model Classification
        ml_res = self.ml_engine.predict_text(combined_text, model_type=model_type)
        ml_prob = ml_res["fraud_probability"]  # 0.0 to 1.0
        ml_score = int(ml_prob * 100)          # 0 to 100

        # 3. Layer 2: Context-Aware Rule Engine
        rule_res = RuleEngine.evaluate(combined_text)
        rule_score = rule_res["rule_score"]    # 0 to 100

        # 4. Layer 3: Salary Anomaly Detection
        salary_res = SalaryAnalyzer.evaluate(
            salary_str=salary,
            job_title=title,
            experience_level=experience_level,
            full_text=combined_text
        )
        salary_risk = salary_res["risk_score"] # 0 to 100

        # 5. Layer 4: URL & Domain Risk Analysis
        url_res = URLAnalyzer.evaluate(
            application_url=application_url,
            text=combined_text,
            company_name=company_name
        )
        url_risk = url_res["overall_url_risk_score"] # 0 to 100

        # 6. Layer 5: Company & Email Verification
        company_res = CompanyVerifier.evaluate(
            company_name=company_name,
            contact_email=contact_email,
            company_website=application_url,
            full_text=combined_text
        )
        company_risk = company_res["risk_score"] # 0 to 100

        # 7. Layer 6: Duplicate / Syndicated Scam Campaign Detection
        campaign_res = self.campaign_detector.evaluate(combined_text)
        campaign_risk = campaign_res["risk_contribution"] # 0 to 40

        # =========================================================================
        # RISK SCORE AGGREGATION
        # Multi-layer weighted blend:
        # ML: 30%, Rules: 30%, Company/Email: 20%, URL: 15%, Salary: 5%
        # Plus bonus campaign duplicate risk if triggered
        # =========================================================================
        base_weighted_score = (
            (ml_score * 0.30) +
            (rule_score * 0.30) +
            (company_risk * 0.20) +
            (url_risk * 0.15) +
            (salary_risk * 0.05)
        )

        # Apply campaign duplicate bonus
        if campaign_res["campaign_match"]:
            base_weighted_score = max(base_weighted_score, base_weighted_score + campaign_risk * 0.5)

        # High-severity override triggers (e.g. asking for bank credentials or severe impersonation)
        if company_risk >= 80 or rule_score >= 70:
            base_weighted_score = max(base_weighted_score, 72)
            
        # Disclaimer adjustment: if legitimate anti-scam disclaimer found and no other severe signals
        if rule_res["disclaimer_found"] and rule_score == 0 and company_risk <= 20 and ml_prob < 0.6:
            base_weighted_score = min(base_weighted_score, 25)

        # Final integer risk score clamped to [0, 100]
        final_risk_score = int(round(min(100, max(0, base_weighted_score))))

        # Determine Risk Tier
        if final_risk_score <= settings.RISK_THRESHOLD_LOW:
            risk_level = "Low"
            verdict = "Likely Genuine"
            verdict_badge = "Low Risk (Likely Genuine)"
        elif final_risk_score <= settings.RISK_THRESHOLD_MEDIUM:
            risk_level = "Medium"
            verdict = "Suspicious"
            verdict_badge = "Medium Risk (Suspicious — Flag for Review)"
        else:
            risk_level = "High"
            verdict = "High Risk"
            verdict_badge = "High Risk (Likely Fraudulent)"

        # =========================================================================
        # COMPOSE EXPLAINABLE REASONS & RISK FACTORS
        # =========================================================================
        risk_factors = []

        if ml_prob >= 0.6:
            risk_factors.append({
                "layer": "Machine Learning",
                "severity": "High" if ml_prob >= 0.8 else "Medium",
                "description": f"Statistical text classification model predicts {int(ml_prob*100)}% likelihood of recruitment fraud based on learned linguistic patterns.",
                "evidence": [f["term"] for f in ml_res["top_features"][:4]]
            })

        for rule in rule_res["triggered_rules"]:
            risk_factors.append({
                "layer": "Rule Engine",
                "severity": "High" if rule["weight"] >= 35 else "Medium",
                "description": f"{rule['rule_name']}: {rule['explanation']}",
                "evidence": rule["snippets"]
            })

        if company_risk >= 35:
            risk_factors.append({
                "layer": "Company & Domain Verification",
                "severity": "High" if company_risk >= 70 else "Medium",
                "description": " ".join(company_res["reasons"]),
                "evidence": [contact_email or "No Email", company_name or "No Company"]
            })

        if url_risk >= 30:
            risk_factors.append({
                "layer": "URL & Domain Analysis",
                "severity": "High" if url_risk >= 60 else "Medium",
                "description": "; ".join(url_res["signals"]),
                "evidence": [u["url"] for u in url_res["urls_analyzed"] if u["risk_score"] > 0]
            })

        if salary_risk >= 35:
            risk_factors.append({
                "layer": "Salary Anomaly",
                "severity": salary_res["anomaly_level"],
                "description": salary_res["reason"],
                "evidence": [salary_res["extracted_salary"]]
            })

        if campaign_res["campaign_match"]:
            risk_factors.append({
                "layer": "Campaign Duplicate Detection",
                "severity": "High",
                "description": campaign_res["reason"],
                "evidence": [campaign_res["matched_campaign"]["campaign_name"]]
            })

        # =========================================================================
        # GENERATE HEDGED ACTIONABLE RECOMMENDATION
        # =========================================================================
        if risk_level == "High":
            recommendation = (
                "DO NOT transfer money, pay any registration or equipment fees, or share sensitive banking/ID details (such as OTPs, PAN, or Aadhaar). "
                "This posting exhibits strong markers of recruitment fraud. Verify the employer independently by visiting their official career portal."
            )
        elif risk_level == "Medium":
            recommendation = (
                "Exercise caution and conduct independent verification before submitting personal or financial information. "
                "Confirm the recruiter's identity through official company channels and avoid communications conducted solely via unverified chat applications."
            )
        else:
            recommendation = (
                "This posting appears standard with low risk signals. However, always exercise baseline job search vigilance: "
                "never pay upfront for employment offers or share net-banking credentials."
            )

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            "risk_level": risk_level,
            "risk_score": final_risk_score,
            "verdict": verdict,
            "verdict_badge": verdict_badge,
            "recommendation": recommendation,
            "risk_factors": risk_factors,
            "matched_snippets": rule_res["matched_snippets"],
            "disclaimer_found": rule_res["disclaimer_found"],
            "breakdown": {
                "ml_probability": ml_prob,
                "ml_score": ml_score,
                "rule_score": rule_score,
                "company_risk_score": company_risk,
                "url_risk_score": url_risk,
                "salary_risk_score": salary_risk,
                "campaign_similarity": campaign_res["similarity_score"]
            },
            "signals": {
                "ml_model": ml_res,
                "rules": rule_res,
                "salary": salary_res,
                "url": url_res,
                "company": company_res,
                "campaign": campaign_res
            },
            "claims_policy_notice": "Decision-support evaluation only; not an absolute guarantee. Verify through independent channels.",
            "analysis_time_ms": elapsed_ms
        }
