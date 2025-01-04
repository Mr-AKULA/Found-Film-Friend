import telebot
from telebot import types
import sqlite3
from datetime import datetime
import Settings
import random

API_TOKEN = Settings.token

#TODO Сделать выбор фильмов на основе приоритетов
#TODO Сделать ввод даты рождения
#TODO Сделать список друзей(с возвожностью добавлять удалять)
#TODO Сделать списки фильмов с проверкой необходимости их отображения. Также сделать БД к информации у кого какие списки.
#TODO Сделать возможность поделиться фильмом (Ставя лайк или дизлайк)
#TODO Сделать настройку приоритетов (возможно отдельным кодом) ! Сделать, весовую категорию группы и списков. Т.е. чем чаще фильм входит в различные списки, тем больше у него приоритет. 
#TODO Просмотреть код, который отвечает за загрузку новых фильмов.
#TODO Логика переключения между выбором и просмотром фильмов.
#TODO Сделать возможность выбора человека (группы людей) для совместного просмотра фильма.
#TODO Вывод списка мест, где можно посмотреть фильм.


# Проверка, существует ли пользователь в базе данных
def user_exists(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(1) FROM users WHERE user_id = ?''', (user_id,))
    exists = cursor.fetchone()[0] > 0
    conn.close()
    return exists

# Функция для получения имени пользователя по его user_id
def get_user_name(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute('''SELECT first_name FROM users WHERE user_id = ?''', (user_id,))
    user_name = cursor.fetchone()
    conn.close()
    return user_name[0] if user_name else None

# Функция для парсинга параметров реферальной ссылки
def parse_referral_params(args):
    params = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=')
            params[key] = value
    return params

# Функция для сохранения реферальной информации в базу данных
def save_referral_to_db(user_id, params):
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

# Функция для получения рефералов из базы данных
def get_referrals_from_db(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM referal WHERE id_invite = ?', (user_id,))
    referrals = cursor.fetchall()
    conn.close()
    return referrals

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if not user_exists(user_id):
        # Регистрация нового пользователя
        #TODO ДОбавлять всю необходимую информацию о пользователе.
        conn = sqlite3.connect(Settings.file_bd)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (user_id, username) VALUES (?, ?)''', (user_id, message.from_user.username))
        conn.commit()
        conn.close()

    # Парсинг параметров реферальной ссылки
    start_command = message.text.split(' ', 1)
    if len(start_command) > 1:
        referral_params = parse_referral_params(start_command[1].split('_'))
        #TODO Сделать проверку на наличие пользователя у нас в БД для ввода даты рождения.
        if referral_params:
            # Проверка наличия параметров
            if 'id' in referral_params and 'film' in referral_params:
                user_name = get_user_name(referral_params["id"])
                bot.send_message(message.chat.id, f'{user_name} предлагает посмотреть фильм {referral_params["film"]}')
            elif 'group' in referral_params:
                bot.send_message(message.chat.id, f'Список {referral_params["group"]} добавлен в списки.')
            elif 'film' in referral_params:
                bot.send_message(message.chat.id, f'Вы хотели бы посмотреть фильм {referral_params["film"]}?')
            elif 'id' in referral_params:
                user_name = get_user_name(referral_params["id"])
                bot.send_message(message.chat.id, f'Добавим {user_name} в друзья?')
            else:
                pass
                #bot.send_message(message.chat.id, '1')

            save_referral_to_db(user_id, referral_params)
        else:
            bot.send_message(message.chat.id, '1')
    else:
        bot.send_message(message.chat.id, 'Давай выберем фильм?')
    #bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

if __name__ == '__main__':

    bot.polling(none_stop=True)
