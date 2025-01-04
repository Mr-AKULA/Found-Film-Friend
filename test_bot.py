import Settings

API_TOKEN = Settings.token
import telebot
from urllib.parse import parse_qs

import telebot


bot = telebot.TeleBot(API_TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Получаем параметры из команды /start
    args = message.text.split(' ', 1)[1] if len(message.text.split(' ', 1)) > 1 else ''
    if args:
        params = args.split('_')
        result = {}
        for param in params:
            key, value = param.split('=')
            result[key] = value

        # Формируем ответное сообщение
        response = "\n".join([f"{key} - {value}" for key, value in result.items()])
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Привет! Пожалуйста, используйте ссылку с параметрами.")

# Запускаем бота
if __name__ == '__main__':
    bot.polling()

