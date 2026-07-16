-- =========================================================
-- Pixel-Agentic AI Orchestrator — Supabase SQL Schema
-- Buni Supabase dashboard > SQL Editor'da run qiling
-- =========================================================

-- Foydalanuvchilar jadvali (Supabase Auth foydalanuvchilariga ulanadi)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Foydalanuvchilar faqat o'z profilini ko'ra oladi" ON profiles;
CREATE POLICY "Foydalanuvchilar faqat o'z profilini ko'ra oladi"
    ON profiles FOR SELECT USING (auth.uid() = id);

-- Dinamik Agentlar jadvali
-- Diqqat: agentlar Gemini/Groq/OpenRouter bilan CHEKLANMAGAN. `protocol` ustuni
-- so'rov formatini bildiradi ("openai_compatible" — deyarli barcha zamonaviy
-- provayderlar: OpenAI, Groq, OpenRouter, Together, DeepSeek, Mistral, Gemini,
-- lokal Ollama va h.k.; yoki "anthropic" — Claude API). `base_url` orqali
-- foydalanuvchi istalgan yangi provayderni kodni o'zgartirmasdan qo'sha oladi.
CREATE TABLE IF NOT EXISTS agents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Executor', 'Critic', 'Architect', 'Creative', 'Guardian')),
    sprite_id TEXT NOT NULL,
    provider_label TEXT NOT NULL, -- ko'rinadigan nom, masalan 'Groq', 'DeepSeek', 'Mening Ollama'
    protocol TEXT NOT NULL CHECK (protocol IN ('openai_compatible', 'anthropic')),
    base_url TEXT NOT NULL, -- masalan https://api.groq.com/openai/v1
    api_key TEXT NOT NULL, -- Backend tomonidan Fernet bilan shifrlangan holda saqlanadi
    model TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    behavior TEXT NOT NULL DEFAULT 'active_patrol',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Foydalanuvchi faqat o'z agentlarini ko'ra oladi" ON agents;
CREATE POLICY "Foydalanuvchi faqat o'z agentlarini ko'ra oladi"
    ON agents FOR ALL USING (auth.uid() = user_id);

-- Chat tarixi jadvali (orkestratsiya natijalarini saqlash uchun)
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES profiles(id) ON DELETE CASCADE NOT NULL,
    user_message TEXT NOT NULL,
    final_output TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Foydalanuvchi faqat o'z chat tarixini ko'ra oladi" ON chat_history;
CREATE POLICY "Foydalanuvchi faqat o'z chat tarixini ko'ra oladi"
    ON chat_history FOR ALL USING (auth.uid() = user_id);

-- Yangi foydalanuvchi ro'yxatdan o'tganda profiles jadvaliga avtomatik yozish
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email)
    VALUES (NEW.id, NEW.email)
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
