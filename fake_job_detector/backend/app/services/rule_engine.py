import re
from typing import Any, Dict, List, Optional, Tuple


class RuleEngine:
    """
    Context-aware, weighted rule engine for recruitment fraud indicators.
    Includes anti-scam disclaimer negation handling to prevent false positives.
    """

    # 1. Anti-Scam Disclaimer / Negation Context Patterns
    # These phrases indicate the employer is warning candidates against scammers
    _DISCLAIMER_PATTERNS = [
        re.compile(r"\b(never|do not|don't|does not|will not|we do not|we don't)\s+(ever\s+)?(ask|charge|demand|request|require|collect)\s+(for\s+)?(any\s+)?(money|fee|fees|payment|deposit|charge|banking details|bank details)\b", re.IGNORECASE),
        re.compile(r"\b(beware|caution|alert|warning)\s+(of\s+)?(fraudulent|fake|scam|scammers|unauthorized)\b", re.IGNORECASE),
        re.compile(r"\bno\s+(application|registration|recruitment|processing|training)\s+fee(s)?\s+(is\s+)?(required|charged|needed)\b", re.IGNORECASE),
        re.compile(r"\b(free\s+of\s+charge|100%\s+free\s+recruitment|we never solicit funds)\b", re.IGNORECASE),
        re.compile(r"\bwe will never ask you for (money|payments|gift cards|crypto|sensitive information)\b", re.IGNORECASE),
        re.compile(r"\bno payment (is\s+)?required (at any stage|for applying|during recruitment)\b", re.IGNORECASE),
    ]

    # 2. Weighted Scam Trigger Rules
    # Structure: (rule_id, rule_name, category, weight, regex_pattern, explanation)
    RULES = [
        # Upfront Fee / Payment Requests (Weight: 35-45)
        (
            "PAY_001",
            "Registration or Processing Fee Requested",
            "Payment Request",
            40,
            re.compile(r"\b(pay|submit|transfer|send|deposit)\s+(\$?[0-9]+|a\s+small|nominal)?\s*(registration|processing|application|enrolment|training|joining|interview)\s*(fee|charges?|cost|deposit|amount)\b", re.IGNORECASE),
            "The posting asks the applicant to pay a fee before joining or during recruitment."
        ),
        (
            "PAY_002",
            "Security / Equipment Deposit Required",
            "Payment Request",
            35,
            re.compile(r"\b(refundable\s+)?(security\s+deposit|equipment\s+deposit|starter\s+kit\s+payment|laptop\s+deposit|training\s+fee|refundable\s+financial\s+verification)\b", re.IGNORECASE),
            "The posting demands an upfront security deposit or equipment purchase before employment."
        ),
        (
            "PAY_003",
            "Cashier Check / Money Order / Wire Scam",
            "Payment Request",
            45,
            re.compile(r"\b(cashier[\s\-]check|wire\s+transfer|money\s+order|deposit\s+(the\s+)?check|send\s+back\s+excess\s+funds|reimburse\s+via\s+bitcoin|crypto\s+deposit)\b", re.IGNORECASE),
            "Classic check-overpayment or wire transfer scam pattern detected."
        ),
        (
            "PAY_004",
            "Pay Before Joining / Advance Payment",
            "Payment Request",
            38,
            re.compile(r"\b(pay\s+before\s+(joining|starting|interview)|mandatory\s+fee\s+to\s+process|advance\s+payment\s+for\s+materials)\b", re.IGNORECASE),
            "Explicit demand for payment prior to starting work or receiving job offer."
        ),

        # Sensitive Information Requests (Weight: 30-40)
        (
            "PII_001",
            "Banking or Financial Credentials Requested",
            "Sensitive Info",
            40,
            re.compile(r"\b(bank\s+account\s+number|routing\s+number|credit\s+card|debit\s+card|cvv|net\s+banking|upi\s+pin|atm\s+pin)\b", re.IGNORECASE),
            "The posting or interview asks for banking details, card numbers, or PINs upfront."
        ),
        (
            "PII_002",
            "National ID / OTP Solicitation",
            "Sensitive Info",
            35,
            re.compile(r"\b(send\s+(your\s+)?otp|aadhaar\s+card\s+copy|pan\s+card\s+details|social\s+security\s+card\s+photo|ssn\s+number\s+required\s+for\s+interview)\b", re.IGNORECASE),
            "Requests sensitive government identification or OTP verification before an offer."
        ),

        # Guaranteed / Urgent / Unrealistic Language (Weight: 20-30)
        (
            "URG_001",
            "Guaranteed / Unrealistic Daily or Weekly Payouts",
            "Unrealistic Claims",
            25,
            re.compile(r"\b(guaranteed\s+(income|daily\s+payout|earnings)|earn\s+\$[1-9][0-9]{2,}\s*(daily|per\s+day|\/day)|daily\s+wire\s+transfer|easy\s+money\s+online|no\s+skills?\s+earn\s+rich)\b", re.IGNORECASE),
            "Unrealistic income guarantees or excessive daily payout promises."
        ),
        (
            "URG_002",
            "High Pressure Immediate Hiring",
            "Urgency / Pressure",
            20,
            re.compile(r"\b(immediate(ly)?\s+hire|start\s+today\s+without\s+interview|urgent(ly)?\s+hiring\s+no\s+experience\s+needed|limited\s+slots\s+act\s+fast|instant\s+joining\s+letter)\b", re.IGNORECASE),
            "High-pressure recruitment tactics offering immediate employment without evaluation."
        ),

        # Off-Platform / Unofficial Communication (Weight: 25-35)
        (
            "COMM_001",
            "Chat App-Only Interview / Telegram / WhatsApp",
            "Unofficial Channel",
            30,
            re.compile(r"\b(contact\s+(hr|recruiter|manager)\s+on\s+(telegram|whatsapp)|telegram\s+id\s*:\s*@?\w+|interview\s+via\s+telegram|whatsapp\s+interview\s+only|google\s+hangouts\s+interview)\b", re.IGNORECASE),
            "Interviews conducted exclusively through untraceable instant messaging apps."
        ),
        (
            "COMM_002",
            "Free Webmail Recruiter Address",
            "Unofficial Channel",
            20,
            re.compile(r"\b[A-Za-z0-9._%+-]+@(gmail|yahoo|hotmail|outlook|protonmail|mail|aol|yandex)\.com\b", re.IGNORECASE),
            "Contact email uses a free webmail service rather than a corporate domain."
        ),

        # Tamil-English Code-Mixed Recruitment Scam Language (Weight: 25-35)
        (
            "MULTI_001",
            "Code-Mixed / Tamil-English Scam Phrasing",
            "Multilingual Scam",
            30,
            re.compile(r"\b(easy\s+work\s+from\s+home\s+daily\s+[0-9]+\s*(rs|rupees|inr)|daily\s+varum|panam\s+kidaikkum|veettil\s+irundhe\s+sambalam|deposit\s+seiyavum|send\s+otp\s+for\s+job|urgent\s+velai|joining\s+fee\s+kattavum)\b", re.IGNORECASE),
            "Code-mixed multilingual phrasing offering quick home earnings or asking for fees/OTPs."
        )
    ]

    @classmethod
    def check_disclaimers(cls, text: str) -> List[str]:
        """Identifies legitimate anti-scam warnings or disclaimer sentences in text."""
        disclaimers = []
        for pattern in cls._DISCLAIMER_PATTERNS:
            for match in pattern.finditer(text):
                disclaimers.append(match.group(0))
        return disclaimers

    @classmethod
    def evaluate(cls, text: str) -> Dict[str, Any]:
        """
        Evaluates text against weighted domain rules with context awareness.
        Returns:
            - rule_score: aggregated raw rule score (0-100)
            - triggered_rules: list of triggered rule objects
            - matched_snippets: list of highlighted text spans
            - disclaimer_found: bool indicating whether legitimate anti-scam disclaimers were present
        """
        if not text or not isinstance(text, str):
            return {
                "rule_score": 0,
                "triggered_rules": [],
                "matched_snippets": [],
                "disclaimer_found": False,
                "disclaimers": []
            }

        # Check for legitimate disclaimers
        disclaimers = cls.check_disclaimers(text)
        disclaimer_found = len(disclaimers) > 0

        # Break text into sentences to check disclaimer scope
        sentences = re.split(r"[.\n;!]", text)
        
        triggered_rules = []
        matched_snippets = []
        total_weight = 0

        for rule_id, rule_name, category, weight, pattern, explanation in cls.RULES:
            matches = list(pattern.finditer(text))
            if not matches:
                continue

            # Check if any match is negated by being inside a disclaimer sentence
            valid_matches = []
            for m in matches:
                snippet = m.group(0)
                start_pos = max(0, m.start() - 60)
                end_pos = min(len(text), m.end() + 60)
                local_window = text[start_pos:end_pos]
                
                # Check if local window contains a negation/disclaimer
                is_negated = False
                for disc_pat in cls._DISCLAIMER_PATTERNS:
                    if disc_pat.search(local_window):
                        is_negated = True
                        break
                        
                if not is_negated:
                    valid_matches.append(snippet)

            if valid_matches:
                # Deduplicate snippet strings
                unique_snippets = list(dict.fromkeys(valid_matches))[:3]
                matched_snippets.extend(unique_snippets)
                
                triggered_rules.append({
                    "rule_id": rule_id,
                    "rule_name": rule_name,
                    "category": category,
                    "weight": weight,
                    "snippets": unique_snippets,
                    "explanation": explanation
                })
                total_weight += weight

        # Normalize rule score to 0 - 100 range (capped)
        normalized_score = min(100, total_weight)

        return {
            "rule_score": normalized_score,
            "triggered_rules": triggered_rules,
            "matched_snippets": list(dict.fromkeys(matched_snippets)),
            "disclaimer_found": disclaimer_found,
            "disclaimers": disclaimers
        }
