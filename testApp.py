import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackContext

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "838027846:AAGi6CMoue6RCXU5ENySylykoaEmlR8RPVg"
WEB_APP_URL = "https://vnyzaica.github.io/"  # URL вашего Mini App

async def start(update: Update, context: CallbackContext) -> None:
    # Создаем кнопку для открытия Mini App
    keyboard = [
        [InlineKeyboardButton(
            "Открыть Mini App",
            web_app=WebAppInfo(url=WEB_APP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Нажмите кнопку ниже, чтобы открыть Mini App:",
        reply_markup=reply_markup
    )

def main() -> None:
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.run_polling()

if __name__ == "__main__":
    main()