import sqlite3
from datetime import datetime
import math

def power(x, y):
    return math.pow(x, y)

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
    """

def get_movie_poster():
    return "SELECT preview_url FROM posters WHERE movie_id = ?"

def count_available_movies():
    return """
    SELECT COUNT(*) FROM movies m
    LEFT JOIN actions a ON m.id = a.movie_id AND a.user_id = ?
    WHERE m.age_rating <= (
        SELECT strftime('%Y', 'now') - strftime('%Y', u.birth_date) - (
            strftime('%m-%d', 'now') < strftime('%m-%d', u.birth_date)
        )
        FROM users u WHERE u.user_id = ?
    ) AND a.movie_id IS NULL
    """

# Action-related queries
def insert_action():
    return """
    INSERT INTO actions (
        user_id, movie_id, 
        want_to_watch, rating
    ) VALUES (?, ?, ?, ?)
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