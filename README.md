```markdown
# 🎬 Movie Recommendation Bot

Телеграм-бот для рекомендации фильмов с учетом возраста и предпочтений пользователя.

## 🚀 Установка и настройка

1. Клонируйте репозиторий
2. Создайте файл `Settings.py` в корне проекта:

```python
# Обязательные параметры
token = ''         # Токен вашего Telegram бота
file_bd = 'movies.db'  # Путь к файлу базы данных
XAPIKEY = ''       # API ключ от kinopoisk.dev

# Дополнительные настройки
admin_ids = []     # ID администраторов через запятую
log_file = 'bot.log'  # Файл для логов
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

## 📋 Основные команды

| Команда | Описание |
|---------|----------|
| `/start` | Начало работы с ботом |
| `/drop` | Сброс истории оценок |
| `/help` | Справка по использованию |
| `/stats` | Статистика для администраторов |

## ⚙️ Технические особенности

### 🔍 Алгоритм рекомендаций

Основной SQL-запрос (`get_random_movie_query()`) включает:

```sql
RANDOM() * POWER(10, m.priority) DESC
```

**Проблема:** В разных версиях SQLite могут возникать ошибки вычисления POWER.

**Решение:** Реализована функция:

```python
def power(x, y):
    return math.pow(x, y)
```

с регистрацией в SQLite:

```python
conn.create_function("POWER", 2, power)
```

### 🗃️ Структура проекта

```
project/
├── main.py          # Основной код бота
├── sql_queries.py    # Все SQL-запросы
├── use_def.py       # Вспомогательные функции
├── Settings.py       # Конфигурация
└── movies.db        # База данных фильмов
```

### 🔧 Тайм-аут обработки запросов

Для улучшения пользовательского опыта добавлена функция тайм-аута, которая ограничивает время выполнения запросов. Это позволяет избежать долгого ожидания ответа от сервера и улучшает отзывчивость бота.

```python
def timeout(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except concurrent.futures.TimeoutError:
                    bot.reply_to(args[0], "Время выполнения запроса истекло. Пожалуйста, попробуйте позже.")
        return wrapper
    return decorator
```

### 📅 Планы развития

- [ ] Система друзей и групп
- [ ] Интеграция с онлайн-кинотеатрами
- [ ] Персонализированные подборки
- [ ] Расширенная статистика

### 📌 Важно

Бот требует предварительной настройки базы данных с фильмами. Пример структуры таблиц доступен в файле `movies.db`.

Для работы с API Кинопоиска необходим бесплатный ключ: [kinopoisk.dev](https://kinopoisk.dev/)
```

Этот обновленный `README.md` включает информацию о новых функциях, таких как тайм-аут обработки запросов, и содержит более подробное описание структуры проекта и технических особенностей.

id+film+group
https://t.me/bot_for_assistant_bot?start=id=1927111121_film=123_group=1_from=YT
id+film
https://t.me/bot_for_assistant_bot?start=id=1927111121_film=123_from=YT
id
https://t.me/bot_for_assistant_bot?start=id=1927111121
film
https://t.me/bot_for_assistant_bot?start=film=123
group
https://t.me/bot_for_assistant_bot?start=group=1
None
https://t.me/bot_for_assistant_bot?start

https://t.me/MrAKULA_bot?start=film=8421_from=YT