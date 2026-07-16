import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")

    @property
    def allowed_origins_list(self) -> List[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


settings = Settings()

_REQUIRED_VARS = ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_JWT_SECRET", "ENCRYPTION_KEY"]


def validate_settings() -> None:
    """Server ishga tushishidan oldin barcha kerakli secret'lar borligini tekshiradi."""
    missing = [v for v in _REQUIRED_VARS if not getattr(settings, v)]
    if missing:
        raise RuntimeError(
            "Quyidagi environment variable'lar (Secrets) topilmadi: "
            + ", ".join(missing)
            + ". Iltimos ularni .env fayliga yoki platformangizning Secrets "
            "panelига qo'shing (.env.example fayliga qarang)."
        )
