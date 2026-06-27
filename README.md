<div align="center">

# 🎬 Found Film Friend

**Свайпай фильмы. Оценивай. Смотри с друзьями.**

[![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![GitHub Pages](https://img.shields.io/badge/GitHub_Pages-Live-222?style=for-the-badge&logo=github&logoColor=white)](https://mr-akula.github.io/Found-Film-Friend/)
[![PWA](https://img.shields.io/badge/PWA-Ready-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)](https://mr-akula.github.io/Found-Film-Friend/)
[![Telegram](https://img.shields.io/badge/Telegram_Mini_App-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/MrAKULA_bot)
[![Android TV](https://img.shields.io/badge/Android_TV-APK-3DDC84?style=for-the-badge&logo=android&logoColor=white)](https://github.com/Mr-AKULA/Found-Film-Friend/releases/tag/v1.0-tv)

[🌐 Веб-версия](https://mr-akula.github.io/Found-Film-Friend/) • [✈️ Telegram](https://t.me/MrAKULA_bot) • [📺 Скачать TV APK](https://github.com/Mr-AKULA/Found-Film-Friend/releases/download/v1.0-tv/FoundFilmFriend-TV.apk)

</div>

---

## О проекте

**Found Film Friend** — сервис рекомендаций фильмов с системой друзей. Листайте карточки фильмов (как Tinder), ставьте лайк или дизлайк, копите список «хочу посмотреть», и находите совпадения с друзьями.

База данных: **38 000+ фильмов** с постерами, жанрами и ссылками на стриминговые сервисы.

| Платформа | Статус | Технологии |
|-----------|--------|------------|
| 🌐 Web App (PWA) | ✅ Запущен | Vanilla JS, Supabase, GitHub Pages |
| ✈️ Telegram Mini App | ✅ Запущен | Telegram WebApp API, авто-логин |
| 📺 Android TV | ✅ Запущен | Java, WebView, D-pad управление |

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
- Быстрые фильтры 🎬 Фильмы / 🎨 Мульты
- Онбординг — при первом входе выбор любимых жанров
- Возрастной фильтр — фильмы подбираются под возраст пользователя

**Просмотр**
- Кнопка **▶ Смотреть бесплатно** в карточке фильма — встроенный плеер (kinokino.vip)
- Ссылки на стриминговые сервисы (Кинопоиск, Иви и др.)

**Список желаний**
- Все лайкнутые фильмы с постерами
- Живой поиск по названию
- Детальная карточка с описанием и ссылками
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
- Haptic feedback при свайпах
- Офлайн-оболочка (service worker)

**📺 Android TV**
- D-pad управление: ← скип, → лайк, ↑ смотрел
- Вход через 6-значный код с телефона — без клавиатуры
- Автоматический вход после первой авторизации
- Нативный сплэш-экран пока грузится страница

---

## Вход и аккаунты

### Telegram Mini App (рекомендуется)

Откройте бота [@MrAKULA_bot](https://t.me/MrAKULA_bot) и нажмите кнопку **🎬 Открыть FFF**. Авторизация происходит автоматически.

### Браузер / ПК

Перейдите на [mr-akula.github.io/Found-Film-Friend](https://mr-akula.github.io/Found-Film-Friend/) и зарегистрируйтесь.

### 📺 Android TV

1. Скачайте [FoundFilmFriend-TV.apk](https://github.com/Mr-AKULA/Found-Film-Friend/releases/download/v1.0-tv/FoundFilmFriend-TV.apk)
2. Установите: `adb install FoundFilmFriend-TV.apk`
3. При запуске появится 6-значный код
4. На телефоне: Настройки → **Войти на TV** → введите код
5. TV войдёт в аккаунт автоматически

### Объединение аккаунтов

Если начали в браузере, а потом открыли в Telegram — два отдельных аккаунта. Чтобы объединить:

1. Откройте Mini App в Telegram
2. Нажмите на логотип **FFF** → Настройки
3. Раздел **«Объединить аккаунты»** → введите email и пароль браузерного аккаунта
4. Нажмите **Объединить**

Все лайки, друзья и рекомендации объединятся без потерь.

---

## Быстрый старт

### 🌐 Web App

```
1. Создайте проект на https://supabase.com
2. Запустите docs/supabase.sql в SQL Editor
3. В docs/app.js замените:
   SUPABASE_URL      = 'https://xxxxxxxx.supabase.co'
   SUPABASE_ANON_KEY = 'ваш_anon_key'
4. Settings → Pages → Source: branch AKULA / docs
5. Auth → URL Configuration:
   Site URL: https://ВАШ-НИК.github.io/Found-Film-Friend/
6. Auth → Settings → отключите "Confirm email"
```

### ✈️ Telegram Mini App

```
1. python main.py
2. В @BotFather → /mybots → Bot Settings → Menu Button
   URL: https://ВАШ-НИК.github.io/Found-Film-Friend/
3. Пользователь открывает бота → нажимает кнопку меню → Mini App
```

### 📺 Android TV APK

```
1. cd android-tv
2. ./gradlew assembleDebug
3. adb install app/build/outputs/apk/debug/app-debug.apk
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
tv_sessions      (code, user_id, activated, access_token, refresh_token)
```

### Row Level Security

- Фильмы / постеры / жанры — публичное чтение
- `actions` — только свои записи (+ видны друзьям для общих фильмов)
- `friends` — видят только участники дружбы
- `recommendations` — видят только отправитель и получатель
- `tv_sessions` — INSERT любой, SELECT только неактивированные; токены доступны только через RPC
- `profiles` — публичное чтение, запись только своего

### RPC функции

| Функция | Назначение |
|---------|-----------|
| `get_next_movie(p_user_id, p_genre_ids)` | Следующий фильм по 3-сигнальному скору |
| `merge_accounts(from, to, ...)` | Слияние TG и браузерного аккаунтов |
| `activate_tv_session(code, access_token, refresh_token)` | Телефон активирует TV-сессию |
| `claim_tv_session(code)` | TV забирает токены (атомарно: читает + удаляет) |

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
│   ├── icon-192.png / icon-512.png ← PWA иконки
│   └── supabase.sql            ← Схема БД + RPC функции
│
├── 📁 android-tv/              ← Android TV приложение
│   ├── app/src/main/
│   │   ├── java/.../MainActivity.java  ← WebView + D-pad + TVBridge
│   │   └── AndroidManifest.xml
│   ├── build.gradle
│   └── gradle.properties
│
├── 📄 FoundFilmFriend-TV.apk   ← Собранный APK
├── 📄 main.py                  ← Telegram Bot
└── 📄 supabase.sql             ← Схема БД
```

---

## Технологии

**Web App / Mini App:**
- Vanilla JS — 0 зависимостей в рантайме
- `Supabase JS SDK v2` — auth + database + RPC
- `Telegram WebApp JS API` — авто-логин, haptic feedback
- CSS Custom Properties + Animations + PWA Service Worker

**Android TV:**
- Java + Android WebView — нативная обёртка
- `JavascriptInterface` — двусторонний мост JS ↔ Java
- D-pad перехватывается только на нужных экранах (TVBridge)
- Вход через паiring-код без клавиатуры

**Telegram Bot:**
- `pyTelegramBotAPI` — запуск Mini App через кнопку меню

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
- [x] Встроенный плеер (kinokino.vip)
- [x] Android TV приложение с D-pad управлением
- [x] TV вход через pairing-код с телефона
- [ ] Push-уведомления о новых совпадениях
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
