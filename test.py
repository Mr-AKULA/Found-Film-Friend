# main.py
import telebot
from telebot import types
import sqlite3
from datetime import datetime
import random
import Settings
from db_helper import update_last_activity, user_exists, save_user_info, get_random_movie, get_posters_movie,update_action

API_TOKEN = Settings.token
bot = telebot.TeleBot(API_TOKEN)



def send_random_movie(message):
    user_id = message.from_user.id
    movie, movie_id = get_random_movie(user_id)
    if movie:
        title, tagline, description, release_year = movie[1], movie[2], movie[3], movie[4]
        preview_url = get_posters_movie(movie_id)

        # Формируем сообщение в зависимости от наличия описания и preview_url
        if description:
            movie_info = f"*{title}*\n*{tagline}*\n\n{description}\n\n*{release_year}*"
        elif tagline:
            movie_info = f"*{title}*\n*{tagline}*\n\n*{release_year}*"
        else:
            movie_info = f"*{title}*\n\n*{release_year}*"

        # Создание кнопок для оценки фильма
        markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
        btn_dislike = types.KeyboardButton('👎')
        btn_menu = types.KeyboardButton('📺')
        btn_like = types.KeyboardButton('👍')
        markup.add(btn_dislike, btn_menu, btn_like)

        # Сохраняем информациию об отправке фильма на оценку в базу данных
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()

        cursor.execute('''INSERT INTO actions
                        (user_id, movie_id, want_to_watch, rating)
                        VALUES (?, ?, ?, ?)''',
                    (user_id, movie_id, None, None))

        conn.commit()
        conn.close()

        if preview_url:
            # Отправляем изображение с подписью
            bot.send_photo(message.chat.id, preview_url, caption=movie_info, parse_mode='Markdown', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, movie_info, parse_mode='Markdown', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Не удалось найти фильм для оценки.")

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

@bot.message_handler(func=lambda message: message.text in ['👎', '👍'])
def movie_rating_handler(message):
    user = message.from_user
    update_last_activity(user.id)  # Обновляем дату последней активности
    user_id = user.id
    # Сохраняем оценку в базе данных
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()

    # Извлекаем preview_url по movie_id
    cursor.execute('''SELECT user_id, movie_id, want_to_watch, rating FROM actions WHERE user_id = ? AND want_to_watch IS NULL''', (user_id,))
    actions = cursor.fetchall()
    conn.commit()
    conn.close()

    if actions:
        # Извлекаем первую запись из actions
        action = actions[0]
        user_id, movie_id, _, _ = action

        if message.text == '👎':
            bot.reply_to(message, "Вы поставили отрицательную оценку.")
            want_to_watch = 0
        elif message.text == '👍':
            bot.reply_to(message, "Вы поставили положительную оценку.")
            want_to_watch = 1

        # Сохраняем оценку в базе данных
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()

        # Выполняем SQL-запрос для обновления данных
        cursor.execute('''UPDATE actions SET want_to_watch = ? WHERE user_id = ? AND movie_id = ?''', (want_to_watch, user_id, movie_id))

        # Сохраняем изменения
        conn.commit()

        # Закрываем соединение с базой данных
        conn.close()

        # Отправляем новый фильм на оценку
        send_random_movie(message)  # После оценки фильма отправляем следующий
    else:
        bot.reply_to(message, "Нет фильмов для оценки.")


@bot.message_handler(func=lambda message: message.text not in ['👎', '📺', '👍'])
def handle_incorrect_input(message):
    bot.reply_to(message, "Некорректный ввод. Пожалуйста, используйте кнопки для оценки фильма.")

if __name__ == '__main__':
    bot.polling(none_stop=True)
