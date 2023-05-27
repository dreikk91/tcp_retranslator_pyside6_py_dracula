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

# import logging
#
# # Створення logger
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
#
# # Створення handler для виводу в консоль
# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.DEBUG)
#
# # Створення форматеру
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
# # Додавання форматеру до handler
# console_handler.setFormatter(formatter)
#
# # Додавання handler до logger
# logger.addHandler(console_handler)

# import logging
# import logging.handlers
# import sys
#
# # Створюємо логгер з назвою "my_logger"
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
#
# # Створюємо об'єкт форматування записів
# formatter = logging.Formatter(
#     "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
#     datefmt="%Y-%m-%d %H:%M:%S"
# )
#
# # Створюємо об'єкт обробника для запису в консоль
# console_handler = logging.StreamHandler(sys.stdout)
# console_handler.setFormatter(formatter)
# console_handler.setLevel(logging.DEBUG)
#
# # Створюємо об'єкт обробника для запису на диск
# file_handler = logging.handlers.TimedRotatingFileHandler(
#     filename="my_log_file.log",
#     when="D",
#     backupCount=7,
#     encoding="utf-8"
# )
# file_handler.setFormatter(formatter)
# file_handler.setLevel(logging.DEBUG)
#
# # Додаємо обробники до логгера
# logger.addHandler(console_handler)
# logger.addHandler(file_handler)
#
# # Додатково налаштовуємо кольори для повідомлень в консолі
# class ColorizingStreamHandler(logging.StreamHandler):
#     COLORS = {
#         logging.DEBUG: "\033[0;34m",  # blue
#         logging.INFO: "\033[0m",  # default (white)
#         logging.WARNING: "\033[0;33m",  # yellow
#         logging.ERROR: "\033[0;31m",  # red
#         logging.CRITICAL: "\033[1;31m",  # bright red
#     }
#
#     def __init__(self, stream=None):
#         logging.StreamHandler.__init__(self, stream)
#
#     def emit(self, record):
#         try:
#             self.stream.write(
#                 self.COLORS[record.levelno] + record.getMessage() + "\033[0m\n"
#             )
#             self.flush()
#         except (ValueError, TypeError):
#             self.handleError(record)
#
# console_handler = ColorizingStreamHandler(sys.stdout)
# console_handler.setFormatter(formatter)
# console_handler.setLevel(logging.DEBUG)
# logger.addHandler(console_handler)

# import logging
# import logging.config
# import logging.handlers
# import sys
# import os
# from datetime import datetime
#
# log_dir = 'logs'
#
# if not os.path.exists(log_dir):
#     os.makedirs(log_dir)
#
# log_file = os.path.join(log_dir, datetime.now().strftime('%Y-%m-%d.log'))
#
# logging_config = {
#     'version': 1,
#     'formatters': {
#         'console': {
#             'format': '%(asctime)s | %(levelname)-8s | %(message)s',
#             'datefmt': '%Y-%m-%d %H:%M:%S',
#         },
#         'file': {
#             'format': '%(asctime)s | %(levelname)-8s | %(message)s',
#             'datefmt': '%Y-%m-%d %H:%M:%S',
#         },
#     },
#     'handlers': {
#         'console': {
#             'class': 'logging.StreamHandler',
#             'level': 'DEBUG',
#             'formatter': 'console',
#             'stream': sys.stdout,
#         },
#         'file': {
#             'class': 'logging.handlers.TimedRotatingFileHandler',
#             'level': 'DEBUG',
#             'formatter': 'file',
#             'filename': log_file,
#             'when': 'midnight',
#             'backupCount': 30,
#         },
#     },
#     'loggers': {
#         'sqlite3': {
#             'level': 'WARNING',
#             'handlers': ['console'],
#             'propagate': False,
#         },
#     },
#     "sqlite3": {"level": "INFO"},
#     'root': {
#         'level': 'DEBUG',
#         'handlers': ['console', 'file'],
#     },
#     'disable_existing_loggers': False,
# }
#
# logging.config.dictConfig(logging_config)
#
# # Example usage
# logger = logging.getLogger(__name__)
# logger.debug('Debug message')
# logger.info('Info message')
# logger.warning('Warning message')
# logger.error('Error message')
# logger.critical('Critical message')
#

# import logging
# import logging.handlers
# import sys
# import os
# import zipfile
# from datetime import datetime
#
# # створення форматувальника
# formatter = logging.Formatter('%(asctime)s | %(levelname)s    | %(name)s:%(funcName)s:%(lineno)d - %(message)s')
#
# # створення об'єкту logger
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
#
# # створення об'єкту handler для запису у файл
# if not os.path.exists('logs'):
#     os.mkdir('logs')
# file_handler = logging.handlers.TimedRotatingFileHandler(
#     'logs/tcp_retranslator.log',
#     when='midnight',
#     interval=1,
#     backupCount=7,
#     encoding='utf-8'
# )
# file_handler.setLevel(logging.DEBUG)
# file_handler.setFormatter(formatter)
#
# # додавання компресії файлу журналу та його перейменування
# def compress_and_rotate(source, dest):
#     file_handler_rotator(source, dest)
#     with open(dest, 'rb') as f_in:
#         with zipfile.ZipFile(dest + '.zip', 'w', zipfile.ZIP_DEFLATED) as f_out:
#             f_out.write(dest)
#     os.remove(dest)
#
# def rename_and_rotate(source, dest):
#     file_handler_rotator(source, dest)
#     now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
#     new_name = f"logs/app_{now}.log"
#     os.rename(dest, new_name)
#
# file_handler_rotator = file_handler.rotator
# file_handler.rotator = rename_and_rotate
# # file_handler_rotator = file_handler.rotator
# # file_handler.rotator = compress_and_rotate
#
# # створення об'єкту handler для виводу в консоль
# console_handler = logging.StreamHandler(sys.stdout)
# console_handler.setLevel(logging.DEBUG)
# console_handler.setFormatter(formatter)
#
# logging.getLogger('sqlite3').setLevel(logging.WARNING)
# logging.getLogger('aiosqlite').setLevel(logging.WARNING)
#
# # додавання об'єктів handler до logger
# logger.addHandler(file_handler)
# logger.addHandler(console_handler)
#
# # налаштування кольорів для різних рівнів логування
# # console_handler.addFilter(logging.Filter('my_logger'))
# # console_handler.addFilter(logging.Filter('root'))
#
# # DEBUG - синій
# logging.addLevelName(logging.DEBUG, "\033[1;34m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
# # INFO - зелений
# logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
# # WARNING - жовтий
# logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
# # ERROR - червоний
# logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
# # CRITICAL - червоний з жирним шрифтом
# logging.addLevelName(logging.CRITICAL, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))


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
logger.setLevel(logging.WARNING)

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

file_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s')

# Створення об'єкту обробника логів для виводу на консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(console_formatter)

# Створення об'єкту обробника логів для зберігання у файлі
# Приклад імені файлу: app-2023-05-15.log.gz
today_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
log_filename = f"logs/tcp_retranslator.log"
file_handler = logging.handlers.RotatingFileHandler(
    filename=log_filename, maxBytes=1024 * 10240, backupCount=7
)

file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(file_formatter)

# Додавання обробників логів до логера
logger.addHandler(console_handler)
logger.addHandler(file_handler)

logging.getLogger("sqlite3").setLevel(logging.WARNING)
logging.getLogger("aiosqlite").setLevel(logging.WARNING)
