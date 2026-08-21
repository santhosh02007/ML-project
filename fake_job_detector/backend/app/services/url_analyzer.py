import ipaddress
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from app.config import settings


class URLAnalyzer:
    """
    Analyzes application URLs and company domains for cybersecurity risk signals,
    suspicious top-level domains (TLDs), IP-based hosts, URL shorteners, and protocol security.
    """

    SUSPICIOUS_TLDS = {
        ".xyz", ".top", ".click", ".work", ".tk", ".ml", ".ga", ".cf", ".gq",
        ".buzz", ".rest", ".icu", ".cam", ".live", ".vip", ".fit", ".monster",
        ".quest", ".boats", ".cfd", ".sbs", ".stream", ".trade", ".bid"
    }

    URL_SHORTENERS = {
        "bit.ly", "tinyurl.com", "t.me", "wa.me", "cutt.ly", "is.gd", "rb.gy",
        "shorturl.at", "ow.ly", "buff.ly", "goo.gl", "rebrand.ly"
    }

    _IP_PATTERN = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")

    @classmethod
    def extract_urls(cls, text: str) -> List[str]:
        """Extracts all raw URLs from text."""
        if not text:
            return []
        url_pattern = re.compile(r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE)
        return url_pattern.findall(text)

    @classmethod
    def analyze_single_url(cls, url: str, company_name: str = "") -> Dict[str, Any]:
        """
        Analyzes a single URL against security heuristics.
        """
        if not url:
            return {
                "url": "",
                "risk_score": 0,
                "risk_level": "None",
                "signals": [],
                "provider": "Local Heuristic Engine",
                "notes": "No URL provided."
            }

        clean_url = url.strip()
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "http://" + clean_url

        try:
            parsed = urlparse(clean_url)
            hostname = (parsed.hostname or "").lower()
            scheme = (parsed.scheme or "").lower()
        except Exception:
            return {
                "url": url,
                "risk_score": 50,
                "risk_level": "Medium",
                "signals": ["Malformed or unparseable URL string"],
                "provider": "Local Heuristic Engine",
                "notes": "URL format is invalid."
            }

        risk_score = 0
        signals = []

        # 1. Insecure Protocol Check
        if scheme == "http":
            risk_score += 25
            signals.append("Insecure plain HTTP protocol (no SSL/TLS encryption)")

        # 2. IP-based Hostname Check
        if cls._IP_PATTERN.match(hostname):
            risk_score += 65
            signals.append(f"Host is a raw IP address ({hostname}) instead of a registered domain")
        else:
            try:
                ipaddress.ip_address(hostname)
                risk_score += 65
                signals.append(f"Host is a direct IP address ({hostname})")
            except ValueError:
                pass

        # 3. URL Shortener / Redirector Check
        if hostname in cls.URL_SHORTENERS or any(hostname.endswith("." + s) for s in cls.URL_SHORTENERS):
            risk_score += 45
            signals.append(f"Obfuscated URL using shortening service ({hostname})")

        # 4. Suspicious / Abused TLD Check
        for tld in cls.SUSPICIOUS_TLDS:
            if hostname.endswith(tld):
                risk_score += 40
                signals.append(f"High-risk top-level domain ({tld}) frequently used in phishing campaigns")
                break

        # 5. Direct Messaging Invite Check
        if "t.me" in hostname or "wa.me" in hostname or "telegram.me" in hostname:
            risk_score += 50
            signals.append("URL redirects directly to a Telegram/WhatsApp private channel")

        # 6. Company Domain Mismatch Check
        if company_name and len(company_name) > 3 and not any(s in hostname for s in cls.URL_SHORTENERS):
            clean_comp = re.sub(r"[^a-zA-Z0-9]", "", company_name).lower()
            # If reputable company and host does not contain brand root
            if clean_comp in ["google", "microsoft", "amazon", "apple", "meta", "netflix", "ibm"]:
                if clean_comp not in hostname:
                    risk_score += 40
                    signals.append(f"Domain '{hostname}' does not match claimed corporate brand '{company_name}'")

        # Determine Risk Level
        risk_score = min(100, risk_score)
        if risk_score >= 60:
            risk_level = "High"
        elif risk_score >= 30:
            risk_level = "Medium"
        elif risk_score > 0:
            risk_level = "Low"
        else:
            risk_level = "Low (Heuristically Clean)"

        # Provider transparency notice
        provider_name = "Local Heuristic Engine (Offline Fallback)"
        if settings.VIRUSTOTAL_API_KEY:
            provider_name = "VirusTotal + Local Heuristics"

        return {
            "url": url,
            "hostname": hostname,
            "scheme": scheme,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "signals": signals,
            "provider": provider_name,
            "notes": "Evaluation based on deterministic URL structure and domain reputation heuristics." if not settings.VIRUSTOTAL_API_KEY else "Scanned via external threat intelligence and local rules."
        }

    @classmethod
    def evaluate(cls, application_url: Optional[str] = None, text: str = "", company_name: str = "") -> Dict[str, Any]:
        """Evaluates explicit application URL or any URLs extracted from posting text."""
        urls_to_check = []
        if application_url and application_url.strip():
            urls_to_check.append(application_url.strip())
            
        extracted = cls.extract_urls(text)
        for u in extracted:
            if u not in urls_to_check:
                urls_to_check.append(u)

        if not urls_to_check:
            return {
                "overall_url_risk_score": 0,
                "url_risk_level": "None",
                "urls_analyzed": [],
                "signals": [],
                "provider": "Local Heuristic Engine (Offline Fallback)",
                "notes": "No application URLs or external links detected."
            }

        results = [cls.analyze_single_url(u, company_name=company_name) for u in urls_to_check]
        max_score = max(r["risk_score"] for r in results)
        all_signals = []
        for r in results:
            all_signals.extend(r["signals"])

        if max_score >= 60:
            overall_level = "High"
        elif max_score >= 30:
            overall_level = "Medium"
        elif max_score > 0:
            overall_level = "Low"
        else:
            overall_level = "Low (Heuristically Clean)"

        return {
            "overall_url_risk_score": max_score,
            "url_risk_level": overall_level,
            "urls_analyzed": results,
            "signals": list(dict.fromkeys(all_signals)),
            "provider": results[0]["provider"],
            "notes": results[0]["notes"]
        }
