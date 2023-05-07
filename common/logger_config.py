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
