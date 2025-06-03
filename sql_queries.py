import sqlite3
from datetime import datetime
import math

def power(x, y):
    return math.pow(x, y)

def check_user_exists(user_id):
    return """SELECT 1 FROM users WHERE user_id = ?"""

def get_user_birth_date(user_id):
    return """SELECT birth_date FROM users WHERE user_id = ?"""

def insert_user():
    return """INSERT INTO users
              (user_id, first_name, last_name, username, language_code, is_bot, birth_date, registration_date, last_activity_date)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""

def get_random_movie_query():
    return """
    SELECT
        m.id,
        m.name,
        m.slogan,
        m.description,
        m.year,
        m.priority
    FROM
        movies m
    LEFT JOIN
        actions a ON m.id = a.movie_id AND a.user_id = ?
    WHERE
        m.age_rating <= (
            SELECT
                strftime('%Y', 'now') - strftime('%Y', u.birth_date) - (
                    strftime('%m-%d', 'now') < strftime('%m-%d', u.birth_date)
                )
            FROM
                users u
            WHERE
                u.user_id = ?
        )
        AND a.movie_id IS NULL
    ORDER BY
        RANDOM() * POWER(10, m.priority) DESC
    LIMIT 1;
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
    FROM
        movies m
    WHERE m.id = ?;
    """

def get_movie_poster():
    return """SELECT preview_url FROM posters WHERE movie_id = ?"""

def insert_action():
    return """INSERT INTO actions
              (user_id, movie_id, want_to_watch, rating)
              VALUES (?, ?, ?, ?)"""

def get_user_name():
    return """SELECT first_name FROM users WHERE user_id = ?"""