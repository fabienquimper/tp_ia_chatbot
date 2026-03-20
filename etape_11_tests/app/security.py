import re, html
from fastapi import HTTPException

INJECTION_PATTERNS = [
    r"ignore\s+(tes|les|toutes?\s+les?|previous|all)\s+(instructions?|directives?|consignes?)",
    r"oublie\s+(tes|les|toutes?\s+les?)\s+(instructions?|directives?|consignes?)",
    r"system\s*prompt",
    r"act\s+as\s+(root|admin|superuser)",
    r"jailbreak",
    r"révèle\s+(le|ton|tes)\s+(prompt|instructions?|system)",
    r"<\s*script",
    r"javascript\s*:",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]

def sanitize(text: str) -> str:
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Message vide")
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail="Message trop long")
    sanitized = html.escape(text.strip())
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text) or pattern.search(sanitized):
            raise HTTPException(status_code=403, detail="Injection détectée")
    return sanitized
