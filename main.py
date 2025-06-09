import telebot
from telebot import types
import sqlite3
from datetime import datetime
import Settings
from use_def import * 
import random
import math
import sys

from Settings import *
from sql_queries import *  # Импортируем все SQL-запросы

import concurrent.futures
import functools
import time



API_TOKEN = Settings.token

bot = telebot.TeleBot(API_TOKEN)

#TODO Сделать выбор фильмов на основе приоритетов
#TODO Сделать список друзей(с возвожностью добавлять удалять)
#TODO Сделать списки фильмов с проверкой необходимости их отображения. Также сделать БД к информации у кого какие списки.
#TODO Сделать возможность поделиться фильмом (Ставя лайк или дизлайк)
#TODO Сделать настройку приоритетов (возможно отдельным кодом) ! Сделать, весовую категорию группы и списков. Т.е. чем чаще фильм входит в различные списки, тем больше у него приоритет. 
#TODO Просмотреть код, который отвечает за загрузку новых фильмов.
#TODO Логика переключения между выбором и просмотром фильмов.
#TODO Сделать возможность выбора человека (группы людей) для совместного просмотра фильма.
#TODO Вывод списка мест, где можно посмотреть фильм.
##TODO Если у пользователя закончились фильмы, то пользователю приходит уведомление об отсутствии фильмов. Нам приходит уведомление об отсутствии фильмов. 


# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

def power(x, y):
    return math.pow(x, y)

