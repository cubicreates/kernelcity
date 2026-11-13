import pytest

from RES.PHASE_2_CORE_MODULES.memory_manager import MemoryManager
from RES.PHASE_4_TESTING.error_handling import ValidationError


def test_empty_and_invalid_blocks_raise():
    with pytest.raises(ValidationError):
        MemoryManager([])
    with pytest.raises(ValidationError):
        MemoryManager([100, -50])


def test_first_best_worst_fit_behavior():
    blocks = [100, 500, 200, 300, 600]
    requests = [
        {"reference": "P1", "size": 212},
        {"reference": "P2", "size": 417},
        {"reference": "P3", "size": 112},
        {"reference": "P4", "size": 426},
    ]

    mm = MemoryManager(blocks)
    first_res = mm.simulate_strategy(blocks, requests, "FIRST_FIT")
    best_res = mm.simulate_strategy(blocks, requests, "BEST_FIT")
    worst_res = mm.simulate_strategy(blocks, requests, "WORST_FIT")

    assert [r.allocated_block_id for r in first_res["records"]] == ["B2", "B5", "B3", None]
    assert [r.allocated_block_id for r in best_res["records"]] == ["B4", "B2", "B3", "B5"]
    assert [r.allocated_block_id for r in worst_res["records"]] == ["B5", "B2", "B4", None]

    assert best_res["metrics"]["allocations_succeeded"] == 4
    assert best_res["metrics"]["allocations_failed"] == 0
    assert mm.get_free_memory() == sum(blocks)


def test_exact_fit_and_deallocate_and_fragmentation():
    mm = MemoryManager([100, 250, 300])
    rec1 = mm.allocate("P1", 100, strategy="FIRST_FIT")
    assert rec1.status == "ALLOCATED"
    assert rec1.allocated_block_id == "B1"
    assert mm.get_internal_fragmentation() == 0

    rec2 = mm.allocate("P2", 200, strategy="BEST_FIT")
    assert rec2.allocated_block_id == "B2"
    assert mm.get_internal_fragmentation() == 50

    rec_fail = mm.allocate("P3", 400, strategy="FIRST_FIT")
    assert rec_fail.status == "FAILED"

    assert mm.deallocate("P1") is True
    assert mm.deallocate("UNKNOWN") is False
    assert mm.get_free_memory() == 400
    assert mm.get_external_fragmentation(pending_request=350) == 400

