import tempfile
from pathlib import Path

from RES.configuration import ConfigurationManager
from RES.database import DatabaseManager
from RES.event_logger import EventLogger


def create_isolated_test_environment():
    temp_dir = Path(tempfile.mkdtemp(prefix="kernel_city_test_"))
    config_manager = ConfigurationManager(temp_dir)
    db = DatabaseManager(config_manager.database_path)
    logger = EventLogger(config_manager.logs_dir, db=db)
    return temp_dir, config_manager, db, logger

