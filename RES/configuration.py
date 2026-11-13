import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from RES.models import NavigationMode


@dataclass
class AppConfig:
    navigation_mode: str = NavigationMode.EXPLORE.value
    cpu_warning_threshold: float = 80.0
    ram_warning_threshold: float = 80.0
    disk_warning_threshold: float = 85.0
    default_time_quantum: int = 2
    job_timeout_seconds: int = 30
    monitor_refresh_seconds: float = 1.0
    database_filename: str = "kernel_city.db"


class ConfigurationManager:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.demo_dir = self.data_dir / "demo"
        self.jobs_dir = self.data_dir / "jobs"
        self.config_dir = self.data_dir / "configuration"
        self.reports_dir = self.base_dir / "reports"
        self.logs_dir = self.base_dir / "logs"
        self.config_file = self.config_dir / "settings.json"
        self._ensure_directories()
        self.config = self.load()

    def _ensure_directories(self) -> None:
        for directory in [
            self.data_dir,
            self.demo_dir,
            self.jobs_dir,
            self.config_dir,
            self.reports_dir,
            self.logs_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)

    def load(self) -> AppConfig:
        if not self.config_file.exists():
            cfg = AppConfig()
            self.save(cfg)
            return cfg
        try:
            raw = json.loads(self.config_file.read_text(encoding="utf-8"))
            defaults = asdict(AppConfig())
            merged: Dict[str, Any] = {**defaults, **{k: v for k, v in raw.items() if k in defaults}}
            return AppConfig(**merged)
        except (OSError, json.JSONDecodeError, TypeError):
            cfg = AppConfig()
            self.save(cfg)
            return cfg

    def save(self, config: AppConfig) -> None:
        self.config = config
        self.config_file.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")

    def update(self, **kwargs: Any) -> AppConfig:
        current = asdict(self.config)
        for key, value in kwargs.items():
            if key in current:
                current[key] = value
        updated = AppConfig(**current)
        self.save(updated)
        return updated

    @property
    def database_path(self) -> Path:
        return self.data_dir / self.config.database_filename

