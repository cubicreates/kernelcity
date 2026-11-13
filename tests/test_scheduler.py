import pytest

from RES.models import Job
from RES.PHASE_2_CORE_MODULES.scheduler import Scheduler
from RES.PHASE_4_TESTING.error_handling import ValidationError


def _make_jobs():
    return [
        Job(job_id="P1", name="J1", job_type="system_info_task", priority=2, arrival_time=0, burst_time=5),
        Job(job_id="P2", name="J2", job_type="system_info_task", priority=1, arrival_time=1, burst_time=3),
        Job(job_id="P3", name="J3", job_type="system_info_task", priority=3, arrival_time=2, burst_time=1),
    ]


def test_empty_workload_raises():
    scheduler = Scheduler()
    with pytest.raises(ValidationError):
        scheduler.schedule([], "FCFS")


def test_invalid_quantum_and_burst_raise():
    scheduler = Scheduler()
    jobs = _make_jobs()
    with pytest.raises(ValidationError):
        scheduler.schedule(jobs, "ROUND_ROBIN", quantum=0)
    bad_job = [Job(job_id="B1", name="Bad", job_type="system_info_task", burst_time=0)]
    with pytest.raises(ValidationError):
        scheduler.schedule(bad_job, "FCFS")


def test_single_process_all_algorithms():
    scheduler = Scheduler()
    single = [Job(job_id="P1", name="Solo", job_type="system_info_task", arrival_time=2, burst_time=4)]
    for algo in Scheduler.SUPPORTED_ALGORITHMS:
        rep = scheduler.schedule(single, algo, quantum=2)
        entry = rep.entries[0]
        assert entry.start_time == 2
        assert entry.completion_time == 6
        assert entry.turnaround_time == 4
        assert entry.waiting_time == 0
        assert entry.response_time == 0


def test_fcfs_exact_metrics():
    scheduler = Scheduler()
    rep = scheduler.schedule(_make_jobs(), "FCFS")
    by_id = {e.job_id: e for e in rep.entries}
    assert by_id["P1"].completion_time == 5
    assert by_id["P1"].waiting_time == 0
    assert by_id["P2"].completion_time == 8
    assert by_id["P2"].waiting_time == 4
    assert by_id["P3"].completion_time == 9
    assert by_id["P3"].waiting_time == 6
    assert rep.avg_waiting_time == round((0 + 4 + 6) / 3, 3)


def test_sjf_exact_metrics():
    scheduler = Scheduler()
    rep = scheduler.schedule(_make_jobs(), "SJF")
    by_id = {e.job_id: e for e in rep.entries}
    assert by_id["P1"].completion_time == 5
    assert by_id["P3"].completion_time == 6
    assert by_id["P2"].completion_time == 9
    assert by_id["P3"].waiting_time == 3
    assert by_id["P2"].waiting_time == 5


def test_priority_tie_breaking_and_metrics():
    scheduler = Scheduler()
    jobs = [
        Job(job_id="P1", name="A", job_type="system_info_task", priority=2, arrival_time=0, burst_time=4),
        Job(job_id="P2", name="B", job_type="system_info_task", priority=1, arrival_time=0, burst_time=2),
        Job(job_id="P3", name="C", job_type="system_info_task", priority=1, arrival_time=0, burst_time=3),
    ]
    rep = scheduler.schedule(jobs, "PRIORITY")
    order = [s.job_id for s in rep.gantt_chart]
    assert order == ["P2", "P3", "P1"]


def test_round_robin_exact_metrics():
    scheduler = Scheduler()
    jobs = [
        Job(job_id="P1", name="A", job_type="system_info_task", arrival_time=0, burst_time=5),
        Job(job_id="P2", name="B", job_type="system_info_task", arrival_time=1, burst_time=3),
    ]
    rep = scheduler.schedule(jobs, "ROUND_ROBIN", quantum=2)
    by_id = {e.job_id: e for e in rep.entries}
    assert [s.job_id for s in rep.gantt_chart] == ["P1", "P2", "P1", "P2", "P1"]
    assert by_id["P1"].completion_time == 8
    assert by_id["P1"].response_time == 0
    assert by_id["P2"].completion_time == 7
    assert by_id["P2"].response_time == 1

