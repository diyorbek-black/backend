from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from uuid import UUID
from datetime import datetime

AgentRole = Literal["Executor", "Critic", "Architect", "Creative", "Guardian"]

# Protocol — HTTP so'rov formati. Deyarli barcha zamonaviy LLM provayderlari
# ("openai_compatible") yoki Anthropic Claude formatini qo'llaydi. Shu ikkitasi
# orqali cheksiz sonli provayder qo'llab-quvvatlanadi — kodni o'zgartirish shart emas.
Protocol = Literal["openai_compatible", "anthropic"]


class AgentCreate(BaseModel):
    name: str
    role: AgentRole
    sprite_id: str
    provider_label: str = Field(..., description="Ko'rinadigan nom, masalan: 'Groq', 'OpenRouter', 'DeepSeek', 'Mening lokal Ollama'")
    protocol: Protocol = Field(default="openai_compatible", description="So'rov formati: openai_compatible yoki anthropic")
    base_url: str = Field(..., description="Provayderning API manzili, masalan https://api.groq.com/openai/v1")
    api_key: str = Field(..., description="Ochiq (shifrlanmagan) kalit — backend uni avtomatik shifrlaydi")
    model: str = Field(..., description="Model nomi, masalan 'llama-3.3-70b-versatile', 'gpt-4o-mini', 'claude-sonnet-4-6'")
    system_prompt: str
    behavior: str = "active_patrol"


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[AgentRole] = None
    sprite_id: Optional[str] = None
    provider_label: Optional[str] = None
    protocol: Optional[Protocol] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    behavior: Optional[str] = None


class AgentResponse(BaseModel):
    id: UUID
    name: str
    role: AgentRole
    sprite_id: str
    provider_label: str
    protocol: Protocol
    base_url: str
    model: str
    system_prompt: str
    behavior: str
    created_at: datetime
    # Diqqat: api_key qasddan qaytarilmaydi — xavfsizlik uchun


class ProviderPreset(BaseModel):
    key: str
    label: str
    protocol: Protocol
    base_url: Optional[str] = None  # None bo'lsa — foydalanuvchi o'zi kiritadi (custom)


class ChatRequest(BaseModel):
    message: str
    agent_ids: Optional[List[UUID]] = None  # bo'sh bo'lsa, foydalanuvchining barcha agentlari ishtirok etadi


class AgentContribution(BaseModel):
    agent_name: str
    role: str
    text: str


class ChatResponse(BaseModel):
    final_output: str
    contributions: List[AgentContribution]
    critique: Optional[str] = None
