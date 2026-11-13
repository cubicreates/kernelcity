import pytest

from RES.PHASE_2_CORE_MODULES.deadlock_manager import DeadlockManager
from RES.PHASE_2_CORE_MODULES.resource_manager import ResourceManager
from RES.PHASE_4_TESTING.error_handling import ResourceValidationError


def test_banker_safe_and_unsafe_requests():
    rm = ResourceManager()
    is_safe, seq, _ = rm.check_safety()
    assert is_safe is True
    assert seq == ["P1", "P3", "P4", "P0", "P2"]

    granted = rm.request_resources(1, [1, 0, 2])
    assert granted["granted"] is True

    denied = rm.request_resources(0, [0, 2, 0])
    assert denied["granted"] is False


def test_banker_validation_errors():
    rm = ResourceManager()
    with pytest.raises(ResourceValidationError):
        rm.request_resources(99, [0, 0, 0])
    with pytest.raises(ResourceValidationError):
        rm.request_resources(0, [-1, 0, 0])
    with pytest.raises(ResourceValidationError):
        rm.request_resources(0, [1, 0])

    exceeds_avail = rm.request_resources(0, [5, 0, 0])
    assert exceeds_avail["granted"] is False

    exceeds_need = rm.request_resources(1, [2, 0, 0])
    assert exceeds_need["granted"] is False


def test_deadlock_detection_and_recovery():
    dm = DeadlockManager()
    res = dm.detect_deadlock()
    assert res["deadlocked"] is True
    assert res["deadlocked_processes"] == ["P0", "P1", "P2"]

    rag = dm.build_resource_allocation_graph()
    assert len(rag["assignment_edges"]) == 3
    assert len(rag["request_edges"]) == 3

    recovery = dm.recover_by_terminating("P0")
    assert recovery["post_recovery_detection"]["deadlocked"] is False


def test_deadlock_free_scenario():
    dm = DeadlockManager()
    dm.configure_scenario(
        resource_types=["R0", "R1"],
        process_names=["P0", "P1"],
        available=[1, 1],
        allocation=[[1, 0], [0, 1]],
        request=[[0, 1], [1, 0]],
    )
    res = dm.detect_deadlock()
    assert res["deadlocked"] is False
    assert res["deadlocked_processes"] == []

