import logging
from pathlib import Path
from typing import Optional

from RES.database import DatabaseManager


class EventLogger:
    def __init__(self, logs_dir: Path, db: Optional[DatabaseManager] = None):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.logs_dir / "kernel_city.log"
        self.db = db
        self.logger = self._build_logger()

    def _build_logger(self) -> logging.Logger:
        logger = logging.getLogger("kernel_city")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.FileHandler(self.log_file, encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger

    def log_event(self, category: str, message: str, level: str = "INFO", details: str = "") -> None:
        log_line = f"[{category}] {message}"
        if details:
            log_line = f"{log_line} | {details}"
        upper_level = level.upper()
        if upper_level == "ERROR":
            self.logger.error(log_line)
        elif upper_level == "WARNING":
            self.logger.warning(log_line)
        else:
            self.logger.info(log_line)
        if self.db is not None:
            try:
                self.db.record_event(category=category, level=upper_level, message=message, details=details)
            except Exception:
                pass

    def read_recent_logs(self, limit: int = 50) -> list[str]:
        if not self.log_file.exists():
            return []
        lines = self.log_file.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-limit:]

    def flush(self) -> None:
        for handler in self.logger.handlers:
            handler.flush()

