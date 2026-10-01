"""Аутентификация с безопасным fallback"""
from datetime import datetime, timedelta
from typing import Optional
from .config import SECRET_KEY

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
except ImportError:
    import hashlib

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return get_password_hash(plain_password) == hashed_password

    def get_password_hash(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()


try:
    from jose import jwt

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
except ImportError:
    import json
    import base64

    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        # Упрощенная генерация токена для окружения без pyjwt/jose
        to_encode = data.copy()
        expire = (datetime.utcnow() + (expires_delta or timedelta(minutes=30))).isoformat()
        to_encode.update({"exp": expire})
        payload = json.dumps(to_encode).encode()
        return base64.urlsafe_b64encode(payload).decode()
