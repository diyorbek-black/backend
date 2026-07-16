from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.security import decode_supabase_jwt

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Flutter client Supabase Google Sign-In orqali olingan `access_token`ni
    Authorization: Bearer <token> header'ida yuboradi. Bu funksiya tokenni
    tekshiradi va foydalanuvchi ma'lumotlarini qaytaradi.
    """
    token = credentials.credentials
    payload = decode_supabase_jwt(token)
    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ichida foydalanuvchi ID (sub) topilmadi",
        )
    return {"id": user_id, "email": email}
