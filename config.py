import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВЬ_СЮДА_ТОКЕН")

# Алфавит для кода комнаты (без 0/O, 1/I/L)
ROOM_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
ROOM_CODE_LENGTH = 6

# Автоочистка
REPORT_TTL_HOURS = 48
REMINDER_MINUTES_DEFAULT = 15

DB_PATH = "bot.db"
