import os
import shutil

import pytest

from RES.models import JobState
from RES.PHASE_2_CORE_MODULES.process_manager import ProcessManager
from RES.PHASE_2_CORE_MODULES.storage_manager import StorageManager
from RES.PHASE_2_CORE_MODULES.system_monitor import SystemMonitor
from RES.PHASE_4_TESTING.error_handling import PathValidationError, ValidationError
from RES.PHASE_4_TESTING.test_support import create_isolated_test_environment
from RES.PHASE_5_DEMONSTRATION.demo_datasets import ensure_demo_input_files


def test_process_execution_and_failures():
    temp_dir, cfg, db, logger = create_isolated_test_environment()
    try:
        files = ensure_demo_input_files(cfg.demo_dir)
        pm = ProcessManager(temp_dir, cfg.jobs_dir, cfg.demo_dir, db, logger, default_timeout=5)

        job_csv = pm.submit_job("CSVTest", "process_csv", input_path=str(files["csv"]))
        rec_csv = pm.execute_job(job_csv.job_id)
        assert rec_csv.outcome == "COMPLETED"
        assert rec_csv.exit_code == 0

        job_sys = pm.submit_job("SysInfo", "system_info_task")
        rec_sys = pm.execute_job(job_sys.job_id)
        assert rec_sys.outcome == "COMPLETED"

        fail_script = cfg.jobs_dir / "fail_script.py"
        fail_script.write_text("import sys; sys.exit(2)\n", encoding="utf-8")
        job_fail = pm.submit_job("FailScript", "run_python_script", input_path=str(fail_script))
        rec_fail = pm.execute_job(job_fail.job_id)
        assert rec_fail.outcome == "FAILED"
        assert rec_fail.exit_code == 2

        slow_script = cfg.jobs_dir / "slow_script.py"
        slow_script.write_text("import time; time.sleep(3)\n", encoding="utf-8")
        job_timeout = pm.submit_job("SlowScript", "run_python_script", input_path=str(slow_script))
        rec_timeout = pm.execute_job(job_timeout.job_id, timeout=1)
        assert rec_timeout.outcome == "FAILED"
        assert "Timed out" in pm.get_job(job_timeout.job_id).error_details

        job_cancel = pm.submit_job("CancelMe", "system_info_task")
        cancelled = pm.cancel_job(job_cancel.job_id)
        assert cancelled.state == JobState.CANCELLED

        with pytest.raises(PathValidationError):
            pm.submit_job("Escape", "process_csv", input_path="/etc/passwd")

        with pytest.raises(ValidationError):
            pm.submit_job("BadType", "arbitrary_shell")
    finally:
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_storage_and_system_monitor():
    temp_dir, cfg, db, _ = create_isolated_test_environment()
    try:
        storage = StorageManager(cfg.jobs_dir, cfg.demo_dir, cfg.reports_dir, cfg.logs_dir)
        temp_file = cfg.jobs_dir / "sample.txt"
        temp_file.write_text("hello kernel city\n", encoding="utf-8")
        assert "hello kernel city" in storage.inspect_file(str(temp_file))
        summary = storage.get_storage_summary()
        assert summary["jobs"]["file_count"] == 1
        storage.delete_temp_file(str(temp_file))
        assert not temp_file.exists()

        monitor = SystemMonitor(temp_dir)
        snap = monitor.get_system_snapshot()
        assert snap["source"] == "LIVE"
        assert 0.0 <= snap["cpu_percent"] <= 100.0
        assert snap["ram_total_gb"] > 0
        assert monitor.is_protected_process(os.getpid()) is True
    finally:
        db.close()
        shutil.rmtree(temp_dir, ignore_errors=True)

