<div align="center">

# 🎬 Found Film Friend

**Свайпай фильмы. Оценивай. Смотри с друзьями.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://core.telegram.org/bots)
[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Android](https://img.shields.io/badge/Android-Java-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://developer.android.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Live-222?style=for-the-badge&logo=github&logoColor=white)](https://mr-akula.github.io/Found_Film_Friend/)

[🌐 Открыть веб-версию](https://mr-akula.github.io/Found_Film_Friend/) • [🤖 Открыть в Telegram](https://t.me/MrAKULA_bot) • [📱 Скачать APK](../../releases)

</div>

---

## О проекте

**Found Film Friend** — сервис рекомендаций фильмов с системой друзей. Пользователь листает карточки фильмов (как Tinder), ставит лайк или дизлайк, формирует список «хочу посмотреть», и видит общие фильмы с друзьями.

Проект доступен в **трёх форматах**:

| Платформа | Статус | Технологии |
|-----------|--------|------------|
| 🤖 Telegram Bot | ✅ Запущен | Python, pyTeleBot, SQLite |
| 🌐 Web App | ✅ GitHub Pages | HTML/CSS/JS, Supabase |
| 📱 Android | 🚧 В разработке | Java, Retrofit, Supabase |

---

## Возможности

- **Свайп фильмов** — листайте карточки, оценивайте одним нажатием
- **Умный алгоритм** — фильмы подбираются по приоритету и ещё не просмотренные
- **Возрастной фильтр** — показываются только фильмы подходящего рейтинга
- **Мой список** — все лайкнутые фильмы в одном месте
- **Где посмотреть** — прямые ссылки на стриминговые сервисы
- **Система друзей** — пригласите друга по ссылке, найдите общие фильмы
- **Реферальные ссылки** — поделитесь конкретным фильмом в Telegram

---

## Ветки репозитория

```
main           — стабильная версия
├── telegram   — Telegram бот (Python)
├── web        — Веб-приложение (GitHub Pages + Supabase)
└── android    — Android приложение (Java)
```

---

## Быстрый старт

### 🤖 Telegram Bot

```bash
# 1. Клонируем репозиторий
git clone https://github.com/Mr-AKULA/Found_Film_Friend.git
cd Found_Film_Friend

# 2. Устанавливаем зависимости
pip install -r requirements.txt

# 3. Настраиваем Settings.py
#    token = "ВАШ_ТОКЕН_БОТА"
#    BOT_USERNAME = "имя_бота"
#    ADMIN_IDS = [ваш_id]

# 4. Запускаем
python main.py
```

### 🌐 Web App (GitHub Pages + Supabase)

```
1. Создайте проект на https://supabase.com
2. Запустите docs/supabase.sql в SQL Editor
3. В docs/app.js замените:
   - SUPABASE_URL  = 'https://xxxxxxxx.supabase.co'
   - SUPABASE_ANON_KEY = 'ваш_anon_key'
4. В настройках репозитория включите:
   Settings → Pages → Source: /docs
5. Добавьте данные о фильмах через Supabase Table Editor
```

### 📱 Android App

```
1. Откройте папку android/ в Android Studio
2. В app/build.gradle замените:
   SUPABASE_URL      = 'https://xxxxxxxx.supabase.co'
   SUPABASE_ANON_KEY = 'ваш_anon_key'
3. Build → Run (минимум Android 8.0 / API 26)
```

---

## Архитектура

### База данных (Supabase / SQLite)

```
users/profiles   ←──┐
movies               │
  ├── posters        │
  ├── genres         │
  ├── watchability   │
  └── countries      │
actions (ratings) ───┤  user_id → profiles
friends ─────────────┘
referrals
```

### Алгоритм подбора фильмов

```sql
-- Случайный фильм с учётом приоритета
ORDER BY RANDOM() * POWER(10, priority) DESC
```

Фильмы с высоким `priority` показываются чаще — удобно для продвижения новых фильмов.

### Реферальные ссылки (Telegram Bot)

| Тип | Формат | Описание |
|-----|--------|----------|
| Фильм | `?start=film=ID` | Открывает конкретный фильм |
| Друг | `?start=id=ID` | Предлагает добавить в друзья |
| Фильм + Друг | `?start=id=ID_film=ID` | Комбо |
| Группа | `?start=group=ID` | Подборка фильмов |

---

## Структура проекта

```
Found_Film_Friend/
├── 📁 docs/                    ← GitHub Pages (web app)
│   ├── index.html              ← SPA
│   ├── style.css               ← Dark cinema theme
│   ├── app.js                  ← Логика + Supabase
│   └── supabase.sql            ← Схема БД
│
├── 📁 android/                 ← Android приложение
│   └── app/src/main/
│       ├── java/com/foundfilmfriend/
│       │   ├── MainActivity.java
│       │   ├── AuthActivity.java
│       │   ├── SplashActivity.java
│       │   ├── api/
│       │   │   ├── ApiClient.java
│       │   │   └── SupabaseApi.java
│       │   └── model/
│       │       ├── Movie.java
│       │       └── Profile.java
│       └── res/layout/
│
├── 📄 main.py                  ← Telegram Bot (главный)
├── 📄 sql_queries.py           ← SQL запросы
├── 📄 use_def.py               ← Вспомогательные функции
├── 📄 Settings.py              ← Конфигурация
├── 📄 requirements.txt
└── 📄 movies.db                ← SQLite база
```

---

## Технологии

**Telegram Bot:**
- `pyTelegramBotAPI` — работа с Telegram API
- `SQLite` — база данных
- `python-dotenv` — управление конфигурацией

**Web App:**
- Vanilla JS (без фреймворков) — работает прямо на GitHub Pages
- `Supabase JS SDK v2` — аутентификация + база данных
- `PostgreSQL` (через Supabase) — с Row Level Security
- CSS Custom Properties + CSS Animations

**Android:**
- `Java` — основной язык
- `Retrofit 2` — HTTP клиент для Supabase REST API
- `Glide` — загрузка изображений
- `Material Design 3` — UI компоненты
- `ViewBinding` — безопасная работа с View

---

## Скриншоты

> Добавьте скриншоты в папку `/docs/screenshots/` и раскомментируйте:

<!--
| Telegram Bot | Web App | Android |
|:---:|:---:|:---:|
| ![Bot](docs/screenshots/bot.png) | ![Web](docs/screenshots/web.png) | ![Android](docs/screenshots/android.png) |
-->

---

## Планы развития

- [x] Telegram Bot
- [x] Реферальная система  
- [x] Система друзей
- [x] Web App (GitHub Pages + Supabase)
- [ ] Android приложение
- [ ] Уведомления о новых фильмах
- [ ] Интеграция с Кинопоиском API
- [ ] Групповые просмотры

---

## Автор

**Mr-AKULA** — [GitHub](https://github.com/Mr-AKULA)

---

<div align="center">
  <sub>Сделано с ❤️ и 🎬</sub>
</div>
