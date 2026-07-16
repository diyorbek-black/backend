from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validate_settings
from app.routers import agents, chat

validate_settings()

app = FastAPI(
    title="Pixel-Agentic AI Orchestrator",
    description="Ko'p-agentli (multi-agent) pixel-art AI orkestratori uchun backend API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=settings.ALLOWED_ORIGINS != "*",  # "*" bilan credentials birga ishlamaydi (brauzer cheklovi)
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(chat.router)


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc: RuntimeError):
    raise HTTPException(status_code=500, detail=str(exc))
