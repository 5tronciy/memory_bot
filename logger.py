import logging
import sys

RESET = "\033[0m"

LEVEL_COLORS = {
    "DEBUG":    "\033[37m",
    "INFO":     "\033[36m",
    "WARNING":  "\033[33m",
    "ERROR":    "\033[31m",
    "CRITICAL": "\033[41m",
}

THREAD_COLORS = {
    "MainThread": "\033[35m",
    "Main": "\033[35m",
    "Debug": "\033[34m",
    "AnalyzeBoard": "\033[32m",
}

DEFAULT_THREAD_COLOR = "\033[37m"

class ColorFormatter(logging.Formatter):
    def format(self, record):
        level_color  = LEVEL_COLORS.get(record.levelname, "")
        thread_color = THREAD_COLORS.get(record.threadName, DEFAULT_THREAD_COLOR)

        original_thread = record.threadName
        record.threadName = f"{thread_color}{original_thread}{level_color}"

        msg = super().format(record)

        record.threadName = original_thread

        return f"{level_color}{msg}{RESET}"

def get_logger(name="MemoryBot", level=logging.DEBUG):
    handler = logging.StreamHandler(sys.stdout)
    fmt = "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s"
    formatter = ColorFormatter(fmt=fmt, datefmt="%H:%M:%S")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
    logger.propagate = False
    return logger

logger = get_logger()
