# import loguru
# from datetime import datetime
#
# # Формат повідомлення для виводу в консоль та файл
# logger = loguru.logger
# logger.add(
#     sink="log\\tcp_retranslator.log",
#     enqueue=True,
#     rotation="1 day",
#     retention="1 week",
#     encoding="utf-8",
#     backtrace=True,
#     diagnose=True,
# )


import logging.handlers
import datetime
import os
import sys
import colorlog

today_date_str = datetime.datetime.now().strftime("%Y-%m-%d")

if not os.path.exists("logs"):
    os.mkdir("logs")

if os.path.isfile("logs\\retranslator.log"):
    os.rename("logs\\retranslator.log", f"logs/tcp_retranslator-{today_date_str}.log")

# Встановлення рівня логування
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Створення об'єкту форматування
console_formatter = colorlog.ColoredFormatter(
    "%(green)s%(asctime)s%(reset)s | %(log_color)s%(levelname)s%(reset)s | "
    "%(cyan)s%(name)s:%(funcName)s:%(lineno)ds%(reset)s  - %(log_color)s%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "white",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)

file_formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
)

# Створення об'єкту обробника логів для виводу на консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(console_formatter)

# Створення об'єкту обробника логів для зберігання у файлі
# Приклад імені файлу: app-2023-05-15.log.gz
today_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
log_filename = f"logs/tcp_retranslator.log"
file_handler = logging.handlers.RotatingFileHandler(
    filename=log_filename, maxBytes=9437184, backupCount=20, mode="w", encoding="utf8"
)

file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(file_formatter)

# Додавання обробників логів до логера
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logging.getLogger("sqlite3").setLevel(logging.DEBUG)
logging.getLogger("aiosqlite").setLevel(logging.DEBUG)
