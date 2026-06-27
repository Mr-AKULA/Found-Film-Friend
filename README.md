<div align="center">

# 🎬 Found Film Friend

**Свайпай фильмы. Оценивай. Смотри с друзьями.**

[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Live-222?style=for-the-badge&logo=github&logoColor=white)](https://mr-akula.github.io/Found-Film-Friend/)
[![PWA](https://img.shields.io/badge/PWA-Ready-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)](https://mr-akula.github.io/Found-Film-Friend/)
[![Telegram](https://img.shields.io/badge/Telegram_Mini_App-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/MrAKULA_bot)

[🌐 Открыть веб-версию](https://mr-akula.github.io/Found-Film-Friend/) • [✈️ Открыть в Telegram](https://t.me/MrAKULA_bot)

</div>

---

## О проекте

**Found Film Friend** — сервис рекомендаций фильмов с системой друзей. Листайте карточки фильмов (как Tinder), ставьте лайк или дизлайк, копите список «хочу посмотреть», и находите совпадения с друзьями.

База данных: **38 000+ фильмов** с постерами, жанрами и ссылками на стриминговые сервисы.

| Платформа | Статус | Технологии |
|-----------|--------|------------|
| 🌐 Web App (PWA) | ✅ Запущен | Vanilla JS, Supabase, GitHub Pages |
| ✈️ Telegram Mini App | ✅ Запущен | Telegram WebApp API, авто-логин |
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
- В Telegram — авторизация автоматически через аккаунт Telegram
- В браузере — регистрация / вход / сброс пароля через email
- Статистика: оценено / хочу / смотрел / друзья + топ-5 жанров
- Объединение аккаунтов — слияние TG и браузерного аккаунтов без потери данных

**PWA / Telegram Mini App**
- Устанавливается на телефон как обычное приложение
- Открывается прямо внутри Telegram — без App Store
- Haptic feedback при свайпах (вибрация на iOS/Android)
- Офлайн-оболочка (service worker)

---

## Вход и аккаунты

### Telegram Mini App (рекомендуется)

Откройте бота [@MrAKULA_bot](https://t.me/MrAKULA_bot) и нажмите кнопку **🎬 Открыть FFF**. Авторизация происходит автоматически — никакого email или пароля.

### Браузер / ПК

Перейдите на [mr-akula.github.io/Found-Film-Friend](https://mr-akula.github.io/Found-Film-Friend/), зарегистрируйтесь через email и пароль.

### Объединение аккаунтов

Если вы начали в браузере, а потом открыли в Telegram (или наоборот) — у вас два отдельных аккаунта. Чтобы объединить их в один с сохранением всех данных:

1. Откройте Mini App в Telegram
2. Нажмите на логотип **FFF** → откроется раздел настроек
3. Прокрутите до раздела **«Объединить аккаунты»**
4. Введите email и пароль от браузерного аккаунта
5. Нажмите **Объединить**

После объединения:
- Все лайки из обоих аккаунтов сохраняются (без дублирования)
- Список друзей объединяется
- История рекомендаций сохраняется
- TG-аккаунт удаляется, браузерный становится основным
- Вход в Mini App по-прежнему происходит автоматически

> ⚠️ После объединения пароль браузерного аккаунта изменяется на внутренний TG-пароль. Чтобы снова входить с браузера, задайте новый пароль в настройках → **«Вход с браузера / ПК»**.

### Вход с браузера после Telegram

Если вы используете Mini App, но хотите также заходить с компьютера:

1. Откройте настройки в Mini App (логотип FFF)
2. Раздел **«Вход с браузера / ПК»** — скопируйте свой email
3. Задайте пароль в том же разделе
4. Войдите на сайте через этот email + пароль

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
6. Auth → Settings → отключите "Confirm email" (для Telegram авто-логина)
7. Загрузите фильмы через export_to_supabase.py
```

### ✈️ Telegram Mini App

```
1. Запустите бота: python main.py
2. В @BotFather:
   /mybots → ваш бот → Bot Settings → Menu Button
   → URL: https://ВАШ-НИК.github.io/Found-Film-Friend/
   → Текст: 🎬 Found Film Friend
3. Пользователь открывает бота → нажимает кнопку меню → Mini App
4. Авторизация происходит автоматически через Telegram
```

---

## Архитектура

### База данных (Supabase PostgreSQL)

```
profiles         ←── auth.users (telegram_id, telegram_username)
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
├── 📁 docs/                    ← Web App / Telegram Mini App
│   ├── index.html              ← SPA
│   ├── style.css               ← Dark cinema theme
│   ├── app.js                  ← Логика + Supabase + Telegram WebApp API
│   ├── manifest.json           ← PWA манифест
│   ├── sw.js                   ← Service Worker
│   ├── icon-192.png            ← PWA иконка
│   ├── icon-512.png            ← PWA иконка (maskable)
│   └── supabase.sql            ← Схема БД + RPC функции
│
├── 📄 main.py                  ← Telegram Bot (запускает Mini App)
├── 📄 sql_queries.py           ← SQL запросы
├── 📄 export_to_supabase.py    ← Миграция SQLite → Supabase
└── 📄 movies.db                ← SQLite (локальная копия)
```

---

## Технологии

**Web App / Mini App:**
- Vanilla JS (без фреймворков) — 0 зависимостей в рантайме
- `Supabase JS SDK v2` — auth + database + RPC
- `Telegram WebApp JS API` — авто-логин, haptic feedback, полный экран
- CSS Custom Properties + CSS Animations + PWA Service Worker

**Telegram Bot:**
- `pyTelegramBotAPI` — запуск Mini App через кнопку меню
- Реферальные ссылки с параметрами

---

## Планы

- [x] Web App (GitHub Pages + Supabase)
- [x] Telegram Mini App с авто-логином
- [x] Система друзей с инвайт-ссылками
- [x] Умный алгоритм (приоритет + лайки + персонализация)
- [x] Свайп вверх = «уже смотрел»
- [x] Свайп вниз = поделиться фильмом
- [x] Фильтр по жанрам
- [x] Отмена последнего свайпа
- [x] Поиск по списку желаний
- [x] Статистика пользователя
- [x] Онбординг для новых пользователей
- [x] PWA — установка на телефон
- [x] Рекомендации между друзьями
- [x] Haptic feedback в Mini App
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
