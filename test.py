import telebot
from telebot import types
import sqlite3
from datetime import datetime
import Settings
import random

API_TOKEN = Settings.token

bot = telebot.TeleBot(API_TOKEN)

# Проверка, существует ли пользователь в базе данных
def user_exists(user_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(1) FROM users WHERE user_id = ?''', (user_id,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists

# Сохранение информации о пользователе в базу данных
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

# Обновление даты последней активности пользователя
def update_last_activity(user_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('''UPDATE users 
                      SET last_activity_date = ? 
                      WHERE user_id = ?''',
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()

# Получение случайного фильма из базы данных
def get_random_movie():
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT name, slogan, description, year FROM movies ORDER BY RANDOM() LIMIT 1''')
    movie = cursor.fetchone()
    conn.close()
    return movie

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    user_info = {
        'user_id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'language_code': user.language_code,
        'is_bot': user.is_bot,
        'birth_date': None,
        'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_activity_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    if user_exists(user.id):
        # Если пользователь уже существует, обновляем только дату последней активности
        update_last_activity(user.id)
    else:
        # Если пользователь новый, сохраняем всю информацию
        save_user_info(user_info)
    
    bot.reply_to(message, f"Привет, {user.first_name}! Добро пожаловать в наш бот для оценки фильмов.")
    send_random_movie(message)

# Отправка случайного фильма для оценки
def send_random_movie(message):
    movie = get_random_movie()
    if movie:
        title, tagline, description, release_year = movie

        # Создание кнопок для оценки фильма
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        btn_dislike = types.KeyboardButton('👎')
        btn_menu = types.KeyboardButton('📺')
        btn_like = types.KeyboardButton('👍')
        markup.add(btn_dislike, btn_menu, btn_like)

        bot.send_message(message.chat.id, f"*{title}*\n*{tagline}*\n\n{description}\n\n*{release_year}*", parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Не удалось найти фильм для оценки.")

# Обработчики для кнопок оценки фильма
@bot.message_handler(func=lambda message: message.text in ['👎', '📺', '👍'])
def movie_rating_handler(message):
    user = message.from_user
    update_last_activity(user.id)  # Обновляем дату последней активности
    if message.text == '👎':
        bot.reply_to(message, "Вы поставили отрицательную оценку.")
    elif message.text == '👍':
        bot.reply_to(message, "Вы поставили положительную оценку.")
    elif message.text == '📺':
        bot.reply_to(message, "Вы решили посмотреть этот фильм.")
    
    send_random_movie(message)  # После оценки фильма отправляем следующий

# Обработчик некорректного ввода
@bot.message_handler(func=lambda message: message.text not in ['👎', '📺', '👍'])
def handle_incorrect_input(message):
    bot.reply_to(message, "Некорректный ввод. Пожалуйста, используйте кнопки для оценки фильма.")

if __name__ == '__main__':
    bot.polling(none_stop=True)
