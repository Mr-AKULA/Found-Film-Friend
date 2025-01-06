# db_helper.py
import sqlite3
from datetime import datetime
import random

def calculate_age(birth_date_str):
    birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
    today = datetime.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age



def update_last_activity(user_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE users
                      SET last_activity_date = ?
                      WHERE user_id = ?''',
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

def user_exists(user_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(1) FROM users WHERE user_id = ?''', (user_id,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists

def save_user_info(user_info):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    if user_exists(user_info['user_id']):
        cursor.execute('''UPDATE users
                          SET first_name = ?, last_name = ?, username = ?, language_code = ?, is_bot = ?, birth_date = ?, last_activity_date = ?
                          WHERE user_id = ?''',
                       (user_info['first_name'], user_info.get('last_name'), user_info.get('username'),
                        user_info.get('language_code'), user_info['is_bot'], user_info.get('birth_date'),
                        user_info['last_activity_date'], user_info['user_id']))
    else:
        cursor.execute('''INSERT INTO users
                          (user_id, first_name, last_name, username, language_code, is_bot, birth_date, registration_date, last_activity_date)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (user_info['user_id'], user_info['first_name'], user_info.get('last_name'), user_info.get('username'),
                        user_info.get('language_code'), user_info['is_bot'], user_info.get('birth_date'),
                        user_info['registration_date'], user_info['last_activity_date']))
    conn.commit()
    conn.close()

def get_random_movie(user_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    query = '''
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
    '''

    cursor.execute(query, (user_id, user_id))
    movie = cursor.fetchone()
    conn.close()

    if movie:
        return movie, movie[0]
    else:
        return None, None

def get_posters_movie(movie_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    # Извлекаем preview_url по movie_id
    cursor.execute('''SELECT preview_url FROM posters WHERE movie_id = ?''', (movie_id,))
    poster = cursor.fetchone()
    conn.close()

    if poster:
        return poster[0]
    else:
        return None


def update_action(user_id, movie_id, want_to_watch, rating):
    # Устанавливаем соединение с базой данных
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    # Выполняем SQL-запрос для обновления данных
    cursor.execute('''UPDATE actions
                      SET user_id = ?, movie_id = ?, want_to_watch = ?, rating = ?
                      WHERE movie_id = ?''',
                   (user_id, movie_id, want_to_watch, rating, movie_id))

    # Сохраняем изменения
    conn.commit()

    # Закрываем соединение с базой данных
    conn.close()