from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app.database import get_supabase
from app.dependencies import get_current_user
from app.security import encrypt_api_key
from app.schemas import AgentCreate, AgentUpdate, AgentResponse, ProviderPreset
from app.llm.providers import PROVIDER_PRESETS

router = APIRouter(tags=["agents"])


@router.get("/providers/presets", response_model=List[ProviderPreset])
async def list_provider_presets():
    """
    Frontend (Flutter) uchun qulay tayyor provayderlar ro'yxati (dropdown uchun).
    Bu FAQAT tavsiya — 'custom' tanlansa, foydalanuvchi o'zi istalgan provayderning
    base_url'ini kiritishi mumkin. Backend hech qanday provayderni cheklamaydi.
    """
    return PROVIDER_PRESETS


@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(user: dict = Depends(get_current_user)):
    sb = get_supabase()
    res = sb.table("agents").select("*").eq("user_id", user["id"]).execute()
    return res.data


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(payload: AgentCreate, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    data = payload.model_dump()
    data["api_key"] = encrypt_api_key(data["api_key"])
    data["user_id"] = user["id"]
    res = sb.table("agents").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Agent yaratilmadi")
    return res.data[0]


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    res = sb.table("agents").select("*").eq("id", str(agent_id)).eq("user_id", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Agent topilmadi")
    return res.data[0]


@router.patch("/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: UUID, payload: AgentUpdate, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    existing = sb.table("agents").select("id").eq("id", str(agent_id)).eq("user_id", user["id"]).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Agent topilmadi")

    data = {k: v for k, v in payload.model_dump(exclude_unset=True).items()}
    if data.get("api_key"):
        data["api_key"] = encrypt_api_key(data["api_key"])

    res = sb.table("agents").update(data).eq("id", str(agent_id)).eq("user_id", user["id"]).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Agent yangilanmadi")
    return res.data[0]


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: UUID, user: dict = Depends(get_current_user)):
    sb = get_supabase()
    sb.table("agents").delete().eq("id", str(agent_id)).eq("user_id", user["id"]).execute()
    return None
