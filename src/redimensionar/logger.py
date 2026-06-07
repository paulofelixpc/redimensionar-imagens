import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.expanduser("~"), ".ls-imagecomm", "logs")
LOG_FILE = os.path.join(LOG_DIR, "application.log")
MAX_BYTES = 512 * 1024
BACKUP_COUNT = 3

_loggers = {}


def get_logger(name: str) -> logging.Logger:
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-7s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        os.makedirs(LOG_DIR, exist_ok=True)

        fh = RotatingFileHandler(LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    _loggers[name] = logger
    return logger
