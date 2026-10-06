import re
from typing import Any, Dict


class SecuritySanitizer:
    """
    Sanitizes and masks sensitive PII (Aadhaar, PAN, Bank details, OTPs, Card numbers)
    from stored text where patterns match. This is partial redaction, not a privacy guarantee.
    """

    # Aadhaar: 12 digits (with spaces or hyphens)
    _AADHAAR_RE = re.compile(r"\b[2-9]{1}[0-9]{3}[\s\-]?[0-9]{4}[\s\-]?[0-9]{4}\b")
    # PAN: 5 letters, 4 digits, 1 letter
    _PAN_RE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b", re.IGNORECASE)
    # Credit/Debit Card: 16 digits
    _CARD_RE = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    # OTP: 4-6 digits near keyword OTP
    _OTP_RE = re.compile(r"\b(?:otp|one\s*time\s*password|verification\s*code)\s*[:=-]?\s*([0-9]{4,6})\b", re.IGNORECASE)
    # UPI PIN / Netbanking password
    _PIN_RE = re.compile(r"\b(?:pin|upi\s*pin|password|passcode)(?:\s*[:=-]\s*([A-Za-z0-9@#$%^&*]{4,16})\b|\s+([0-9]{4,8})\b)", re.IGNORECASE)

    @classmethod
    def mask_pii(cls, text: str) -> str:
        """Masks detected PII in text strings."""
        if not text or not isinstance(text, str):
            return text

        # 1. Mask Cards
        text = cls._CARD_RE.sub("[REDACTED_CARD_NUMBER]", text)
        # 2. Mask Aadhaar
        text = cls._AADHAAR_RE.sub("[REDACTED_AADHAAR]", text)
        # 3. Mask PAN
        text = cls._PAN_RE.sub("[REDACTED_PAN]", text)
        # 4. Mask OTP
        text = cls._OTP_RE.sub(r"OTP: [REDACTED_OTP]", text)
        # 5. Mask PIN / Passwords
        text = cls._PIN_RE.sub(r"PIN/Password: [REDACTED_SECRET]", text)

        return text

    @classmethod
    def sanitize_job_dict(cls, job_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Returns a copy of the job dictionary with all text fields sanitized for PII."""
        sanitized = {}
        for k, v in job_dict.items():
            if isinstance(v, str):
                sanitized[k] = cls.mask_pii(v)
            else:
                sanitized[k] = v
        return sanitized
