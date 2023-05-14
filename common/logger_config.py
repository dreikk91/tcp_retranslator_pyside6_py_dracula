import loguru
from datetime import datetime

# Формат повідомлення для виводу в консоль та файл
logger = loguru.logger
logger.add(
    sink="log\\tcp_retranslator.log",
    enqueue=True,
    rotation="1 day",
    retention="1 week",
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
)
# import logging
#
# logging.basicConfig(
#     format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)s - %(message)s',
#     level=logging.DEBUG,
#     datefmt='%Y-%m-%d %H:%M:%S'
# )
#
# logger = logging.getLogger(__name__)

# import logging
# import logging.config
# import logging.handlers
# import sys
#
# # формат повідомлення логу
# LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)s - %(message)s"
# DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
#
# # створення логера
# LOGGING_CONFIG = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "console_formatter": {
#             "()": "colorlog.ColoredFormatter",
#             "format": LOG_FORMAT,
#             "datefmt": DATE_FORMAT,
#             "log_colors": {
#                 "DEBUG": "white",
#                 "INFO": "green",
#                 "WARNING": "yellow",
#                 "ERROR": "red",
#                 "CRITICAL": "bold_red",
#             },
#             "secondary_log_colors": {},
#             "style": "%",
#         },
#         "file_formatter": {
#             "format": LOG_FORMAT,
#             "datefmt": DATE_FORMAT,
#         },
#     },
#     "handlers": {
#         # обробник для виводу логів у консоль
#         "console": {
#             "class": "logging.StreamHandler",
#             "level": "DEBUG",
#             "formatter": "console_formatter",
#             "stream": sys.stdout,
#         },
#         # обробник для запису логів у файл
#         "file": {
#             "class": "logging.handlers.TimedRotatingFileHandler",
#             "level": "DEBUG",
#             "formatter": "file_formatter",
#             "filename": "app.log",
#             "when": "D",
#             "interval": 1,
#             "backupCount": 30,
#             "encoding": "utf8",
#             "utc": True,
#         },
#     },
#     "root": {
#         "level": "DEBUG",
#         "handlers": ["console", "file"],
#     },
# }
#
# # налаштування логера
# logging.config.dictConfig(LOGGING_CONFIG)

# # використання логера
# logger = logging.getLogger()
# logger.debug("Debug message")
# logger.info("Info message")
# logger.warning("Warning message")
# logger.error("Error message")
# logger.critical("Critical message")
# import logging
# from logging.config import dictConfig
#
# logging_config = dict(
#     version = 1,
#     formatters = {
#         'f': {'format':
#               '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'}
#         },
#     handlers = {
#         'h': {'class': 'logging.StreamHandler',
#               'formatter': 'f',
#               'level': logging.DEBUG}
#         },
#     root = {
#         'handlers': ['h'],
#         'level': logging.DEBUG,
#         },
# )
#
# dictConfig(logging_config)
#
# logger = logging.getLogger()
# logger.debug('often makes a very good meal of %s', 'visiting tourists')