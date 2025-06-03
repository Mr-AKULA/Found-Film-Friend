import telebot
from telebot import types
import sqlite3
from datetime import datetime
import Settings
from use_def import * 
import random
from main import bot


# Проверка, существует ли пользователь в базе данных и указанали дата рождения. Если существует - возвращает TRUE. 
def def_user_exists(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(1) FROM users WHERE user_id = ? AND birth_date IS NOT NULL''', (user_id,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists

# Функция для получения имени пользователя по его user_id
def def_get_user_name(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute('''SELECT first_name FROM users WHERE user_id = ?''', (user_id,))
    user_name = cursor.fetchone()
    conn.close()
    return user_name[0] if user_name else None

# Функция для парсинга параметров реферальной ссылки
def def_parse_referral_params(args):
    params = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=')
            params[key] = value
    return params

# Функция для сохранения реферальной информации в базу данных
def def_save_referral_to_db(user_id, params):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    id_invite = params.get('id')
    id_film = params.get('film')
    id_list = params.get('group')
    from_ = params.get('from')

    cursor.execute('''
    INSERT INTO referal (id_user, id_invite, id_film, id_list, from_)
    VALUES (?, ?, ?, ?, ?)
    ''', (user_id, id_invite, id_film, id_list, from_))
    conn.commit()
    conn.close()








