from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан. Создайте файл .env с BOT_TOKEN=...")

ROOM_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
ROOM_CODE_LENGTH = 6

REPORT_TTL_HOURS = 48
REMINDER_MINUTES_DEFAULT = 15

DB_PATH = "bot.db"
