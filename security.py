from jose import jwt, JWTError
from fastapi import HTTPException, status
from cryptography.fernet import Fernet, InvalidToken
from app.config import settings

ALGORITHM = "HS256"


def decode_supabase_jwt(token: str) -> dict:
    """Supabase Auth tomonidan berilgan JWT tokenni tekshiradi va payload'ni qaytaradi."""
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            audience="authenticated",
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati o'tgan",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _get_fernet() -> Fernet:
    try:
        return Fernet(settings.ENCRYPTION_KEY.encode())
    except Exception:
        raise RuntimeError(
            "ENCRYPTION_KEY noto'g'ri formatda. U 32-byte, base64 (Fernet) "
            "formatidagi kalit bo'lishi kerak. Yaratish uchun: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )


def encrypt_api_key(raw_key: str) -> str:
    """Agentning LLM provider API kalitini bazaga saqlashdan oldin shifrlaydi."""
    return _get_fernet().encrypt(raw_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Bazadan olingan shifrlangan API kalitni LLM'ga so'rov yuborish uchun deshifrlaydi."""
    try:
        return _get_fernet().decrypt(encrypted_key.encode()).decode()
    except InvalidToken:
        raise HTTPException(status_code=500, detail="Agent API kalitini deshifrlab bo'lmadi")
