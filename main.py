import telebot
from telebot import types
import sqlite3
from datetime import datetime
import Settings
import random

API_TOKEN = Settings.token


bot = telebot.TeleBot(API_TOKEN)