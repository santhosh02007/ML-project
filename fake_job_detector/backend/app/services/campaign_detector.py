from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.ml.preprocessor import TextCleaner


class CampaignDetector:
    """
    Detects recurring scam campaigns across different job titles or postings
    using TF-IDF cosine similarity clustering.
    """

    _instance: Optional["CampaignDetector"] = None

    # Curated known recurring scam template campaigns
    KNOWN_SCAM_CAMPAIGNS = [
        {
            "campaign_id": "SCAM_CAMP_001",
            "campaign_name": "Check Cashing / Overpayment Wire Transfer Campaign",
            "text": "Quality assurance mystery shopper package handler. Receive check via cashier wire, deposit into personal bank account, keep commission and wire remaining funds via Bitcoin or Western Union.",
            "threat_level": "High Risk"
        },
        {
            "campaign_id": "SCAM_CAMP_002",
            "campaign_name": "Telegram / WhatsApp Direct Payout Typing Scam",
            "text": "Virtual assistant data entry typing specialist. No experience needed daily payout 3000 rupees. Must contact recruiter on Telegram or WhatsApp for immediate hiring without interview.",
            "threat_level": "High Risk"
        },
        {
            "campaign_id": "SCAM_CAMP_003",
            "campaign_name": "Upfront Laptop & Training Security Deposit Scam",
            "text": "Mandatory refundable security deposit for home office equipment laptop and training materials. Pay registration fee before starting work.",
            "threat_level": "High Risk"
        },
        {
            "campaign_id": "SCAM_CAMP_004",
            "campaign_name": "Phishing OTP / Banking Verification Campaign",
            "text": "Urgent recruitment candidate verification. Submit bank account number, net banking credentials, Aadhaar copy and OTP to complete background screening.",
            "threat_level": "High Risk"
        }
    ]

    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
        self.campaign_texts = [c["text"] for c in self.KNOWN_SCAM_CAMPAIGNS]
        self.campaign_metadata = self.KNOWN_SCAM_CAMPAIGNS
        self.campaign_vectors = self.vectorizer.fit_transform([
            TextCleaner.clean(t) for t in self.campaign_texts
        ])

    @classmethod
    def get_instance(cls) -> "CampaignDetector":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def evaluate(self, text: str, threshold: float = 0.70) -> Dict[str, Any]:
        """
        Calculates cosine similarity against known scam campaigns.
        """
        if not text or len(text.strip()) < 15:
            return {
                "campaign_match": False,
                "similarity_score": 0.0,
                "matched_campaign": None,
                "risk_contribution": 0
            }

        cleaned = TextCleaner.clean(text)
        if not cleaned:
            return {
                "campaign_match": False,
                "similarity_score": 0.0,
                "matched_campaign": None,
                "risk_contribution": 0
            }

        query_vec = self.vectorizer.transform([cleaned])
        sims = cosine_similarity(query_vec, self.campaign_vectors)[0]
        max_idx = int(np.argmax(sims))
        max_sim = float(sims[max_idx])

        if max_sim >= threshold:
            matched = self.campaign_metadata[max_idx]
            # Risk contribution scales with similarity
            risk_contrib = int(max_sim * 40)
            return {
                "campaign_match": True,
                "similarity_score": round(max_sim * 100, 1),
                "matched_campaign": {
                    "campaign_id": matched["campaign_id"],
                    "campaign_name": matched["campaign_name"],
                    "threat_level": matched["threat_level"]
                },
                "risk_contribution": risk_contrib,
                "reason": f"Text exhibits {int(max_sim*100)}% structural pattern similarity to known syndicated scam: '{matched['campaign_name']}'."
            }

        return {
            "campaign_match": False,
            "similarity_score": round(max_sim * 100, 1),
            "matched_campaign": None,
            "risk_contribution": 0,
            "reason": "No high-confidence duplicate scam campaign cluster match detected."
        }
