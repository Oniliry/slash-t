#logger.py

import os
import logging

from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

from core.config import LOGGING_DIR

class CustomTimedRotatingFileHandler(TimedRotatingFileHandler):
    """
    Кастомный обработчик для ротации логов с переопределением имени файла.
    """
    def rotation_filename(self, default_name):
        """
        Переопределение имени файла при ротации.
        
        :param default_name: Стандартное имя файла.
        :return: Новое имя файла с датой.
        """
        dirname, _ = os.path.split(default_name)
        date_part: str = default_name.rsplit(".", 1)[-1]

        return os.path.join(dirname, f"{date_part}.log")

os.makedirs(LOGGING_DIR, exist_ok=True)

today_filename: str = datetime.now().strftime("%Y-%m-%d.log")
log_file: str = os.path.join(LOGGING_DIR, today_filename)

logger = logging.getLogger("my_logger")

logger.setLevel(logging.DEBUG)

handler = CustomTimedRotatingFileHandler(
    filename=log_file,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

handler.suffix = "%Y-%m-%d"

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

handler.setFormatter(formatter)

logger.addHandler(handler)