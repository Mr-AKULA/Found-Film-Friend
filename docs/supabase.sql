-- ═══════════════════════════════════════════════════════
--   Found Film Friend — Supabase Schema
--   Run this in Supabase SQL Editor
-- ═══════════════════════════════════════════════════════

-- ── PROFILES (extends Supabase Auth) ──────────────────
CREATE TABLE IF NOT EXISTS public.profiles (
  id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name    TEXT,
  email_username  TEXT,
  birth_date      DATE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO public.profiles (id, email_username, birth_date)
  VALUES (
    NEW.id,
    split_part(NEW.email, '@', 1),
    (NEW.raw_user_meta_data->>'birth_date')::DATE
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ── MOVIES ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.movies (
  id                  SERIAL PRIMARY KEY,
  name                TEXT NOT NULL,
  slogan              TEXT,
  description         TEXT,
  year                INTEGER,
  age_rating          INTEGER DEFAULT 0,
  priority            INTEGER DEFAULT 1,
  duration_minutes    INTEGER,
  description_status  INTEGER
);

-- ── POSTERS ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.posters (
  id          SERIAL PRIMARY KEY,
  movie_id    INTEGER REFERENCES public.movies(id) ON DELETE CASCADE,
  preview_url TEXT NOT NULL
);

-- ── GENRES ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.genres (
  id   SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS public.movie_genres (
  movie_id INTEGER REFERENCES public.movies(id) ON DELETE CASCADE,
  genre_id INTEGER REFERENCES public.genres(id) ON DELETE CASCADE,
  PRIMARY KEY (movie_id, genre_id)
);

-- ── COUNTRIES ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.countries (
  id   SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS public.movie_countries (
  movie_id   INTEGER REFERENCES public.movies(id) ON DELETE CASCADE,
  country_id INTEGER REFERENCES public.countries(id) ON DELETE CASCADE,
  PRIMARY KEY (movie_id, country_id)
);

-- ── WATCHABILITY (where to stream) ───────────────────
CREATE TABLE IF NOT EXISTS public.watchability (
  id           SERIAL PRIMARY KEY,
  movie_id     INTEGER REFERENCES public.movies(id) ON DELETE CASCADE,
  service_name TEXT NOT NULL,
  link         TEXT NOT NULL
);

-- ── ACTIONS (user ratings) ────────────────────────────
CREATE TABLE IF NOT EXISTS public.actions (
  id             SERIAL PRIMARY KEY,
  user_id        UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  movie_id       INTEGER REFERENCES public.movies(id) ON DELETE CASCADE,
  want_to_watch  BOOLEAN,
  timestamp      TIMESTAMPTZ DEFAULT NOW(),
  rating         INTEGER,
  UNIQUE(user_id, movie_id)
);

-- ── FRIENDS ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.friends (
  id         SERIAL PRIMARY KEY,
  user_one   UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  user_two   UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  status     INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_one, user_two)
);

-- ── REFERRALS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.referrals (
  id          SERIAL PRIMARY KEY,
  user_id     UUID REFERENCES public.profiles(id),
  invited_by  UUID REFERENCES public.profiles(id),
  source      TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ══════════════════════════════════════════════════════

ALTER TABLE public.profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movies      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posters     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.genres      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movie_genres ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchability ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.actions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.friends     ENABLE ROW LEVEL SECURITY;

-- Profiles: anyone can read, owner can write
CREATE POLICY "Profiles are public"       ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Users insert own profile"  ON public.profiles FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users update own profile"  ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Movies & related: public read (admin writes via service key)
CREATE POLICY "Movies public read"       ON public.movies       FOR SELECT USING (true);
CREATE POLICY "Posters public read"      ON public.posters      FOR SELECT USING (true);
CREATE POLICY "Genres public read"       ON public.genres       FOR SELECT USING (true);
CREATE POLICY "Movie genres public read" ON public.movie_genres FOR SELECT USING (true);
CREATE POLICY "Watchability public read" ON public.watchability FOR SELECT USING (true);

-- Actions: users manage own; anyone can read want_to_watch=true (for common movies)
CREATE POLICY "Users manage own actions"  ON public.actions FOR ALL   USING (auth.uid() = user_id);
CREATE POLICY "Liked movies are visible"  ON public.actions FOR SELECT USING (want_to_watch = true);

-- Friends: users see own friendships, insert own
CREATE POLICY "Users see own friends"     ON public.friends FOR SELECT USING (auth.uid() = user_one OR auth.uid() = user_two);
CREATE POLICY "Users add friends"         ON public.friends FOR INSERT WITH CHECK (auth.uid() = user_one);
CREATE POLICY "Users update own friends"  ON public.friends FOR UPDATE USING (auth.uid() = user_one);

-- ══════════════════════════════════════════════════════
-- RPC FUNCTION: get_next_movie
-- Returns one unrated movie matching user's age
-- ══════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION public.get_next_movie(p_user_id UUID)
RETURNS TABLE (
  id           INTEGER,
  name         TEXT,
  slogan       TEXT,
  description  TEXT,
  year         INTEGER,
  age_rating   INTEGER,
  priority     INTEGER,
  preview_url  TEXT
)
LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
  user_age INTEGER;
BEGIN
  -- Calculate user's age from birth_date
  SELECT EXTRACT(YEAR FROM AGE(CURRENT_DATE, birth_date))::INTEGER
  INTO user_age
  FROM public.profiles
  WHERE id = p_user_id;

  -- Default to 18 if no birth_date
  IF user_age IS NULL THEN user_age := 18; END IF;

  RETURN QUERY
  SELECT
    m.id,
    m.name,
    m.slogan,
    m.description,
    m.year,
    m.age_rating,
    m.priority,
    p.preview_url
  FROM public.movies m
  LEFT JOIN public.posters p ON m.id = p.movie_id
  WHERE
    COALESCE(m.age_rating, 0) <= user_age
    AND m.id NOT IN (
      SELECT movie_id FROM public.actions WHERE user_id = p_user_id
    )
  ORDER BY RANDOM() * POWER(10, COALESCE(m.priority, 1)::FLOAT) DESC
  LIMIT 1;
END;
$$;

GRANT EXECUTE ON FUNCTION public.get_next_movie TO authenticated, anon;

-- ══════════════════════════════════════════════════════
-- INDEXES for performance
-- ══════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_actions_user_id      ON public.actions(user_id);
CREATE INDEX IF NOT EXISTS idx_actions_movie_id     ON public.actions(movie_id);
CREATE INDEX IF NOT EXISTS idx_actions_want         ON public.actions(user_id, want_to_watch);
CREATE INDEX IF NOT EXISTS idx_friends_user_one     ON public.friends(user_one);
CREATE INDEX IF NOT EXISTS idx_friends_user_two     ON public.friends(user_two);
CREATE INDEX IF NOT EXISTS idx_posters_movie_id     ON public.posters(movie_id);

-- ══════════════════════════════════════════════════════
-- SAMPLE DATA (optional, for testing)
-- Remove or replace with real data from your movies.db
-- ══════════════════════════════════════════════════════

INSERT INTO public.movies (name, slogan, description, year, age_rating, priority) VALUES
  ('Интерстеллар', 'Следующее поколение отправится дальше',
   'Команда исследователей путешествует сквозь червоточину в попытке обеспечить выживание человечества.',
   2014, 12, 3),
  ('Начало', 'Твой разум — место преступления',
   'Кобб — вор, крадущий ценные секреты из глубин подсознания во время сна.',
   2010, 12, 3),
  ('Побег из Шоушенка', 'Страх может сдержать тебя, надежда может освободить',
   'Два заключённых дружатся, находя утешение и возможное спасение через акты простой человеческой доброты.',
   1994, 16, 3),
  ('Форрест Гамп', NULL,
   'Несколько десятилетий американской истории глазами доброго и искреннего человека.',
   1994, 12, 2),
  ('Матрица', 'Добро пожаловать в реальный мир',
   'Хакер узнаёт от таинственных повстанцев правду о реальности.',
   1999, 16, 3)
ON CONFLICT DO NOTHING;

INSERT INTO public.posters (movie_id, preview_url)
SELECT id, 'https://images.kinocheck.com/images/movies/' || LOWER(REPLACE(name, ' ', '_')) || '.jpg'
FROM public.movies
ON CONFLICT DO NOTHING;