def update_last_activity(user_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute(update_last_activity_user(),
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()


def def_find_date_of_birth(message, send_message):
    send_message = f'{send_message}\nВведите вашу дату рождения в формате ДД.ММ.ГГГГ.'
    x = bot.send_message(message.chat.id, send_message)
    bot.register_next_step_handler(x, def_process_birth_date)


#Тайм-аут будет действовать индивидуально для каждого пользователя, так как каждый вызов функции movie_rating_handler обрабатывается независимо для каждого пользователя.
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


    
#Проверка, есть ли у пользователя дата рождения.    True - есть дата рождения.
def def_check_birthday(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute(get_user_birth_date(), (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return True
    else:
        return False
    

def get_random_movie(user_id, film=None):
    def clean_none(value):
        return value if value is not None else ""
    
    conn = sqlite3.connect('movies.db')
    if film is None:
        
        conn.create_function("POWER", 2, power)
        cursor = conn.cursor()

        # Сначала пробуем найти фильм без оценки
        cursor.execute(get_empty_movie_query(), (user_id, user_id))
        movie = cursor.fetchone()

        # Если не нашли, берем случайный
        if not movie:
            cursor.execute(get_random_movie_query(), (user_id, user_id))
            movie = cursor.fetchone()
        
        if movie:
            cleaned_movie = tuple(clean_none(value) for value in movie)
            return cleaned_movie, cleaned_movie[0]
        else:
            return None, "no_movies"
        
    else:
        cursor = conn.cursor()
        cursor.execute(get_specific_movie(), (film,user_id))
        movie = cursor.fetchone()
        conn.close()
        
        if movie:
            cleaned_movie = tuple(clean_none(value) for value in movie)
            return cleaned_movie, cleaned_movie[0]
        else:
            return None, None

def get_posters_movie(movie_id):
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute(get_movie_poster(), (movie_id,))
    poster = cursor.fetchone()
    conn.close()
    return poster[0] if poster else None

# Вспомогательная функция для получения информации о пользователе
def get_user_info(user_id):
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    cursor.execute(get_user_name(), (user_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        name, username = result
        return f"{name} (@{username})" if username else name
    return f"ID: {user_id}"


# Новая функция для уведомления админов
def notify_admins_no_movies(user_id):
    user_info = get_user_info(user_id)  # Нужно реализовать эту функцию
    message = f"⚠️ У пользователя {user_info} закончились фильмы для оценки!"
    
    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(admin_id, message)
        except Exception as e:
            print(f"Не удалось отправить уведомление админу {admin_id}: {e}")



# ошибка 888 в description_status - Слишком длинное описание
# ошибка 222 в description_status - Всё успешно
# ошибка 111 в description_status - Описание не найдено

def send_random_movie(message):
    try:
        user_id = message.from_user.id
        movie, movie_id = get_random_movie(user_id)


        if movie_id == "no_movies":
            bot.send_message(message.chat.id, "К сожалению, у нас закончились фильмы для вас. Мы уже работаем над добавлением новых!")
            # notify_admins_no_movies(user_id)
            return

        if movie:
            title, tagline, description, release_year = movie[1], movie[2], movie[3], movie[4]      
            # if tagline == None:
            preview_url = get_posters_movie(movie_id)
            # Определяем статус описания
            if description:
                if len(description) > 900:
                    description_status = 888  # Слишком длинное описание
                    short_description = description[:900] + "..."
                    movie_info = f"*{title}*\n*{tagline}*\n\n{short_description}\n\n*{release_year}*"
                else:
                    description_status = 222  # Успешно
                    movie_info = f"*{title}*\n*{tagline}*\n\n{description}\n\n*{release_year}*"
            else:
                description_status = 111  # Описание не найдено
                if tagline:
                    movie_info = f"*{title}*\n*{tagline}*\n\n*{release_year}*"
                else:
                    movie_info = f"*{title}*\n\n*{release_year}*"
            # print(title)
            # print(f"Preview URL: {preview_url}")  # Добавьте перед отправкой
            # Создание кнопок для оценки фильма
            markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
            btn_dislike = types.KeyboardButton('👎')
            btn_menu = types.KeyboardButton('📺')
            btn_like = types.KeyboardButton('👍')
            markup.add(btn_dislike, btn_menu, btn_like)

            # Сохраняем информациию об отправке фильма на оценку в базу данных
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()
            
            # Обновляем статус описания в таблице movies
            cursor.execute(update_movies_description_status(), (description_status, movie_id))
            
            cursor.execute(insert_action(), (user_id, movie_id, None, None))
            conn.commit()
            conn.close()

            if preview_url:
                # Отправляем изображение с подписью
                bot.send_photo(message.chat.id, preview_url, caption=movie_info, parse_mode='Markdown', reply_markup=markup)
            else:
                bot.send_message(message.chat.id, movie_info, parse_mode='Markdown', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Не удалось найти фильм для оценки.")
    
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при загрузке фильма")




#Обработка даты рождения пользователя   
def def_process_birth_date(message):

    user = message.from_user
    birth_date_str = message.text
    try:
        birth_date = datetime.strptime(birth_date_str, '%d.%m.%Y').date()
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

        conn = sqlite3.connect(Settings.file_bd)
        cursor = conn.cursor()
        cursor.execute(insert_user(),
                       (user_info['user_id'], user_info['first_name'], user_info.get('last_name'),
                        user_info.get('username'), user_info.get('language_code'), user_info['is_bot'],
                        user_info.get('birth_date'), user_info['registration_date'],
                        user_info['last_activity_date']))
        conn.commit()
        conn.close()

        bot.reply_to(message, "Спасибо! Теперь вы можете оценивать фильмы.")
        send_random_movie(message)
    except ValueError:
        bot.reply_to(message, "Некорректный формат даты рождения. Пожалуйста, укажите дату рождения в формате ДД.ММ.ГГГГ.")
        bot.register_next_step_handler(message, def_process_birth_date)


def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn_dislike = types.KeyboardButton('👎')
    btn_menu = types.KeyboardButton('📺')
    btn_like = types.KeyboardButton('👍')
    markup.add(btn_dislike, btn_menu, btn_like)
    return markup

# Кнопки для TV-меню
def get_tv_keyboard():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_back = types.KeyboardButton('🔙 Назад')
    btn_friends = types.KeyboardButton('👥 Друзья')
    markup.add(btn_back, btn_friends )
    return markup

# Обработчик кнопки 📺
# Глобальная переменная для хранения текущих страниц пользователей
user_pages = {}

@bot.message_handler(func=lambda message: message.text == '📺')
def handle_tv_button(message):
    try:
        user_id = message.from_user.id
        user_pages[user_id] = {'page': 0}  # Теперь это словарь с ключом 'page'  # Сбрасываем страницу при новом открытии
        
        # Меняем основную клавиатуру
        reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        reply_markup.add('👥 Друзья', '🔙 Назад')
        
        # Отправляем сообщение с клавиатурой (используем невидимый символ, если нужно)
        bot.send_message(
            message.chat.id,
            "⚡",  # Можно даже использовать "‎" (невидимый символ Unicode U+200E)⚡
            reply_markup=reply_markup
        )
        
        # Показываем первую страницу фильмов
        show_movies_page(message.chat.id, user_id)
        
    except Exception as e:
        print(f"Ошибка в handle_tv_button: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте позже.")
        
def show_movies_page(chat_id, user_id, page=0):
    try:
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        
        # Получаем все уникальные лайкнутые фильмы
        cursor.execute("""
            SELECT DISTINCT m.id, m.name 
            FROM movies m
            JOIN actions a ON m.id = a.movie_id 
            WHERE a.user_id = ? AND a.want_to_watch = 1
            ORDER BY m.name
        """, (user_id,))
        
        all_movies = cursor.fetchall()
        total_movies = len(all_movies)
        
        if total_movies == 0:
            bot.send_message(chat_id, "У вас пока нет лайкнутых фильмов.\nПоставьте 👍 хотя бы одному фильму.")
            return
        
        # Разбиваем на страницы
        movies_per_page = 5
        start_index = page * movies_per_page
        end_index = start_index + movies_per_page
        page_movies = all_movies[start_index:end_index]
        
        # Создаем инлайн-клавиатуру
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Добавляем кнопки фильмов
        for movie_id, movie_name in page_movies:
            markup.add(types.InlineKeyboardButton(
                text=f"{movie_name}",
                callback_data=f"movie_{movie_id}"
            ))
        
        # Добавляем кнопки пагинации
        pagination_buttons = []
        
        if page > 0:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="⬅️",
                callback_data=f"page_{page-1}"
            ))
        
        if end_index < total_movies:
            pagination_buttons.append(types.InlineKeyboardButton(
                text="➡️",
                callback_data=f"page_{page+1}"
            ))
        
        if pagination_buttons:
            markup.row(*pagination_buttons)
        
        # Всегда редактируем существующее сообщение
        try:
            if user_id in user_pages and 'message_id' in user_pages[user_id]:
                bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=user_pages[user_id]['message_id'],
                    text=f"Лайкнутые фильмы (всего {total_movies}):",
                    reply_markup=markup
                )
            else:
                # Если сообщения еще нет, создаем новое
                sent_message = bot.send_message(
                    chat_id,
                    f"Лайкнутые фильмы (всего {total_movies}):",
                    reply_markup=markup
                )
                # Сохраняем ID сообщения
                if user_id not in user_pages:
                    user_pages[user_id] = {}
                user_pages[user_id]['message_id'] = sent_message.message_id
                
        except Exception as e:
            print(f"Ошибка при редактировании сообщения: {e}")
            # Если не удалось отредактировать (например, сообщение устарело), создаем новое
            sent_message = bot.send_message(
                chat_id,
                f"🎬 Ваши лайкнутые фильмы (всего {total_movies}):",
                reply_markup=markup
            )
            user_pages[user_id]['message_id'] = sent_message.message_id
        
    except Exception as e:
        print(f"Ошибка в show_movies_page: {e}")
        bot.send_message(chat_id, "⚠️ Ошибка при загрузке фильмов")


@bot.callback_query_handler(func=lambda call: call.data.startswith('page_'))
def handle_page_change(call):
    try:
        user_id = call.from_user.id
        page = int(call.data.split('_')[1])
        user_pages[user_id]['page'] = page  # Теперь сохраняем в словарь
        
        show_movies_page(call.message.chat.id, user_id, page)
        bot.answer_callback_query(call.id)
    except:
        bot.answer_callback_query(call.id, "⚠️ Ошибка при переключении страницы")
   
# Обработчик кнопки Назад
@bot.message_handler(func=lambda message: message.text == '🔙 Назад')
def handle_back_button(message):
    try:
        send_random_movie(message)

    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка")

@timeout(2)  # Установливаем нужное количество секунд для тайм-аута
@bot.message_handler(func=lambda message: message.text in ['👎', '👍'])
def movie_rating_handler(message):
    user = message.from_user
    update_last_activity(user.id)  # Обновляем дату последней активности
    user_id = user.id
    
    try:
        # Сохраняем оценку в базе данных
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()

        # Извлекаем preview_url по movie_id
        cursor.execute(get_pending_actions(), (user_id,))
        actions = cursor.fetchall()
        conn.commit()
        conn.close()

        if actions:
            # Извлекаем первую запись из actions
            action = actions[0]
            user_id, movie_id, _, _ = action


            if message.text == '👎':
                # bot.reply_to(message, "Вы поставили отрицательную оценку.")
                want_to_watch = 0
            elif message.text == '👍':
                # bot.reply_to(message, "Вы поставили положительную оценку.")
                want_to_watch = 1

            # Сохраняем оценку в базе данных
            conn = sqlite3.connect('movies.db')
            cursor = conn.cursor()

            # Выполняем SQL-запрос для обновления данных
            cursor.execute(update_action_rating(), (want_to_watch, user_id, movie_id))
            conn.commit()
            conn.close()

            time.sleep(0.5)
            # Отправляем новый фильм на оценку
            send_random_movie(message)  # После оценки фильма отправляем следующий
        else:
            bot.reply_to(message, "Нет фильмов для оценки.")

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        time.sleep(1)
        bot.reply_to(message, "Произошла ошибка подождите и попробуйте снова.")



# # Обработчик команды /start
# @bot.message_handler(commands=['start'])
# def handle_start(message):
#     user_id = message.from_user.id
#     status_old_user = def_user_exists(user_id)
#     print(f'Пользователь {user_id} старый?  {status_old_user}')

#     # Парсинг параметров реферальной ссылки
#     start_command = message.text.split(' ', 1)
#     if len(start_command) > 1:
#         referral_params = def_parse_referral_params(start_command[1].split('_'))

#         #FIXME Если пользователь новый, то после указания даты рождения первым фильмом ему предлагается фильм, который посоветовали. 
#         if referral_params:
#             # Проверка наличия параметров
#             if 'id' in referral_params and 'film' in referral_params:
#                 user_name = def_get_user_name(referral_params["id"])                
#                 if status_old_user:
#                     print(1)
#                     bot.send_message(message.chat.id, f'{user_name} предлагает посмотреть фильм {referral_params["film"]}') #FIXME Добавить функцию подбора фильмов.
#                 else:
#                     #FIXME После ввода даты рождения уточнить подходит ли фильм по возрасту. 
#                     def_find_date_of_birth(message, f'{user_name} предлагает посмотреть фильм {referral_params["film"]}. Уточните ваш возраст для уточнения критериев фильма.')

#             elif 'group' in referral_params:                
#                 if status_old_user:
#                     bot.send_message(message.chat.id, f'Список {referral_params["group"]} добавлен в списки.') #FIXME Добавить функцию подбора фильмов.
#                 else:
#                     def_find_date_of_birth(message, f'Список {referral_params["group"]} добавлен в списки для оценки. Для продолжение, нам необходимо уточнить ваш возраст. ')
            
#             elif 'film' in referral_params:              
#                 if status_old_user:
#                     bot.send_message(message.chat.id, f'Вы хотели бы посмотреть фильм {referral_params["film"]}?')
#                     pass #FIXME Добавить функцию подбора фильмов.
#                 else:
#                     #FIXME После ввода даты рождения уточнить подходит ли фильм по возрасту. 
#                     def_find_date_of_birth(message, f'Мы знаем, что вы хотели бы оценить фильм {referral_params["film"]}, но ответьте на один вопрос... ')
            
#             elif 'id' in referral_params:
#                 user_name = def_get_user_name(referral_params["id"])
#                 bot.send_message(message.chat.id, f'Добавим {user_name} в друзья?')
#                 #FIXME После ответа пользователя уточнять наличие даты рождения.
            
#             else:
#                 pass
#                 #bot.send_message(message.chat.id, '1')

#             def_save_referral_to_db(user_id, referral_params)
#         else:
#             bot.send_message(message.chat.id, '1')
#     else:
#         if status_old_user:
#             bot.send_message(message.chat.id, 'Давай выберем фильм?')
#             send_random_movie(message)
#         else:
#         #FIXME Сделать проверку на регистрацию пользователя. (Возможно пользователь зарегистрирован и ему не нужно указывать дату рождения.)
#             def_find_date_of_birth(message, f'Привет! Ты попал в бота для оценки фильмов. Нам необходимо знать твой возраст для корректного подбора фильмов для тебя.')
#         #bot.send_message(message.chat.id, 'Давай выберем фильм?')
#     #bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}!')

def film_name_fankhon(film_id): 
    """Получает название фильма по его ID"""
    # Получаем информацию о фильме из базы
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM movies WHERE id = ?", (film_id,))
    film_data = cursor.fetchone()
    conn.close()
    
    return film_data[0] if film_data else f"фильм (ID: {film_id})"


@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    status_old_user = def_user_exists(user_id)
    print(f'Пользователь {user_id} старый? {status_old_user}')

    # Парсинг параметров реферальной ссылки
    start_command = message.text.split(' ', 1)
    referral_params = {}
    
    if len(start_command) > 1:
        referral_params = def_parse_referral_params(start_command[1].split('_'))
        def_save_referral_to_db(user_id, referral_params)

    # Обработка разных сценариев в зависимости от параметров
    if referral_params:
        # Сценарий 1: Пришел с реферальной ссылкой с фильмом и пользователем
        if 'id' in referral_params and 'film' in referral_params:
            user_name = def_get_user_name(referral_params["id"])           
            film_id = referral_params["film"]
            film_name = film_name_fankhon(film_id)
            
            
            if status_old_user:
                movie, _ = get_random_movie(user_id, film_id)  # Ищем по ID
                if movie:
                    send_specific_movie(message, movie)
                else:
                    bot.send_message(
                        message.chat.id,
                        f'Фильм "{film_name}" не найден или не доступен по возрасту. Предлагаем другой фильм.'
                    )
                    send_random_movie(message)
            else:
                def_find_date_of_birth(
                    message,
                    f'Вы хотели бы оценить фильм "{film_name}". '
                    'Укажите вашу дату рождения для проверки возрастных ограничений.'
                    'После регестрации перйдите по ссылке ещё раз.'
                )

        # Сценарий 2: Пришел с группой фильмов
        elif 'group' in referral_params:
            group_name = referral_params["group"]
            # Сохраняем группу для пользователя
            # save_user_group(user_id, group_name)
            
            # if status_old_user:
            #     bot.send_message(
            #         message.chat.id,
            #         f'Список "{group_name}" добавлен в ваши списки. Теперь мы будем учитывать эти фильмы при подборе.'
            #     )
            #     send_random_movie(message)
            # else:
            #     def_find_date_of_birth(
            #         message,
            #         f'Список "{group_name}" добавлен в ваши списки. '
            #         'Перед началом укажите вашу дату рождения для корректного подбора фильмов.'
            #     )
            pass

        # Сценарий 3: Только фильм в ссылке
        elif 'film' in referral_params:
            film_id = referral_params["film"]
            film_name = film_name_fankhon(film_id)
            
            if status_old_user:
                movie, _ = get_random_movie(user_id, film_id)  # Ищем по ID
                if movie:
                    send_specific_movie(message, movie)
                else:
                    bot.send_message(
                        message.chat.id,
                        f'Фильм "{film_name}" не найден. Предлагаем другой фильм.'
                    )
                    send_random_movie(message)
            else:
                def_find_date_of_birth(
                    message,
                    f'Вы хотели бы оценить фильм "{film_name}". '
                    'Укажите вашу дату рождения для проверки возрастных ограничений.'
                )

        # Сценарий 4: Только ID пользователя в ссылке
        elif 'id' in referral_params:
            referred_user_id = referral_params["id"]
            user_name = def_get_user_name(referred_user_id)
            
            # Предлагаем добавить в друзья
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Добавить в друзья", callback_data=f"add_friend_{referred_user_id}"),
                types.InlineKeyboardButton("Отказаться", callback_data="skip_friend")
            )
            
            bot.send_message(
                message.chat.id,
                f'Хотите добавить {user_name} в друзья?',
                reply_markup=markup
            )
            
            if not status_old_user:
                def_find_date_of_birth(
                    message,
                    'Перед продолжением укажите вашу дату рождения.'
                )

    # Сценарий 5: Обычный старт без параметров
    else:
        if status_old_user:
            bot.send_message(
                message.chat.id,
                'Давай выберем фильм?',
                reply_markup=get_main_keyboard()
            )
            send_random_movie(message)
        else:
            # Проверка выполнения
            def_find_date_of_birth(
                message,
                    'Укажите вашу дату рождения для проверки возрастных ограничений.'
                )


def send_specific_movie(message, movie):
    """Отправляет конкретный фильм пользователю"""
    title, tagline, description, release_year = movie[1], movie[2], movie[3], movie[4]
    preview_url = get_posters_movie(movie[0])
    
    movie_info = f"*{title}*\n"
    if tagline:
        movie_info += f"*{tagline}*\n\n"
    if description:
        movie_info += f"{description}\n\n"
    movie_info += f"*{release_year}*"
    
    if preview_url:
        bot.send_photo(
            message.chat.id,
            preview_url,
            caption=movie_info,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            movie_info,
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
    
    # Сохраняем информацию о показе
    conn = sqlite3.connect('movies.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO actions (user_id, movie_id) VALUES (?, ?)",
        (message.from_user.id, movie[0])
    )
    conn.commit()
    conn.close()

# Добавляем обработчик команды /stats для админов
@bot.message_handler(commands=['stats'])
def handle_stats(message):
    if message.from_user.id not in ADMIN_IDS:
        bot.reply_to(message, "Эта команда доступна только администраторам")
        return
        
    conn = sqlite3.connect(Settings.file_bd)
    cursor = conn.cursor()
    
    # Получаем статистику по пользователям без фильмов
    cursor.execute(get_users_without_movies())
    users_without_movies = cursor.fetchall()
    conn.close()
    
    if users_without_movies:
        response = "Пользователи без доступных фильмов:\n"
        for user_id, count in users_without_movies:
            response += f"- {get_user_info(user_id)}\n"
    else:
        response = "Все пользователи имеют доступные фильмы для оценки."
    
    bot.reply_to(message, response)


if __name__ == '__main__':

    bot.polling(none_stop=True)

