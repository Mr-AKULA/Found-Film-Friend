import telebot
from telebot import types
import sqlite3
from datetime import datetime
import Settings
from use_def import * 
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
#TODO Если у пользователя закончились фильмы, то пользователю приходит уведомление об отсутствии фильмов. Нам приходит уведомление об отсутствии фильмов. 

#TODO Все SQL - запросы в отдельном файле. 

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

def def_find_date_of_birth(message, send_message):
    send_message = f'{send_message}\nВведите вашу дату рождения в формате ДД.ММ.ГГГГ.'
    x = bot.send_message(message.chat.id, send_message)
    bot.register_next_step_handler(x, def_process_birth_date)

    
#Проверка, есть ли у пользователя дата рождения.    True - есть дата рождения.
def def_check_birthday(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute("SELECT birth_date FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return True
    else:
        return False
    

#FIXME Добавить функцию отправки фильма
def get_random_movie(user_id, film = None):
    if film == None:
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
    else:
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
    WHERE m.movie_id = ?;
    '''

        cursor.execute(query, (film))
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

#Обработка даты рождения пользователя   
def def_process_birth_date(message):
    user = message.from_user
    birth_date_str = message.text
    try:
        birth_date = datetime.strptime(birth_date_str, '%d.%m.%Y').date()
        user = message.from_user
        user_info = {
        'user_id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'username': user.username,
        'language_code': user.language_code,
        'is_bot': user.is_bot,
        'birth_date': birth_date,
        'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'last_activity_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
        # Сохраняем информацию о пользователе в БД.
        conn = sqlite3.connect(Settings.file_bd)
        cursor = conn.cursor()
        #TODO Сделать аккаунт открытым или закрытым.
        cursor.execute('''INSERT INTO users
                          (user_id, first_name, last_name, username, language_code, is_bot, birth_date, registration_date, last_activity_date)
                          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (user_info['user_id'], user_info['first_name'], user_info.get('last_name'), user_info.get('username'),
                        user_info.get('language_code'), user_info['is_bot'], user_info.get('birth_date'),
                        user_info['registration_date'], user_info['last_activity_date']))
        conn.commit()
        conn.close()
        # Продолжаем работу бота
        #FIXME Если пользователь пришел по реферальной ссылке, то первым предложить определённый фильм.
        bot.reply_to(message, f"Спасибо! Теперь вы можете оценивать фильмы.")
        send_random_movie(message)
    except ValueError:
        # Если дата рождения введена некорректно, запрашиваем ее снова
        bot.reply_to(message, "Некорректный формат даты рождения. Пожалуйста, укажите дату рождения в формате ДД.ММ.ГГГГ.")
        bot.register_next_step_handler(message, def_process_birth_date)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    status_old_user = def_user_exists(user_id)
    print(f'Пользователь {user_id} старый?  {status_old_user}')

    # Парсинг параметров реферальной ссылки
    start_command = message.text.split(' ', 1)
    if len(start_command) > 1:
        referral_params = def_parse_referral_params(start_command[1].split('_'))

        #FIXME Если пользователь новый, то после указания даты рождения первым фильмом ему предлагается фильм, который посоветовали. 
        if referral_params:
            # Проверка наличия параметров
            if 'id' in referral_params and 'film' in referral_params:
                user_name = def_get_user_name(referral_params["id"])                
                if status_old_user:
                    print(1)
                    bot.send_message(message.chat.id, f'{user_name} предлагает посмотреть фильм {referral_params["film"]}') #FIXME Добавить функцию подбора фильмов.
                else:
                    #FIXME После ввода даты рождения уточнить подходит ли фильм по возрасту. 
                    def_find_date_of_birth(message, f'{user_name} предлагает посмотреть фильм {referral_params["film"]}. Уточните ваш возраст для уточнения критериев фильма.')

            elif 'group' in referral_params:                
                if status_old_user:
                    bot.send_message(message.chat.id, f'Список {referral_params["group"]} добавлен в списки.') #FIXME Добавить функцию подбора фильмов.
                else:
                    def_find_date_of_birth(message, f'Список {referral_params["group"]} добавлен в списки для оценки. Для продолжение, нам необходимо уточнить ваш возраст. ')
            
            elif 'film' in referral_params:              
                if status_old_user:
                    bot.send_message(message.chat.id, f'Вы хотели бы посмотреть фильм {referral_params["film"]}?')
                    pass #FIXME Добавить функцию подбора фильмов.
                else:
                    #FIXME После ввода даты рождения уточнить подходит ли фильм по возрасту. 
                    def_find_date_of_birth(message, f'Мы знаем, что вы хотели бы оценить фильм {referral_params["film"]}, но ответьте на один вопрос... ')
            
            elif 'id' in referral_params:
                user_name = def_get_user_name(referral_params["id"])
                bot.send_message(message.chat.id, f'Добавим {user_name} в друзья?')
                #FIXME После ответа пользователя уточнять наличие даты рождения.
            
            else:
                pass
                #bot.send_message(message.chat.id, '1')

            def_save_referral_to_db(user_id, referral_params)
        else:
            bot.send_message(message.chat.id, '1')
    else:
        if status_old_user:
            bot.send_message(message.chat.id, 'Давай выберем фильм?')
            send_random_movie(message)
        else:
        #FIXME Сделать проверку на регистрацию пользователя. (Возможно пользователь зарегистрирован и ему не нужно указывать дату рождения.)
            def_find_date_of_birth(message, f'Привет! Ты попал в бота для оценки фильмов. Нам необходимо знать твой возраст для корректного подбора фильмов для тебя.')
        #bot.send_message(message.chat.id, 'Давай выберем фильм?')
    #bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

if __name__ == '__main__':

    bot.polling(none_stop=True)