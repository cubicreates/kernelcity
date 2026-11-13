import csv
import shutil
import tempfile
from pathlib import Path

import pytest

from GUI.maps import DISTRICT_BUILDINGS
from RES.kernel import KernelEngine
from RES.models import JobState
from RES.PHASE_4_TESTING.error_handling import PathValidationError, ValidationError


def test_v2_district_structure_and_process_state_transitions():
    assert list(DISTRICT_BUILDINGS.keys()) == [
        "OPERATIONS DISTRICT",
        "MEMORY DISTRICT",
        "RESOURCE DISTRICT",
        "INTELLIGENCE DISTRICT",
    ]

    temp_dir = Path(tempfile.mkdtemp(prefix="kc_v2_proc_"))
    try:
        engine = KernelEngine(base_dir=temp_dir)
        job = engine.process_manager.submit_job("CustomJob", "system_info_task", job_id="CUSTOM-101")
        assert job.job_id == "CUSTOM-101"

        with pytest.raises(ValidationError):
            engine.process_manager.submit_job("Duplicate", "system_info_task", job_id="CUSTOM-101")

        engine.process_manager.transition_job_state("CUSTOM-101", JobState.WAITING)
        assert engine.process_manager.get_job("CUSTOM-101").state == JobState.WAITING

        with pytest.raises(ValidationError):
            engine.process_manager.transition_job_state("CUSTOM-101", JobState.TERMINATED)

        engine.shutdown()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_memory_pool_creation_from_total():
    temp_dir = Path(tempfile.mkdtemp(prefix="kc_v2_mem_"))
    try:
        engine = KernelEngine(base_dir=temp_dir)
        blocks = engine.memory_manager.create_pool_from_total(1000, [200, 300, 300])
        assert [b.size for b in blocks] == [200, 300, 300, 200]
        assert engine.memory_manager.get_free_blocks_count() == 4
        with pytest.raises(ValidationError):
            engine.memory_manager.create_pool_from_total(500, [300, 300])
        engine.shutdown()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_all_csv_exports_headers_escaping_and_overwrite_protection():
    temp_dir = Path(tempfile.mkdtemp(prefix="kc_v2_csv_"))
    try:
        engine = KernelEngine(base_dir=temp_dir)

        sched_demo = engine.demo_engine.run_scheduling_demo(quantum=2)
        rr_report = sched_demo["comparison"]["reports"]["ROUND_ROBIN"]
        assert "std_waiting_time" in sched_demo["comparison"]["dataframe"].columns
        gantt_png = engine.analytics.charts.generate_gantt_chart_png(rr_report, filename="test_gantt.png")
        assert gantt_png.exists()

        sched_csv = engine.analytics.export_scheduling_csv(rr_report, filename="sched_test")
        assert sched_csv.exists()
        with sched_csv.open(encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 4
        assert rows[0]["algorithm"] == "ROUND_ROBIN"
        assert rows[0]["quantum"] == "2"

        gantt_csv = engine.analytics.export_gantt_csv(rr_report, filename="gantt_test")
        assert gantt_csv.exists()

        cmp_csv = engine.analytics.export_scheduling_comparison_csv(sched_demo["comparison"], filename="sched_cmp")
        assert cmp_csv.exists()
        with cmp_csv.open(encoding="utf-8") as f:
            cmp_rows = list(csv.DictReader(f))
        assert len(cmp_rows) == 4

        with pytest.raises(ValidationError):
            engine.analytics.export_scheduling_comparison_csv(sched_demo["comparison"], filename="sched_cmp", overwrite=False)

        overwritten = engine.analytics.export_scheduling_comparison_csv(sched_demo["comparison"], filename="sched_cmp", overwrite=True)
        assert overwritten == cmp_csv

        with pytest.raises(PathValidationError):
            engine.analytics.export_scheduling_csv(rr_report, filename="bad_dir", output_dir="/outside/forbidden")

        mem_demo = engine.demo_engine.run_memory_demo()
        mem_cmp_csv = engine.analytics.export_memory_comparison_csv(mem_demo["comparison"], filename="mem_cmp")
        assert mem_cmp_csv.exists()

        engine.memory_manager.allocate('PROC,"A"', 100, strategy="FIRST_FIT")
        mem_csv = engine.analytics.export_memory_csv(
            engine.memory_manager.history,
            engine.memory_manager.blocks,
            engine.memory_manager.get_metrics(),
            filename="mem_single",
        )
        with mem_csv.open(encoding="utf-8") as f:
            mem_rows = list(csv.DictReader(f))
        assert mem_rows[0]["process_id"] == 'PROC,"A"'

        is_safe, seq, _ = engine.resource_manager.check_safety()
        res_csv = engine.analytics.export_resource_allocation_csv(engine.resource_manager.state, is_safe, seq, filename="res_test")
        assert res_csv.exists()

        det = engine.deadlock_manager.detect_deadlock()
        dl_csv = engine.analytics.export_deadlock_csv(
            engine.deadlock_manager.process_names,
            engine.deadlock_manager.resource_types,
            engine.deadlock_manager.allocation,
            engine.deadlock_manager.request,
            det,
            filename="deadlock_test",
        )
        assert dl_csv.exists()

        snap = engine.system_monitor.get_system_snapshot()
        mon_csv = engine.analytics.export_monitoring_csv([snap], filename="mon_test")
        assert mon_csv.exists()

        job = engine.process_manager.submit_job("HistJob", "system_info_task")
        engine.process_manager.execute_job(job.job_id)
        hist_csv = engine.analytics.export_history_csv(engine.db.get_execution_records(), filename="hist_test")
        assert hist_csv.exists()

        engine.shutdown()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

