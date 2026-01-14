import logging
import sys
from datetime import datetime
from pathlib import Path
import json

# Log dizini
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """JSON formatında log çıktısı için custom formatter"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Extra fields varsa ekle
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "duration_ms"):
            log_entry["duration_ms"] = record.duration_ms
        if hasattr(record, "status_code"):
            log_entry["status_code"] = record.status_code
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Exception bilgisi varsa ekle
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """Renkli console çıktısı için formatter"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Request ID varsa göster
        request_id = getattr(record, "request_id", "")
        request_str = f"[{request_id[:8]}] " if request_id else ""

        return f"{color}{timestamp} | {record.levelname:8} | {request_str}{record.name} | {record.getMessage()}{self.RESET}"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
) -> logging.Logger:
    """
    Profesyonel logger kurulumu

    Args:
        name: Logger adı (örn: 'api', 'allocation', 'database')
        level: Log seviyesi
        log_to_file: Dosyaya log yazılsın mı
        log_to_console: Console'a log yazılsın mı
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Önceki handler'ları temizle
    logger.handlers.clear()

    if log_to_console:
        # Console handler - renkli format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ConsoleFormatter())
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    if log_to_file:
        # File handler - JSON format
        log_file = LOG_DIR / f"{name}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(JSONFormatter())
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

        # Error-only file handler
        error_file = LOG_DIR / f"{name}.error.log"
        error_handler = logging.FileHandler(error_file, encoding="utf-8")
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)

    return logger


# Pre-configured loggers
api_logger = setup_logger("api")
allocation_logger = setup_logger("allocation")
database_logger = setup_logger("database")
request_logger = setup_logger("request")


class LoggerAdapter(logging.LoggerAdapter):
    """Request context ile zenginleştirilmiş logger"""

    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def get_request_logger(request_id: str, user_id: str = None) -> LoggerAdapter:
    """Her request için context'li logger döndür"""
    extra = {"request_id": request_id}
    if user_id:
        extra["user_id"] = user_id
    return LoggerAdapter(request_logger, extra)
