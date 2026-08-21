import re
from typing import Any, Dict, Optional, Tuple


class SalaryAnalyzer:
    """
    Extracts and normalizes salary specifications, comparing them against role/experience
    benchmarks to detect compensation anomalies commonly seen in recruitment fraud.
    """

    # Hourly regex: $30/hr, $35 - $50 per hour, $40/hour
    _HOURLY_RE = re.compile(r"\$?\s*([0-9]{1,3})\s*(?:-|to)\s*\$?([0-9]{1,3})\s*(?:\/|\s*per\s*)(?:hr|hour|h)\b", re.IGNORECASE)
    _HOURLY_SINGLE_RE = re.compile(r"\$?\s*([0-9]{1,3})\s*(?:\/|\s*per\s*)(?:hr|hour|h)\b", re.IGNORECASE)

    # Weekly regex: $1000 - $2000 weekly, $1500/week
    _WEEKLY_RE = re.compile(r"\$?\s*([0-9]{1,5})\s*(?:-|to)\s*\$?([0-9]{1,5})\s*(?:\/|\s*per\s*)(?:wk|week)\b", re.IGNORECASE)
    _WEEKLY_SINGLE_RE = re.compile(r"\$?\s*([0-9]{1,5})\s*(?:\/|\s*per\s*)(?:wk|week)\b", re.IGNORECASE)

    # Daily regex: $300 - $500 daily, $400/day
    _DAILY_RE = re.compile(r"\$?\s*([0-9]{1,4})\s*(?:-|to)\s*\$?([0-9]{1,4})\s*(?:\/|\s*per\s*)(?:day|daily)\b", re.IGNORECASE)

    # Annual K format: $60k - $80k, 60k-80k, $120k/yr
    _ANNUAL_K_RE = re.compile(r"\$?\s*([0-9]{2,3})\s*k\s*(?:-|to)\s*\$?\s*([0-9]{2,3})\s*k", re.IGNORECASE)
    _ANNUAL_K_SINGLE_RE = re.compile(r"\$?\s*([0-9]{2,3})\s*k\s*(?:\/|\s*per\s*)?(?:yr|year|annum)?\b", re.IGNORECASE)

    # Annual full numbers: $60000 - $80000, 60,000-80,000
    _ANNUAL_FULL_RE = re.compile(r"\$?\s*([0-9]{2,3}),?([0-9]{3})\s*(?:-|to)\s*\$?\s*([0-9]{2,3}),?([0-9]{3})", re.IGNORECASE)

    # Entry-level / low-skill title patterns
    _LOW_SKILL_TITLES = re.compile(r"\b(data\s+entry|clerk|typist|receptionist|virtual\s+assistant|mystery\s+shopper|survey|packaging|shipping\s+agent|customer\s+service|assistant)\b", re.IGNORECASE)

    @classmethod
    def parse_salary_range(cls, text_or_range: str) -> Tuple[Optional[float], Optional[float], str]:
        """
        Parses raw text or salary string and returns annualized minimum and maximum USD equivalents.
        """
        if not text_or_range or str(text_or_range).lower() in ["not disclosed", "none", "nan", ""]:
            return None, None, "Undisclosed"

        s = str(text_or_range).strip()

        # 1. Hourly check ($35-$50/hr)
        m = cls._HOURLY_RE.search(s)
        if m:
            low, high = float(m.group(1)), float(m.group(2))
            return low * 2000, high * 2000, f"${low}-${high}/hr"

        m = cls._HOURLY_SINGLE_RE.search(s)
        if m:
            val = float(m.group(1))
            return val * 2000, val * 2000, f"${val}/hr"

        # 2. Daily check ($300-$500/day)
        m = cls._DAILY_RE.search(s)
        if m:
            low, high = float(m.group(1)), float(m.group(2))
            return low * 250, high * 250, f"${low}-${high}/day"

        # 3. Weekly check ($1000-$2000/wk)
        m = cls._WEEKLY_RE.search(s)
        if m:
            low, high = float(m.group(1)), float(m.group(2))
            return low * 50, high * 50, f"${low}-${high}/wk"

        m = cls._WEEKLY_SINGLE_RE.search(s)
        if m:
            val = float(m.group(1))
            return val * 50, val * 50, f"${val}/wk"

        # 4. Annual K ($60k-$80k)
        m = cls._ANNUAL_K_RE.search(s)
        if m:
            low, high = float(m.group(1)) * 1000, float(m.group(2)) * 1000
            return low, high, f"${int(low/1000)}k-${int(high/1000)}k"

        m = cls._ANNUAL_K_SINGLE_RE.search(s)
        if m:
            val = float(m.group(1)) * 1000
            return val, val, f"${int(val/1000)}k"

        # 5. Annual Full ($60,000 - $80,000)
        m = cls._ANNUAL_FULL_RE.search(s)
        if m:
            low = float(m.group(1) + m.group(2))
            high = float(m.group(3) + m.group(4))
            return low, high, f"${int(low):,}-${int(high):,}"

        return None, None, s

    @classmethod
    def evaluate(
        cls,
        salary_str: Optional[str] = None,
        job_title: str = "",
        experience_level: str = "",
        full_text: str = ""
    ) -> Dict[str, Any]:
        """
        Evaluates whether the specified or extracted salary represents an unrealistic anomaly.
        """
        # Try parsing explicit salary_str first, then check full_text
        min_usd, max_usd, display_str = cls.parse_salary_range(salary_str)
        if min_usd is None and full_text:
            min_usd, max_usd, display_str = cls.parse_salary_range(full_text)

        if min_usd is None or max_usd is None:
            return {
                "anomaly_level": "Low",
                "risk_score": 0,
                "extracted_salary": "Not Disclosed / Standard",
                "annualized_range_usd": None,
                "reason": "Salary is undisclosed or follows standard industry reporting."
            }

        avg_annual_usd = (min_usd + max_usd) / 2.0
        is_low_skill = bool(cls._LOW_SKILL_TITLES.search(job_title) or cls._LOW_SKILL_TITLES.search(full_text))
        is_entry = "entry" in experience_level.lower() or "no experience" in full_text.lower() or "0" in experience_level

        risk_score = 0
        anomaly_level = "Low"
        reason = "Salary is within standard market distribution for this role."

        # Flag 1: Low-skill / Data Entry / Typist claiming >$80,000/yr or >$40/hr
        if is_low_skill and avg_annual_usd > 80000:
            anomaly_level = "High"
            risk_score = 75
            reason = f"Extremely inflated compensation ({display_str}, approx ${int(avg_annual_usd):,}/yr) for an entry-level / routine role ({job_title or 'Data Entry'}). Classic scam indicator."

        # Flag 2: Entry-level with zero experience claiming >$120,000/yr
        elif is_entry and avg_annual_usd > 120000:
            anomaly_level = "High"
            risk_score = 70
            reason = f"Unrealistic salary ({display_str}) offered for a zero-experience or entry-level position."

        # Flag 3: Very high daily payout ($500+/day or $2500+/wk for generic work)
        elif avg_annual_usd > 150000 and ("work from home" in full_text.lower() or "typing" in full_text.lower()):
            anomaly_level = "High"
            risk_score = 80
            reason = f"Exorbitant work-from-home compensation ({display_str}) advertised."

        # Flag 4: Moderately high
        elif is_low_skill and avg_annual_usd > 55000:
            anomaly_level = "Medium"
            risk_score = 35
            reason = f"Salary ({display_str}) is higher than standard median for this position; warrants scrutiny."

        return {
            "anomaly_level": anomaly_level,
            "risk_score": risk_score,
            "extracted_salary": display_str,
            "annualized_range_usd": f"${int(min_usd):,} - ${int(max_usd):,}",
            "reason": reason
        }
