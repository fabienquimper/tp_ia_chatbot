"""
Étape 09 — Sécurité
Rate limiting, prompt injection guard, sanitization, JWT.
"""
import os, re, html
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from jose import JWTError, jwt
from passlib.context import CryptContext

# ── Configuration ─────────────────────────────────────────────────────────
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# ── Rate Limiter ───────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# ── Password Hashing ───────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utilisateurs de démo (en prod : utiliser une vraie base de données)
DEMO_USERS = {
    "alice": pwd_context.hash("password123"),
    "bob": pwd_context.hash("secret456"),
    "admin": pwd_context.hash("admin789"),
}

# ── OAuth2 ─────────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# ── Prompt Injection Patterns ──────────────────────────────────────────────
INJECTION_PATTERNS = [
    r"ignore\s+(tes|les|toutes?\s+les?|previous|all)\s+(instructions?|directives?|consignes?)",
    r"oublie\s+(tes|les|toutes?\s+les?)\s+(instructions?|directives?|consignes?)",
    r"system\s*prompt",
    r"act\s+as\s+(root|admin|superuser|system|god)",
    r"tu\s+es\s+(maintenant|désormais)\s+(un[e]?\s+)?(?:autre|nouveau|méchant|evil)",
    r"DAN\s*mode",
    r"jailbreak",
    r"révèle\s+(le|ton|tes)\s+(prompt|instructions?|system)",
    r"pretend\s+you\s+(are|have\s+no)",
    r"roleplay\s+as",
    r"<\s*script",  # XSS
    r"javascript\s*:",
    r"on\w+\s*=",  # HTML event handlers
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]

def sanitize(text: str) -> str:
    """
    Nettoie et valide le texte de l'utilisateur.
    - Échappe les caractères HTML
    - Détecte les tentatives d'injection de prompt
    - Lève HTTPException 403 si injection détectée
    """
    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="Message vide non autorisé")

    # Limite de longueur
    if len(text) > 2000:
        raise HTTPException(status_code=400, detail="Message trop long (max 2000 caractères)")

    # Échappement HTML (prévention XSS)
    sanitized = html.escape(text.strip())

    # Détection d'injection de prompt
    for pattern in COMPILED_PATTERNS:
        if pattern.search(sanitized) or pattern.search(text):
            raise HTTPException(
                status_code=403,
                detail="Requête refusée : tentative d'injection de prompt détectée"
            )

    return sanitized

# ── JWT ────────────────────────────────────────────────────────────────────

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(username: str, password: str) -> Optional[str]:
    """Retourne le username si authentifié, None sinon."""
    if username not in DEMO_USERS:
        return None
    if not verify_password(password, DEMO_USERS[username]):
        return None
    return username

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un JWT signé."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> str:
    """Vérifie un JWT et retourne le username. Lève HTTPException si invalide."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    return verify_token(token)
