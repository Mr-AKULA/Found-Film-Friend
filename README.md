<div align="center">

# 🎬 Found Film Friend

**Свайпай фильмы. Оценивай. Смотри с друзьями.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Android](https://img.shields.io/badge/Android-Java-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://developer.android.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Live-222?style=for-the-badge&logo=github&logoColor=white)](https://mr-akula.github.io/Found-Film-Friend/)

[🌐 Открыть веб-версию](https://mr-akula.github.io/Found-Film-Friend/) • [🤖 Открыть в Telegram](https://t.me/MrAKULA_bot) • [📱 Скачать APK](../../releases)

</div>

---

## О проекте

**Found Film Friend** — сервис рекомендаций фильмов с системой друзей. Пользователь листает карточки фильмов (как Tinder), ставит лайк или дизлайк, формирует список «хочу посмотреть», и видит общие фильмы с друзьями.

База данных: **12 000+ фильмов** с постерами, жанрами и ссылками на стриминговые сервисы.

Проект доступен в **трёх форматах**:

| Платформа | Статус | Технологии |
|-----------|--------|------------|
| 🌐 Web App | ✅ Запущен | Vanilla JS, Supabase, GitHub Pages |
| 🤖 Telegram Bot | ✅ Запущен | Python, pyTeleBot, SQLite |
| 📱 Android | 🚧 В разработке | Java, Retrofit, Supabase |

---

## Возможности

### Умный алгоритм подбора
Каждый фильм получает скор из трёх сигналов:

```
скор = RANDOM() × 10 ^ ( priority + log(лайки сообщества) + log(жанровые предпочтения юзера) )
```

| Сигнал | Источник | Эффект |
|--------|----------|--------|
| `priority` | Задаётся вручную (1–3) | Качественные фильмы чаще |
| `log(лайки)` | Всё сообщество | Популярное поднимается само |
| `log(жанровый скор)` | Личные лайки юзера | Персонализация по вкусу |

Чем больше фильмов оценил пользователь — тем точнее подборка.

### Полный список функций

- **Свайп фильмов** — листайте карточки, оценивайте кнопками или жестами
- **Возрастной фильтр** — фильмы подбираются под возраст пользователя
- **Мой список** — все лайкнутые фильмы с постерами
- **Система друзей** — пригласите друга по персональной ссылке
- **Общие фильмы** — видите что совпадает с конкретным другом
- **Список друга** — можно посмотреть что лайкнул друг
- **Сброс пароля** — восстановление через email
- **Персонализация** — алгоритм учится на жанрах которые вы лайкаете
- **Народный рейтинг** — лайки всех пользователей влияют на порядок
- **Где посмотреть** — прямые ссылки на стриминговые сервисы

---

## Быстрый старт

### 🌐 Web App (GitHub Pages + Supabase)

```
1. Создайте проект на https://supabase.com
2. Запустите docs/supabase.sql в SQL Editor
3. В docs/app.js замените:
   SUPABASE_URL     = 'https://xxxxxxxx.supabase.co'
   SUPABASE_ANON_KEY = 'ваш_anon_key'
4. Settings → Pages → Source: /docs
5. В Supabase → Auth → URL Configuration установите:
   Site URL: https://ВАШ-НИК.github.io/Found-Film-Friend/
6. Загрузите фильмы через export_to_supabase.py
7. (Опционально) Загрузите постеры через upload_posters.py
```

### 🤖 Telegram Bot

```bash
git clone https://github.com/Mr-AKULA/Found-Film-Friend.git
cd Found-Film-Friend
pip install -r requirements.txt
# Настройте Settings.py: token, BOT_USERNAME, ADMIN_IDS
python main.py
```

### 📱 Android App

```
1. Откройте папку android/ в Android Studio
2. Замените SUPABASE_URL и SUPABASE_ANON_KEY в app/build.gradle
3. Build → Run (Android 8.0+ / API 26)
```

---

## Архитектура

### База данных (Supabase PostgreSQL)

```
profiles         ←── auth.users (auto-created via trigger)
movies
  ├── posters         (preview_url → Supabase Storage)
  ├── genres
  ├── movie_genres    (many-to-many)
  ├── watchability    (ссылки на стриминг)
  └── countries
actions          (user_id, movie_id, want_to_watch)
friends          (user_one, user_two, status)
referrals
```

### Row Level Security

Все таблицы защищены RLS-политиками:
- Фильмы/постеры/жанры — публичное чтение
- Actions — только свои записи
- Friends — видит только участников дружбы
- Profiles — публичное чтение, запись только своего

### RPC функция `get_next_movie`

Выбирает случайный непросмотренный фильм с учётом возраста и трёх сигналов ранжирования. Работает через PostgreSQL `WITH` запросы без JOIN на posters (скалярный подзапрос исключает ambiguous column).

---

## Структура проекта

```
Found_Film_Friend/
├── 📁 docs/                    ← GitHub Pages (web app)
│   ├── index.html              ← SPA
│   ├── style.css               ← Dark cinema theme
│   ├── app.js                  ← Логика + Supabase SDK
│   └── supabase.sql            ← Схема БД + RPC функции
│
├── 📁 android/                 ← Android приложение
│   └── app/src/main/
│       ├── java/com/foundfilmfriend/
│       └── res/layout/
│
├── 📄 main.py                  ← Telegram Bot
├── 📄 sql_queries.py           ← SQL запросы бота
├── 📄 export_to_supabase.py    ← Миграция SQLite → Supabase
├── 📄 upload_posters.py        ← Загрузка постеров в Storage
└── 📄 movies.db                ← SQLite (локальная копия)
```

---

## Технологии

**Web App:**
- Vanilla JS (без фреймворков) — работает на GitHub Pages
- `Supabase JS SDK v2` — auth + database + storage
- `PostgreSQL` через Supabase — с Row Level Security
- `persistSession: false` — обход Tracking Prevention в Edge/Firefox
- CSS Custom Properties + CSS Animations

**Telegram Bot:**
- `pyTelegramBotAPI` — Telegram API
- `SQLite` — локальная база данных
- Реферальные ссылки с параметрами фильм/друг/группа

**Android:**
- `Java` — основной язык
- `Retrofit 2` — HTTP клиент для Supabase REST API
- `Glide` — загрузка постеров
- `Material Design 3`

---

## Планы развития

- [x] Telegram Bot с реферальной системой
- [x] Web App (GitHub Pages + Supabase)
- [x] Система друзей с инвайт-ссылками
- [x] Умный алгоритм (приоритет + народный рейтинг + персонализация)
- [x] Сброс пароля через email
- [x] Просмотр списка друга
- [ ] Свайп вверх = "уже смотрел"
- [ ] Фильтр по жанрам на сегодня
- [ ] Android приложение
- [ ] Уведомления о новых совпадениях с друзьями
- [ ] Групповые просмотры

---

## Автор

**Mr-AKULA** — [GitHub](https://github.com/Mr-AKULA)

---

<div align="center">
  <sub>Сделано с ❤️ и 🎬</sub>
</div>
