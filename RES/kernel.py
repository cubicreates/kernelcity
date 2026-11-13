from pathlib import Path
from typing import Optional

from RES.configuration import ConfigurationManager
from RES.database import DatabaseManager
from RES.event_logger import EventLogger
from RES.PHASE_2_CORE_MODULES.deadlock_manager import DeadlockManager
from RES.PHASE_2_CORE_MODULES.memory_manager import MemoryManager
from RES.PHASE_2_CORE_MODULES.process_manager import ProcessManager
from RES.PHASE_2_CORE_MODULES.resource_manager import ResourceManager
from RES.PHASE_2_CORE_MODULES.scheduler import Scheduler
from RES.PHASE_2_CORE_MODULES.storage_manager import StorageManager
from RES.PHASE_2_CORE_MODULES.system_monitor import SystemMonitor
from RES.PHASE_3_ANALYSIS.analytics import AnalyticsEngine
from RES.PHASE_5_DEMONSTRATION.demo_datasets import ensure_demo_input_files
from RES.PHASE_5_DEMONSTRATION.demo_engine import DemoEngine


class KernelEngine:
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent
        self.config_manager = ConfigurationManager(self.base_dir)
        self.db = DatabaseManager(self.config_manager.database_path)
        self.logger = EventLogger(self.config_manager.logs_dir, db=self.db)

        ensure_demo_input_files(self.config_manager.demo_dir)

        cfg = self.config_manager.config
        self.process_manager = ProcessManager(
            base_dir=self.base_dir,
            jobs_dir=self.config_manager.jobs_dir,
            demo_dir=self.config_manager.demo_dir,
            db=self.db,
            logger=self.logger,
            default_timeout=cfg.job_timeout_seconds,
        )
        self.scheduler = Scheduler()
        self.memory_manager = MemoryManager()
        self.resource_manager = ResourceManager()
        self.deadlock_manager = DeadlockManager()
        self.system_monitor = SystemMonitor(
            base_dir=self.base_dir,
            cpu_threshold=cfg.cpu_warning_threshold,
            ram_threshold=cfg.ram_warning_threshold,
            disk_threshold=cfg.disk_warning_threshold,
        )
        self.storage_manager = StorageManager(
            jobs_dir=self.config_manager.jobs_dir,
            demo_dir=self.config_manager.demo_dir,
            reports_dir=self.config_manager.reports_dir,
            logs_dir=self.config_manager.logs_dir,
        )
        self.analytics = AnalyticsEngine(
            reports_dir=self.config_manager.reports_dir,
            db=self.db,
            base_dir=self.base_dir,
        )
        self.demo_engine = DemoEngine(self)
        self.logger.log_event("SYSTEM", "KernelEngine initialized successfully.")

    def shutdown(self) -> None:
        self.logger.log_event("SYSTEM", "KernelEngine shutting down.")
        self.process_manager.terminate_all_active()
        self.logger.flush()
        self.db.close()

