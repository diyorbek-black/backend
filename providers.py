import httpx
from fastapi import HTTPException

TIMEOUT = httpx.Timeout(60.0)


async def call_openai_compatible(base_url: str, api_key: str, model: str, system_prompt: str, user_message: str) -> str:
    """
    OpenAI /chat/completions formatiga mos KEZ KELGAN provayder uchun ishlaydi:
    OpenAI, Groq, OpenRouter, Together AI, DeepSeek, Mistral, Fireworks,
    Google Gemini (OpenAI-compatible endpoint: /v1beta/openai), lokal Ollama/LM Studio va h.k.
    Foydalanuvchi shunchaki agent yaratishda shu provayderning base_url'ini kiritadi.
    """
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"{base_url} xatosi ({resp.status_code}): {resp.text[:500]}")
    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail=f"{base_url} javobini o'qib bo'lmadi: {data}")


async def call_anthropic(base_url: str, api_key: str, model: str, system_prompt: str, user_message: str) -> str:
    """Anthropic Claude /v1/messages formati (x-api-key header, boshqa provayderlardan farqli)."""
    url = base_url.rstrip("/") + "/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Anthropic API xatosi ({resp.status_code}): {resp.text[:500]}")
    data = resp.json()
    try:
        return data["content"][0]["text"]
    except (KeyError, IndexError):
        raise HTTPException(status_code=502, detail=f"Anthropic javobini o'qib bo'lmadi: {data}")


PROTOCOL_MAP = {
    "openai_compatible": call_openai_compatible,
    "anthropic": call_anthropic,
}


async def call_llm(protocol: str, base_url: str, api_key: str, model: str, system_prompt: str, user_message: str) -> str:
    func = PROTOCOL_MAP.get(protocol)
    if not func:
        raise HTTPException(status_code=400, detail=f"Noma'lum protocol: {protocol} (faqat 'openai_compatible' yoki 'anthropic' bo'lishi mumkin)")
    return await func(base_url, api_key, model, system_prompt, user_message)


# ---------------------------------------------------------------------------
# Qulaylik uchun: frontend'da dropdown ko'rsatish uchun tayyor "presetlar".
# Bu ro'yxat FAQAT tavsiya — foydalanuvchi istalgan boshqa provayderni ham
# "custom" tanlab, o'zining base_url + api_key + model qiymatlarini kiritib
# qo'sha oladi. Backend hech qanday provayderni cheklamaydi.
# ---------------------------------------------------------------------------
PROVIDER_PRESETS = [
    {"key": "openai", "label": "OpenAI", "protocol": "openai_compatible", "base_url": "https://api.openai.com/v1"},
    {"key": "groq", "label": "Groq", "protocol": "openai_compatible", "base_url": "https://api.groq.com/openai/v1"},
    {"key": "openrouter", "label": "OpenRouter", "protocol": "openai_compatible", "base_url": "https://openrouter.ai/api/v1"},
    {"key": "gemini", "label": "Google Gemini", "protocol": "openai_compatible", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai"},
    {"key": "together", "label": "Together AI", "protocol": "openai_compatible", "base_url": "https://api.together.xyz/v1"},
    {"key": "deepseek", "label": "DeepSeek", "protocol": "openai_compatible", "base_url": "https://api.deepseek.com"},
    {"key": "mistral", "label": "Mistral", "protocol": "openai_compatible", "base_url": "https://api.mistral.ai/v1"},
    {"key": "fireworks", "label": "Fireworks AI", "protocol": "openai_compatible", "base_url": "https://api.fireworks.ai/inference/v1"},
    {"key": "anthropic", "label": "Anthropic Claude", "protocol": "anthropic", "base_url": "https://api.anthropic.com/v1"},
    {"key": "ollama_local", "label": "Lokal Ollama", "protocol": "openai_compatible", "base_url": "http://localhost:11434/v1"},
    {"key": "custom", "label": "Boshqa (o'zim kiritaman)", "protocol": "openai_compatible", "base_url": None},
]
