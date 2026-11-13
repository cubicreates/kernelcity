import shutil
import tempfile
from pathlib import Path

from GUI.city import KernelCityGUI
from RES.kernel import KernelEngine
from RES.PHASE_5_DEMONSTRATION.walkthrough import run_complete_walkthrough


def test_database_persistence_across_restart():
    temp_dir = Path(tempfile.mkdtemp(prefix="kc_persist_"))
    try:
        engine1 = KernelEngine(base_dir=temp_dir)
        job = engine1.process_manager.submit_job("PersistJob", "system_info_task")
        engine1.process_manager.execute_job(job.job_id)
        engine1.shutdown()

        engine2 = KernelEngine(base_dir=temp_dir)
        reloaded = engine2.process_manager.get_job(job.job_id)
        assert reloaded.name == "PersistJob"
        records = engine2.db.get_execution_records()
        assert any(r.job_id == job.job_id for r in records)
        engine2.shutdown()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_walkthrough_and_reports():
    temp_dir = Path(tempfile.mkdtemp(prefix="kc_walkthrough_"))
    try:
        engine = KernelEngine(base_dir=temp_dir)
        result = run_complete_walkthrough(engine)
        assert Path(result["text_report"]).exists()
        assert Path(result["json_report"]).exists()
        assert Path(result["scheduling"]["chart_path"]).exists()
        assert Path(result["memory"]["chart_path"]).exists()
        csv_path = engine.analytics.export_csv_report("test_csv", [{"a": 1, "b": 2}])
        assert csv_path.exists()
        engine.shutdown()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_gui_shares_engine_and_res_is_independent():
    temp_dir = Path(tempfile.mkdtemp(prefix="kc_gui_"))
    try:
        engine = KernelEngine(base_dir=temp_dir)
        gui = KernelCityGUI(engine)
        assert gui.kernel is engine
        job = engine.process_manager.submit_job("GuiSharedJob", "system_info_task")
        assert gui.kernel.process_manager.get_job(job.job_id).name == "GuiSharedJob"
        engine.shutdown()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

