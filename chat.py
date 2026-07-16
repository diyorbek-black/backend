from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from app.database import get_supabase
from app.dependencies import get_current_user
from app.schemas import ChatRequest, ChatResponse, AgentContribution
from app.orchestrator.graph import run_orchestration

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(payload: ChatRequest, user: dict = Depends(get_current_user)):
    sb = get_supabase()

    query = sb.table("agents").select("*").eq("user_id", user["id"])
    if payload.agent_ids:
        query = query.in_("id", [str(i) for i in payload.agent_ids])
    agents_res = query.execute()
    agents = agents_res.data

    if not agents:
        raise HTTPException(
            status_code=400,
            detail="Faol agent topilmadi. Avval kamida bitta agent yarating (/agents).",
        )

    try:
        result = await run_orchestration(agents, payload.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sb.table("chat_history").insert(
        {
            "user_id": user["id"],
            "user_message": payload.message,
            "final_output": result["final_output"] or "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    ).execute()

    return ChatResponse(
        final_output=result["final_output"] or "",
        contributions=[AgentContribution(**p) for p in result["proposals"]],
        critique=result.get("critique_feedback"),
    )
