<div align="center">

# 🎬 Found Film Friend

**Свайпай фильмы. Оценивай. Смотри с друзьями.**

[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Live-222?style=for-the-badge&logo=github&logoColor=white)](https://mr-akula.github.io/Found-Film-Friend/)
[![PWA](https://img.shields.io/badge/PWA-Ready-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)](https://mr-akula.github.io/Found-Film-Friend/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

[🌐 Открыть веб-версию](https://mr-akula.github.io/Found-Film-Friend/) • [🤖 Открыть в Telegram](https://t.me/MrAKULA_bot)

</div>

---

## О проекте

**Found Film Friend** — сервис рекомендаций фильмов с системой друзей. Листайте карточки фильмов (как Tinder), ставьте лайк или дизлайк, копите список «хочу посмотреть», и находите совпадения с друзьями.

База данных: **38 000+ фильмов** с постерами, жанрами и ссылками на стриминговые сервисы.

| Платформа | Статус | Технологии |
|-----------|--------|------------|
| 🌐 Web App (PWA) | ✅ Запущен | Vanilla JS, Supabase, GitHub Pages |
| 🤖 Telegram Bot | ✅ Запущен | Python, pyTeleBot, SQLite |
| 📱 Android | 🚧 В разработке | Java, Retrofit, Supabase |

---

## Возможности

### Умный алгоритм подбора

Каждый фильм получает скор из трёх сигналов:

```
скор = RANDOM() × 10 ^ ( priority + log(1 + лайки сообщества) + log(1 + жанровый скор юзера) )
```

| Сигнал | Источник | Эффект |
|--------|----------|--------|
| `priority` | Задаётся вручную (1–3) | Качественные фильмы чаще |
| `log(лайки)` | Всё сообщество | Популярное поднимается само |
| `log(жанровый скор)` | Личные лайки пользователя | Персонализация по вкусу |

### Полный список функций

**Оценка фильмов**
- Свайп вправо / кнопка ❤️ — хочу посмотреть
- Свайп влево / кнопка ✕ — не интересно
- Свайп вверх / кнопка 👁 — уже смотрел (исключается из ленты)
- Свайп вниз — поделиться фильмом с другом
- Клавиатура: `→` лайк, `←` скип, `↑` смотрел
- Отмена последнего действия — кнопка «↩ Отменить» (3.5с) или `Ctrl+Z`

**Фильтры и персонализация**
- Горизонтальная панель жанров — фильтрует ленту на лету
- Онбординг — при первом входе выбор любимых жанров
- Возрастной фильтр — фильмы подбираются под возраст пользователя

**Список желаний**
- Все лайкнутые фильмы с постерами
- Живой поиск по названию
- Детальная карточка с описанием и ссылками «Где посмотреть»
- Удаление из списка

**Друзья и рекомендации**
- Пригласительная ссылка — один клик, друг добавлен
- Общие фильмы — что совпадает с конкретным другом
- Список друга — всё что друг лайкнул
- Рекомендации — отправь фильм другу напрямую
- Оценка рекомендаций — ❤️ хочу / 👁 смотрел / ✕ не интересно

**Аккаунт**
- Регистрация / вход / сброс пароля через email
- Статистика: оценено / хочу / смотрел / друзья + топ-5 жанров

**PWA**
- Устанавливается на телефон как обычное приложение
- Офлайн-оболочка (service worker кэширует статику)
- Иконка с мотивом кинохлопушки + сердца

---

## Быстрый старт

### 🌐 Web App

```
1. Создайте проект на https://supabase.com
2. Запустите docs/supabase.sql в SQL Editor
3. В docs/app.js замените:
   SUPABASE_URL      = 'https://xxxxxxxx.supabase.co'
   SUPABASE_ANON_KEY = 'ваш_anon_key'
4. Settings → Pages → Source: /docs
5. Auth → URL Configuration:
   Site URL: https://ВАШ-НИК.github.io/Found-Film-Friend/
6. Загрузите фильмы через export_to_supabase.py
```

### 🤖 Telegram Bot

```bash
git clone https://github.com/Mr-AKULA/Found-Film-Friend.git
cd Found-Film-Friend
pip install -r requirements.txt
# Настройте Settings.py: token, BOT_USERNAME, ADMIN_IDS
python main.py
```

---

## Архитектура

### База данных (Supabase PostgreSQL)

```
profiles         ←── auth.users (auto-created via trigger)
movies
  ├── posters         (preview_url → Kinopoisk CDN)
  ├── genres
  ├── movie_genres    (many-to-many)
  ├── watchability    (ссылки на стриминг)
  └── countries
actions          (user_id, movie_id, want_to_watch, watched)
friends          (user_one, user_two, status)
recommendations  (from_user, to_user, movie_id, seen)
referrals
```

### Row Level Security

- Фильмы / постеры / жанры — публичное чтение
- `actions` — только свои записи (+ liked записи видны друзьям для общих фильмов)
- `friends` — видят только участники дружбы
- `recommendations` — видят только отправитель и получатель
- `profiles` — публичное чтение, запись только своего

### RPC `get_next_movie(p_user_id, p_genre_ids)`

PostgreSQL-функция с `WITH`-запросами. Выбирает один непросмотренный фильм:
1. Исключает уже оценённые (`actions`)
2. Фильтрует по возрасту пользователя
3. Фильтрует по выбранным жанрам (если передан `p_genre_ids`)
4. Требует наличия постера
5. Ранжирует по формуле 3-сигнального скора

---

## Структура проекта

```
Found_Film_Friend/
├── 📁 docs/                    ← GitHub Pages (web app)
│   ├── index.html              ← SPA
│   ├── style.css               ← Dark cinema theme
│   ├── app.js                  ← Логика + Supabase SDK
│   ├── manifest.json           ← PWA манифест
│   ├── sw.js                   ← Service Worker
│   ├── icon-192.png            ← PWA иконка
│   ├── icon-512.png            ← PWA иконка (maskable)
│   └── supabase.sql            ← Схема БД + RPC функции
│
├── 📄 main.py                  ← Telegram Bot
├── 📄 sql_queries.py           ← SQL запросы бота
├── 📄 export_to_supabase.py    ← Миграция SQLite → Supabase
└── 📄 movies.db                ← SQLite (локальная копия)
```

---

## Технологии

**Web App:**
- Vanilla JS (без фреймворков) — GitHub Pages, 0 зависимостей в рантайме
- `Supabase JS SDK v2` — auth + database + RPC
- `persistSession: false` — обход Tracking Prevention в Edge/Firefox
- CSS Custom Properties + CSS Animations + PWA Service Worker

**Telegram Bot:**
- `pyTelegramBotAPI` — Telegram API
- `SQLite` — локальная база данных
- Реферальные ссылки с параметрами

---

## Планы

- [x] Telegram Bot с реферальной системой
- [x] Web App (GitHub Pages + Supabase)
- [x] Система друзей с инвайт-ссылками
- [x] Умный алгоритм (приоритет + лайки + персонализация)
- [x] Сброс пароля через email
- [x] Список друга
- [x] Свайп вверх = «уже смотрел»
- [x] Свайп вниз = поделиться фильмом
- [x] Фильтр по жанрам
- [x] Отмена последнего свайпа
- [x] Поиск по списку желаний
- [x] Статистика пользователя
- [x] Онбординг для новых пользователей
- [x] PWA — установка на телефон
- [x] Рекомендации между друзьями
- [ ] Android приложение
- [ ] Уведомления о новых совпадениях
- [ ] Групповые сессии просмотра

---

## Авторы

| Роль | Участник |
|------|----------|
| 💡 Идея | **vnyzaica** — [GitHub](https://github.com/vnyzaica) |
| 👨‍💻 Автор | **Mr-AKULA** — [GitHub](https://github.com/Mr-AKULA) |

---

<div align="center">
  <sub>Сделано с ❤️ и 🎬</sub>
</div>
