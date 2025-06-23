import sqlite3
from datetime import datetime
import math

def power(x, y):
    return math.pow(x, y)

def update_movies_description_status():
    return """
    UPDATE movies
    SET description_status = ? 
    WHERE id = ?
    """
# User-related queries
def check_user_exists():
    return "SELECT 1 FROM users WHERE user_id = ?"

def get_user_birth_date():
    return "SELECT birth_date FROM users WHERE user_id = ?"

def get_user_name():
    return "SELECT first_name FROM users WHERE user_id = ?"

def get_user_info():
    return "SELECT first_name, username FROM users WHERE user_id = ?"

def insert_user():
    return """
    INSERT INTO users (
        user_id, first_name, last_name, username, 
        language_code, is_bot, birth_date, 
        registration_date, last_activity_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

def update_last_activity_user():
    return """
    UPDATE users
    SET last_activity_date = ?
    WHERE user_id = ?
    """

def get_empty_movie_query():
    return """
    SELECT
        m.id,
        m.name,
        m.slogan,
        m.description,
        m.year
    FROM movies m
    RIGHT JOIN actions a ON m.id = a.movie_id AND a.user_id = ?
    WHERE
        m.age_rating <= (
            SELECT strftime('%Y', 'now') - strftime('%Y', u.birth_date) - (
                strftime('%m-%d', 'now') < strftime('%m-%d', u.birth_date)
            )
            FROM users u
            WHERE u.user_id = ?
        )
        AND a.want_to_watch IS NULL
    LIMIT 1
    """


# short_description
# description
# Movie-related queries
def get_random_movie_query():
    return """
    SELECT
        m.id,
        m.name,
        m.slogan,
        m.description,
        m.year,
        m.priority
    FROM movies m
    LEFT JOIN actions a ON m.id = a.movie_id AND a.user_id = ?
    WHERE
        m.age_rating <= (
            SELECT strftime('%Y', 'now') - strftime('%Y', u.birth_date) - (
                strftime('%m-%d', 'now') < strftime('%m-%d', u.birth_date)
            )
            FROM users u
            WHERE u.user_id = ?
        )
        AND a.movie_id IS NULL
    ORDER BY RANDOM() * POWER(10, m.priority) DESC
    LIMIT 1
    """

def get_specific_movie():
    return """
    SELECT
        m.id,
        m.name,
        m.slogan,
        m.description,
        m.year,
        m.priority
    FROM movies m
    WHERE m.id = ? 
    AND m.age_rating <= (
        SELECT strftime('%Y', 'now') - strftime('%Y', u.birth_date) - (
            strftime('%m-%d', 'now') < strftime('%m-%d', u.birth_date)
        )
        FROM users u
        WHERE u.user_id = ?
    )
    """

def get_movie_poster():
    return "SELECT preview_url FROM posters WHERE movie_id = ?"

# Action-related queries
def insert_action():
    return """
    INSERT OR REPLACE INTO actions (
        user_id, movie_id, 
        want_to_watch, timestamp, rating
    ) VALUES (?, ?, ?, ?, ?)
    """

def get_pending_actions():
    return """
    SELECT user_id, movie_id, want_to_watch, rating 
    FROM actions 
    WHERE user_id = ? AND want_to_watch IS NULL
    """

def update_action_rating():
    return """
    UPDATE actions 
    SET want_to_watch = ? 
    WHERE user_id = ? AND movie_id = ?
    """

# get_users_without_movies() - не используется (закомментирован в main.py)
# Admin queries
def get_users_without_movies():
    return """
    SELECT u.user_id, COUNT(m.id) 
    FROM users u
    LEFT JOIN movies m ON m.age_rating <= (
        strftime('%Y', 'now') - strftime('%Y', u.birth_date) - (
            strftime('%m-%d', 'now') < strftime('%m-%d', u.birth_date)
        )
    )
    LEFT JOIN actions a ON m.id = a.movie_id AND a.user_id = u.user_id
    WHERE a.movie_id IS NULL
    GROUP BY u.user_id
    HAVING COUNT(m.id) = 0
    """

# Было (ошибочно):
# def get_user_exists():
#     return "SELECT 1 FROM users WHERE id = ?"

# Стало (правильно):
def get_user_exists():
    return "SELECT 1 FROM users WHERE user_id = ?"

def get_user_name():
    return "SELECT first_name, username FROM users WHERE user_id = ?"

def get_user_birth_date():
    return "SELECT birth_date FROM users WHERE user_id = ?"
# Для проверки существования записи
def check_existing_action():
    return """
    SELECT 1 FROM actions 
    WHERE user_id = ? AND movie_id = ?
    LIMIT 1
    """

def get_last_shown_movie_query():
    return """
    SELECT movie_id FROM actions 
    WHERE user_id = ? 
    ORDER BY timestamp DESC 
    LIMIT 1
    """

# Добавить эти новые запросы:
def get_friends_list():
    return """
    SELECT u.user_id, u.username 
    FROM friends f
    JOIN users u ON (f.id_friend_one = u.user_id OR f.id_friend_two = u.user_id)
    WHERE (f.id_friend_one = ? OR f.id_friend_two = ?) 
    AND f.friend = 1
    AND u.user_id != ?
    ORDER BY u.username
    """

def get_friend_movies():
    return """
    SELECT DISTINCT m.id, m.name 
    FROM movies m
    JOIN actions a ON m.id = a.movie_id 
    WHERE a.user_id = ? AND a.want_to_watch = 1
    ORDER BY m.name
    """

def get_common_movies():
    return """
    SELECT DISTINCT m.id, m.name 
    FROM movies m
    JOIN actions a1 ON m.id = a1.movie_id AND a1.user_id = ? AND a1.want_to_watch = 1
    JOIN actions a2 ON m.id = a2.movie_id AND a2.user_id = ? AND a2.want_to_watch = 1
    ORDER BY m.name
    """

def get_watchability_links():
    return "SELECT service_name, link FROM watchability WHERE movie_id = ?"

def check_friendship_status():
    return """
    SELECT 1 FROM friends
    WHERE ((id_friend_one = ? AND id_friend_two = ?) 
    OR (id_friend_one = ? AND id_friend_two = ?))
    AND friend = 1
    """

