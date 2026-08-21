import html
import re
from typing import Any, Dict, List, Optional
import pandas as pd


# Fraud-relevant tokens that must NEVER be removed as stopwords
FRAUD_PRESERVED_TOKENS = {
    "fee", "fees", "deposit", "urgent", "urgently", "guaranteed", "guarantee",
    "bank", "banking", "verification", "verify", "training", "telegram", "whatsapp",
    "wire", "crypto", "bitcoin", "check", "cashier", "reimburse", "reimbursement",
    "otp", "aadhaar", "pan", "upi", "pin", "payment", "pay", "charge", "charges",
    "money", "dollar", "dollars", "daily", "weekly", "bonus", "bonuses",
    "interview", "immediate", "immediately", "start", "today", "no", "never",
    "not", "without", "free", "cash", "credit", "card", "account", "payout",
    "processing", "registration", "equipment", "advance", "clearance"
}

# Standard English stopwords (excluding preserved tokens)
STANDARD_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any",
    "are", "as", "at", "be", "because", "been", "before", "being", "below", "between",
    "both", "but", "by", "did", "do", "does", "doing", "down", "during", "each", "few",
    "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "him", "his", "how", "i", "if", "in", "into", "is", "it", "its", "me", "more", "most",
    "my", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
    "their", "theirs", "them", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when", "where",
    "which", "while", "who", "whom", "why", "with", "you", "your", "yours"
} - FRAUD_PRESERVED_TOKENS


class TextCleaner:
    """Preprocesses raw job posting text while preserving critical fraud indicators."""
    
    _HTML_TAG_RE = re.compile(r"<[^>]+>")
    _URL_RE = re.compile(r"https?://\S+|www\.\S+")
    _EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
    _NON_ALPHANUM_RE = re.compile(r"[^a-zA-Z0-9\s]")
    _WHITESPACE_RE = re.compile(r"\s+")

    @classmethod
    def clean(cls, text: Any, remove_stopwords: bool = True) -> str:
        if pd.isna(text) or text is None:
            return ""
        
        # 1. Unescape HTML entities
        text = html.unescape(str(text))
        
        # 2. Strip HTML tags
        text = cls._HTML_TAG_RE.sub(" ", text)
        
        # 3. Replace URLs and Emails with specific tokens for feature extraction
        text = cls._URL_RE.sub(" url_link ", text)
        text = cls._EMAIL_RE.sub(" contact_email ", text)
        
        # 4. Lowercase
        text = text.lower()
        
        # 5. Clean special characters (keep alphanumeric and spaces)
        text = cls._NON_ALPHANUM_RE.sub(" ", text)
        
        # 6. Normalize whitespace
        tokens = cls._WHITESPACE_RE.split(text.strip())
        
        # 7. Stopword filtering with fraud preservation
        if remove_stopwords:
            tokens = [t for t in tokens if (t in FRAUD_PRESERVED_TOKENS or t not in STANDARD_STOPWORDS) and len(t) > 1]
            
        return " ".join(tokens)


def build_combined_text_series(df: pd.DataFrame) -> pd.Series:
    """
    Combines key job text columns into a single unified text string for each posting.
    Preserves structural context (Title, Profile, Description, Requirements, etc.).
    """
    columns_to_combine = [
        ("title", "Title: "),
        ("company_profile", " Company Profile: "),
        ("description", " Description: "),
        ("requirements", " Requirements: "),
        ("benefits", " Benefits: "),
        ("location", " Location: "),
        ("employment_type", " Employment Type: "),
        ("required_education", " Education: "),
        ("required_experience", " Experience: ")
    ]
    
    combined = pd.Series("", index=df.index, dtype=str)
    for col, prefix in columns_to_combine:
        if col in df.columns:
            cleaned_col = df[col].fillna("").astype(str).apply(lambda x: TextCleaner.clean(x))
            # Only append prefix if content is non-empty
            non_empty_mask = cleaned_col != ""
            combined.loc[non_empty_mask] += prefix + cleaned_col.loc[non_empty_mask]
            
    return combined.str.strip()


def build_combined_text_from_dict(job_dict: Dict[str, Any]) -> str:
    """Builds clean combined text string from a single job dictionary."""
    parts = []
    fields = [
        ("title", "Title: "),
        ("company_profile", " Company Profile: "),
        ("description", " Description: "),
        ("requirements", " Requirements: "),
        ("benefits", " Benefits: "),
        ("location", " Location: "),
        ("employment_type", " Employment Type: "),
        ("required_education", " Education: "),
        ("required_experience", " Experience: ")
    ]
    for key, prefix in fields:
        val = job_dict.get(key, "")
        if val and not pd.isna(val):
            cleaned = TextCleaner.clean(val)
            if cleaned:
                parts.append(f"{prefix}{cleaned}")
                
    return " ".join(parts).strip()
