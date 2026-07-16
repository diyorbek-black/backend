# Pixel-Agentic AI Orchestrator — Backend (FastAPI)

Bu backend sizning ko'p-agentli (multi-agent) pixel-art AI ilovangiz uchun to'liq ishlaydigan API'dir.

## ⭐ Asosiy xususiyat: cheksiz sonli AI provayder

Backend Gemini/Groq/OpenRouter bilan **cheklanmagan**. Agent yaratishda siz istalgan
provayderni ulay olasiz — kod o'zgartirish shart emas. Buning siri: har bir agent
`protocol` + `base_url` orqali aniqlanadi:

| Protocol | Nima uchun | Misollar |
|---|---|---|
| `openai_compatible` | `/chat/completions` formatini qo'llovchi barcha provayderlar | OpenAI, Groq, OpenRouter, Together AI, DeepSeek, Mistral, Fireworks, Google Gemini (OpenAI-compat endpoint), lokal Ollama/LM Studio |
| `anthropic` | Claude'ning o'ziga xos formati | Anthropic Claude API |

`GET /providers/presets` — Flutter frontend uchun tayyor dropdown ro'yxatini qaytaradi
(shu jumladan `"custom"` — foydalanuvchi o'zi istalgan `base_url` kiritishi mumkin).

Yangi provayder qo'shish uchun **backendni o'zgartirish shart emas** — foydalanuvchi
frontend'dan shunchaki:
```json
{
  "provider_label": "Mening yangi provayderim",
  "protocol": "openai_compatible",
  "base_url": "https://api.example.com/v1",
  "api_key": "sk-...",
  "model": "model-nomi"
}
```
kiritib, agent yaratadi.

## Loyiha tuzilishi

```
app/
├── main.py                # FastAPI kirish nuqtasi, CORS, routerlar
├── config.py               # Secrets/env o'zgaruvchilarni o'qish va tekshirish
├── database.py              # Supabase klient (singleton)
├── security.py              # JWT tekshirish + API kalitlarni Fernet bilan shifrlash
├── dependencies.py          # get_current_user (Supabase JWT orqali auth)
├── schemas.py                # Pydantic modellari
├── llm/
│   └── providers.py          # openai_compatible / anthropic protokollari + presetlar
├── orchestrator/
│   └── graph.py               # LangGraph: dinamik ko'p-agentli orkestratsiya
└── routers/
    ├── agents.py               # Agentlar CRUD + /providers/presets
    └── chat.py                  # Orkestratsiya endpointi
sql/
└── schema.sql                  # Supabase jadvallari (profiles, agents, chat_history) + RLS
```

## O'rnatish

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` faylini to'ldiring:

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=...           # service_role kalit (server-side, "sb_secret_..." bilan boshlanadi)
SUPABASE_JWT_SECRET=...    # Supabase Dashboard > Project Settings > API > JWT Secret
ENCRYPTION_KEY=...         # quyida qanday generatsiya qilishni ko'ring
ALLOWED_ORIGINS=*          # yoki "https://sizning-domen.com,https://boshqa-domen.com"
```

### ENCRYPTION_KEY generatsiya qilish

Agentlarning LLM API kalitlari bazada **shifrlangan** holda saqlanadi (Fernet, AES tabiatli
simmetrik shifrlash). Buning uchun 32-baytli maxsus kalit kerak:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Siz so'ragandek, men sizga tayyor kalit generatsiya qilib qo'ydim (buni faqat **o'zingizning**
Secrets panelingizga, masalan Replit/Vercel/Railway'da qo'shing — bu yerda hech qayerda
saqlanmaydi):

```
ENCRYPTION_KEY=kY0mua73E3FoCUQe0j5PmYCL_5A6YA3D1wlCYSd4j9o=
```

> ⚠️ Bu kalit yo'qolsa, bazadagi shifrlangan API kalitlarni deshifrlab bo'lmaydi —
> ehtiyot nusxasini xavfsiz joyda saqlang.

## Supabase sozlash

1. Supabase loyihangizni oching → **SQL Editor**
2. `sql/schema.sql` faylining butun mazmunini nusxalab, run qiling
3. **Authentication → Providers → Google**'ni yoqing (Flutter Google Sign-In uchun)
4. **Project Settings → API**'dan `SUPABASE_URL`, `service_role key` (bu — `SUPABASE_KEY`) va
   `JWT Secret`'ni oling

## Ishga tushirish

```bash
uvicorn app.main:app --reload --port 8000
```

Server ishga tushgach: `http://localhost:8000/docs` — Swagger UI orqali barcha endpointlarni
sinab ko'rishingiz mumkin.

## API endpointlari

| Method | Endpoint | Tavsif |
|---|---|---|
| GET | `/health` | Server holatini tekshirish |
| GET | `/providers/presets` | Tayyor provayder ro'yxati (frontend dropdown uchun) |
| GET | `/agents` | Foydalanuvchining barcha agentlarini olish |
| POST | `/agents` | Yangi agent yaratish (istalgan provayder bilan) |
| GET | `/agents/{id}` | Bitta agentni olish |
| PATCH | `/agents/{id}` | Agentni yangilash |
| DELETE | `/agents/{id}` | Agentni o'chirish |
| POST | `/chat` | Xabar yuborish → barcha (yoki tanlangan) agentlar orkestratsiyasi ishga tushadi |

Barcha endpointlar (health'dan tashqari) `Authorization: Bearer <supabase_access_token>`
header talab qiladi. Flutter tomondan Supabase Google Sign-In'dan keyin olingan
`session.accessToken`'ni shu yerga qo'yasiz.

### `POST /agents` misoli

```json
{
  "name": "Sparky",
  "role": "Creative",
  "sprite_id": "pixel_wizard_blue",
  "provider_label": "Groq",
  "protocol": "openai_compatible",
  "base_url": "https://api.groq.com/openai/v1",
  "api_key": "gsk_xxxxxxxx",
  "model": "llama-3.3-70b-versatile",
  "system_prompt": "Sen ijodkor agentsan. G'oyalarni kengaytir, nostandart yechimlar taklif qil.",
  "behavior": "active_patrol"
}
```

### `POST /chat` misoli

```json
{
  "message": "Ilovaga qanday gamification qo'shsam bo'ladi?",
  "agent_ids": null
}
```

Javob:
```json
{
  "final_output": "...(Executor rolidagi agent tomonidan yakunlangan javob)...",
  "contributions": [
    {"agent_name": "Ada", "role": "Architect", "text": "..."},
    {"agent_name": "Sparky", "role": "Creative", "text": "..."}
  ],
  "critique": "...(Critic rolidagi agent fikri, agar mavjud bo'lsa)..."
}
```

## Qanday ishlaydi: dinamik orkestratsiya

`app/orchestrator/graph.py` foydalanuvchining **haqiqiy, bazadagi** agentlariga qarab har
safar LangGraph grafini qayta quradi (blueprint hujjatidagi statik misoldan farqli):

1. Agentlar rollari bo'yicha guruhlanadi: `Architect → Creative → Guardian → Critic → Executor`
2. Har bir mavjud rol o'z tugunini oladi; mavjud bo'lmagan rollar avtomatik o'tkazib yuboriladi
3. `Architect`/`Creative`/`Guardian` — o'z taklifini qo'shadi (zanjir bo'ylab keyingi agent oldingi
   takliflarni ko'radi)
4. `Critic` — barcha takliflarni tanqidiy tahlil qiladi
5. `Executor` — hammasini jamlab, yakuniy javobni beradi (agar alohida Executor agent bo'lmasa,
   oxirgi agent shu vazifani ham bajaradi)

## Xavfsizlik bo'yicha eslatmalar

- **Hech qachon** `.env` faylini yoki haqiqiy API kalitlaringizni Git'ga yoki chatga
  yubormang — ular kompromis bo'lgan hisoblanadi va darhol almashtirilishi kerak.
- Backend Supabase'ga **service_role** kalit bilan ulanadi (RLS'ni bypass qiladi), shuning
  uchun har bir so'rovda `user_id` bo'yicha qo'lda filtrlash amalga oshirilgan — buni
  o'chirmang.
- Agentlarning LLM API kalitlari bazada har doim **shifrlangan** holda saqlanadi va
  hech qachon API javoblarida qaytarilmaydi.
- Production'da `ALLOWED_ORIGINS=*` o'rniga aniq domen(lar) ro'yxatini qo'yish tavsiya
  etiladi.

## Keyingi qadam (Roadmap bo'yicha)

- ✅ Phase 1: Supabase SQL sxemasi tayyor (`sql/schema.sql`)
- ✅ Phase 2: FastAPI backend + LangGraph orkestratsiya tayyor
- ⏭ Phase 3: Flutter — Google Sign-In (Supabase Auth) + Flame pixel interfeysini shu API'ga bog'lash
- ⏭ Phase 4: Ko'p-agentli hamkorlikni real API kalitlar bilan test qilish
