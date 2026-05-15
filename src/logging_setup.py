import logging
import logging.handlers
import sys
from pathlib import Path
try:
    from pythonjsonlogger import jsonlogger
    _HAS_JSON_LOGGER = True
except ImportError:
    _HAS_JSON_LOGGER = False
APP_LOGGER_NAME = 'immigration_verification'

def configure_logging(log_dir: str='logs', level: int=logging.INFO) -> logging.Logger:
    """Configure application logger with file + console handlers"""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    if logger.handlers:
        return logger
    fmt_console = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s :: %(message)s')
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(fmt_console)
    logger.addHandler(console)
    file_handler = logging.handlers.RotatingFileHandler(filename=str(Path(log_dir) / 'app.log'), maxBytes=1000000, backupCount=3, encoding='utf-8')
    file_handler.setLevel(level)
    if _HAS_JSON_LOGGER:
        json_fmt = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s %(event)s')
        file_handler.setFormatter(json_fmt)
    else:
        file_handler.setFormatter(fmt_console)
    logger.addHandler(file_handler)
    return logger

def get_logger() -> logging.Logger:
    return logging.getLogger(APP_LOGGER_NAME)
