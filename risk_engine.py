import re
from urllib.parse import urlparse

HIGH_RISK_PATTERNS = {
    "Upfront payment requested": [r"pay (?:a|an|the)? ?fee", r"registration fee", r"deposit(?:\s+(?:money|funds))?\s*\$?\d*", r"pay to start", r"top ?up"],
    "Cryptocurrency mentioned": [r"\bbitcoin\b", r"\beth\b", r"\busdt\b", r"\bcrypto(?:currency)?\b", r"wallet address"],
    "Money transfer requested": [r"bank transfer", r"wire transfer", r"send money", r"transfer funds"],
    "Sensitive identity request": [r"passport", r"driver'?s licence", r"bank account details", r"tax file number", r"\btfn\b"],
}

MEDIUM_RISK_PATTERNS = {
    "Moved to private messaging app": [r"whatsapp", r"telegram", r"signal"],
    "Urgency / pressure language": [r"act now", r"limited positions", r"immediate start", r"respond within", r"urgent hiring"],
    "Unrealistic income claim": [r"easy money", r"guaranteed income", r"earn \$?\d{3,}.*(?:day|week)", r"work only \d+.*hours"],
    "No formal hiring process": [r"no interview", r"instant hire", r"hired immediately"],
    "Generic recruiter language": [r"dear candidate", r"dear applicant", r"selected randomly"],
}

LOW_RISK_PATTERNS = {
    "Formal application process mentioned": [r"interview", r"application portal", r"careers page", r"selection process"],
}

FREE_EMAIL_DOMAINS = {"gmail.com", "outlook.com", "hotmail.com", "yahoo.com", "proton.me", "protonmail.com", "icloud.com"}


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_emails(text: str):
    return re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)


def extract_urls(text: str):
    urls = re.findall(r"https?://[^\s)\]>]+", text)
    return [u.rstrip('.,;') for u in urls]


def domain_from_email(email: str):
    return email.split("@", 1)[1].lower() if "@" in email else ""


def domain_from_url(url: str):
    try:
        host = urlparse(url).netloc.lower().split(":")[0]
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def check_patterns(text: str, mapping: dict):
    hits = []
    for label, patterns in mapping.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.I):
                hits.append(label)
                break
    return hits


def analyse(text: str, claimed_company_domain: str = ""):
    t = normalise(text)
    high = check_patterns(t, HIGH_RISK_PATTERNS)
    medium = check_patterns(t, MEDIUM_RISK_PATTERNS)
    low = check_patterns(t, LOW_RISK_PATTERNS)

    emails = extract_emails(text)
    urls = extract_urls(text)
    signals = []
    score = 0

    for item in high:
        signals.append(("high", item))
        score += 22
    for item in medium:
        signals.append(("medium", item))
        score += 11

    if emails:
        free_emails = [e for e in emails if domain_from_email(e) in FREE_EMAIL_DOMAINS]
        if free_emails:
            signals.append(("medium", "Recruiter uses a free email provider"))
            score += 10

    if claimed_company_domain:
        expected = claimed_company_domain.lower().replace("https://", "").replace("http://", "").strip("/")
        expected = expected[4:] if expected.startswith("www.") else expected
        mismatches = []
        for e in emails:
            d = domain_from_email(e)
            if d and d not in FREE_EMAIL_DOMAINS and d != expected and not d.endswith("." + expected):
                mismatches.append(d)
        for u in urls:
            d = domain_from_url(u)
            if d and d != expected and not d.endswith("." + expected):
                mismatches.append(d)
        if mismatches:
            signals.append(("high", f"Domain mismatch detected: {', '.join(sorted(set(mismatches)))}"))
            score += 25

    if "Formal application process mentioned" in low:
        score -= 7
    if emails and all(domain_from_email(e) not in FREE_EMAIL_DOMAINS for e in emails):
        score -= 4

    score = max(0, min(100, score))
    level = "High" if score >= 70 else "Medium" if score >= 35 else "Low"

    return {"score": score, "level": level, "signals": signals, "emails": emails, "urls": urls}
