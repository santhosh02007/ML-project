import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse


class CompanyVerifier:
    """
    Verifies consistency between claimed company name, official website, and recruiter contact email.
    Detects brand impersonation, lookalike domains, and free webmail mismatch.
    """

    FREE_EMAIL_DOMAINS = {
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "protonmail.com",
        "mail.com", "aol.com", "zoho.com", "yandex.com", "icloud.com", "gmx.com"
    }

    # Major recognizable corporate brands and their official base domains
    KNOWN_ENTERPRISES = {
        "google": ["google.com", "alphabet.com"],
        "microsoft": ["microsoft.com", "linkedin.com"],
        "amazon": ["amazon.com", "amazon.jobs", "aws.com"],
        "apple": ["apple.com"],
        "meta": ["meta.com", "facebook.com", "instagram.com"],
        "netflix": ["netflix.com"],
        "ibm": ["ibm.com"],
        "cisco": ["cisco.com"],
        "oracle": ["oracle.com"],
        "adobe": ["adobe.com"],
        "salesforce": ["salesforce.com"],
        "tata": ["tcs.com", "tatamotors.com", "tata.com"],
        "infosys": ["infosys.com"],
        "wipro": ["wipro.com"],
        "accenture": ["accenture.com"],
        "deloitte": ["deloitte.com"],
        "tesla": ["tesla.com"],
        "walmart": ["walmart.com", "walmartcareers.com"]
    }

    @classmethod
    def extract_email_domain(cls, email: Optional[str]) -> Optional[str]:
        if not email or "@" not in email:
            return None
        parts = email.strip().split("@")
        return parts[-1].lower() if len(parts) > 1 else None

    @classmethod
    def extract_url_domain(cls, url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url
        try:
            parsed = urlparse(clean_url)
            host = (parsed.hostname or "").lower()
            # Remove 'www.' prefix
            if host.startswith("www."):
                host = host[4:]
            return host
        except Exception:
            return None

    @classmethod
    def evaluate(
        cls,
        company_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        company_website: Optional[str] = None,
        full_text: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates company identity authenticity.
        Outputs:
            - status: "Verified" | "Suspicious" | "Unknown" | "Unable to verify"
            - risk_score: 0 to 100
            - reasons: list of detected anomalies or verification points
        """
        # If email not passed, look for email in text
        if not contact_email and full_text:
            email_match = re.search(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", full_text)
            if email_match:
                contact_email = email_match.group(0)

        email_domain = cls.extract_email_domain(contact_email)
        website_domain = cls.extract_url_domain(company_website)
        
        comp_clean = (company_name or "").strip()
        comp_root = re.sub(r"[^a-zA-Z0-9]", "", comp_clean).lower()

        reasons = []
        risk_score = 0
        status = "Unable to verify"

        # Case 1: Incomplete parameters
        if not comp_clean and not email_domain:
            return {
                "status": "Unable to verify",
                "risk_score": 25,
                "claimed_company": "Not Specified",
                "email_domain": None,
                "website_domain": None,
                "reasons": ["Company name and contact email were not provided. Legitimacy cannot be assessed."]
            }

        # Check against Known Enterprises
        is_known_brand = False
        expected_domains = []
        for brand_key, official_domains in cls.KNOWN_ENTERPRISES.items():
            if brand_key in comp_root:
                is_known_brand = True
                expected_domains = official_domains
                break

        # Check 1: Brand Impersonation via Free Webmail
        if is_known_brand and email_domain in cls.FREE_EMAIL_DOMAINS:
            status = "Suspicious"
            risk_score = 85
            reasons.append(
                f"Severe Impersonation Signal: Claiming to recruit for '{comp_clean}' using a public free webmail address (@{email_domain}). Legitimate enterprises recruit via official corporate domains."
            )

        # Check 2: Brand Impersonation via Lookalike / Unofficial Domain
        elif is_known_brand and email_domain:
            if not any(email_domain == ed or email_domain.endswith("." + ed) for ed in expected_domains):
                status = "Suspicious"
                risk_score = 80
                reasons.append(
                    f"Domain Mismatch: Claiming to represent '{comp_clean}' from unverified domain '@{email_domain}' instead of official domains ({', '.join(expected_domains)})."
                )
            else:
                status = "Verified"
                risk_score = 0
                reasons.append(f"Email domain '@{email_domain}' matches official corporate domain for '{comp_clean}'.")

        # Check 3: Generic company using free webmail
        elif email_domain in cls.FREE_EMAIL_DOMAINS:
            status = "Suspicious"
            risk_score = 45
            reasons.append(
                f"Contact email uses free public webmail (@{email_domain}) rather than an established company domain."
            )

        # Check 4: Website vs Email consistency for unlisted companies
        elif email_domain and website_domain:
            if email_domain == website_domain or email_domain.endswith("." + website_domain):
                status = "Verified"
                risk_score = 5
                reasons.append(f"Contact email domain '@{email_domain}' matches provided website '{website_domain}'.")
            else:
                status = "Suspicious"
                risk_score = 40
                reasons.append(f"Discrepancy between contact email domain (@{email_domain}) and website ({website_domain}).")

        # Case 5: Standard custom domain, unverified external registry
        elif email_domain:
            status = "Unknown"
            risk_score = 15
            reasons.append(f"Email domain '@{email_domain}' is custom but not in enterprise registry. Requires independent verification.")

        else:
            status = "Unable to verify"
            risk_score = 20
            reasons.append("Insufficient employer verification data provided.")

        return {
            "status": status,
            "risk_score": risk_score,
            "claimed_company": comp_clean or "Not Specified",
            "email_domain": email_domain,
            "website_domain": website_domain,
            "reasons": reasons
        }
