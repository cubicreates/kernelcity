from copy import deepcopy
from typing import Dict, List, Optional

from RES.models import MemoryAllocationRecord, MemoryBlock
from RES.PHASE_4_TESTING.error_handling import ValidationError


class MemoryManager:
    STRATEGIES = ("FIRST_FIT", "BEST_FIT", "WORST_FIT")

    def __init__(self, initial_blocks: Optional[List[int]] = None):
        self.blocks: List[MemoryBlock] = []
        self.history: List[MemoryAllocationRecord] = []
        self._counter = 0
        if initial_blocks is None:
            initial_blocks = [100, 250, 300, 350]
        self.configure_blocks(initial_blocks)

    def configure_blocks(self, block_sizes: List[int]) -> List[MemoryBlock]:
        if not block_sizes:
            raise ValidationError("At least one memory block size is required.")
        blocks: List[MemoryBlock] = []
        for idx, size in enumerate(block_sizes, start=1):
            if size <= 0:
                raise ValidationError("All memory block sizes must be > 0.")
            blocks.append(MemoryBlock(block_id=f"B{idx}", size=int(size)))
        self.blocks = blocks
        self.history.clear()
        self._counter = 0
        return self.blocks

    def create_pool_from_total(self, total_memory: int, partition_sizes: List[int]) -> List[MemoryBlock]:
        if total_memory <= 0:
            raise ValidationError("Total memory size must be > 0.")
        if not partition_sizes:
            raise ValidationError("At least one partition size is required.")
        if any(p <= 0 for p in partition_sizes):
            raise ValidationError("All partition sizes must be > 0.")
        used = sum(partition_sizes)
        if used > total_memory:
            raise ValidationError(f"Sum of partitions ({used} KB) exceeds total memory ({total_memory} KB).")
        sizes = list(partition_sizes)
        if used < total_memory:
            sizes.append(total_memory - used)
        return self.configure_blocks(sizes)

    def allocate(self, reference: str, requested_size: int, strategy: str = "FIRST_FIT") -> MemoryAllocationRecord:
        ref = (reference or "").strip()
        if not ref:
            raise ValidationError("Allocation reference cannot be empty.")
        if requested_size <= 0:
            raise ValidationError("Requested memory size must be > 0.")
        strat = (strategy or "").strip().upper()
        if strat not in self.STRATEGIES:
            raise ValidationError(f"Unsupported memory strategy: {strategy}")

        free_blocks = [b for b in self.blocks if b.allocated_to is None and b.size >= requested_size]
        chosen: Optional[MemoryBlock] = None
        if free_blocks:
            if strat == "FIRST_FIT":
                chosen = free_blocks[0]
            elif strat == "BEST_FIT":
                chosen = min(free_blocks, key=lambda b: (b.size, self.blocks.index(b)))
            else:
                chosen = max(free_blocks, key=lambda b: (b.size, -self.blocks.index(b)))

        self._counter += 1
        alloc_id = f"MEM-{self._counter:04d}"

        if chosen is not None:
            chosen.allocated_to = ref
            chosen.requested_size = requested_size
            chosen.internal_fragmentation = chosen.size - requested_size
            record = MemoryAllocationRecord(
                allocation_id=alloc_id,
                reference=ref,
                requested_size=requested_size,
                allocated_block_id=chosen.block_id,
                remaining_free_space=self.get_free_memory(),
                status="ALLOCATED",
                strategy=strat,
            )
        else:
            record = MemoryAllocationRecord(
                allocation_id=alloc_id,
                reference=ref,
                requested_size=requested_size,
                allocated_block_id=None,
                remaining_free_space=self.get_free_memory(),
                status="FAILED",
                strategy=strat,
            )

        self.history.append(record)
        return record

    def deallocate(self, reference_or_block_id: str) -> bool:
        target = (reference_or_block_id or "").strip()
        if not target:
            raise ValidationError("Specify a block ID or process reference to deallocate.")
        released = False
        for block in self.blocks:
            if block.allocated_to == target or (block.block_id == target and block.allocated_to is not None):
                block.allocated_to = None
                block.requested_size = 0
                block.internal_fragmentation = 0
                released = True
        return released

    def get_total_memory(self) -> int:
        return sum(b.size for b in self.blocks)

    def get_allocated_memory(self) -> int:
        return sum(b.requested_size for b in self.blocks if b.allocated_to is not None)

    def get_occupied_block_memory(self) -> int:
        return sum(b.size for b in self.blocks if b.allocated_to is not None)

    def get_free_memory(self) -> int:
        return sum(b.size for b in self.blocks if b.allocated_to is None)

    def get_internal_fragmentation(self) -> int:
        return sum(b.internal_fragmentation for b in self.blocks if b.allocated_to is not None)

    def get_external_fragmentation(self, pending_request: Optional[int] = None) -> int:
        free_blocks = [b.size for b in self.blocks if b.allocated_to is None]
        if not free_blocks:
            return 0
        total_free = sum(free_blocks)
        if pending_request is not None:
            if max(free_blocks) < pending_request and total_free >= pending_request:
                return total_free
            return 0
        if len(free_blocks) <= 1:
            return 0
        return total_free - max(free_blocks)

    def get_free_blocks(self) -> List[MemoryBlock]:
        return [b for b in self.blocks if b.allocated_to is None]

    def get_allocated_blocks(self) -> List[MemoryBlock]:
        return [b for b in self.blocks if b.allocated_to is not None]

    def get_free_blocks_count(self) -> int:
        return len(self.get_free_blocks())

    def get_fragmentation_explanation(self) -> str:
        return (
            "Internal fragmentation is the unused space inside fixed partitions (Partition Size - Requested Size). "
            "External fragmentation is free memory scattered across non-contiguous unallocated partitions."
        )

    def get_metrics(self) -> Dict[str, int]:
        success_count = sum(1 for r in self.history if r.status == "ALLOCATED")
        fail_count = sum(1 for r in self.history if r.status == "FAILED")
        return {
            "total_memory": self.get_total_memory(),
            "requested_memory": sum(r.requested_size for r in self.history),
            "allocated_memory": self.get_allocated_memory(),
            "occupied_block_memory": self.get_occupied_block_memory(),
            "free_memory": self.get_free_memory(),
            "free_blocks_count": self.get_free_blocks_count(),
            "internal_fragmentation": self.get_internal_fragmentation(),
            "external_fragmentation": self.get_external_fragmentation(),
            "allocations_succeeded": success_count,
            "allocations_failed": fail_count,
        }

    def simulate_strategy(self, block_sizes: List[int], requests: List[Dict[str, object]], strategy: str) -> Dict[str, object]:
        temp_manager = MemoryManager(deepcopy(block_sizes))
        records: List[MemoryAllocationRecord] = []
        for item in requests:
            ref = str(item["reference"])
            size = int(item["size"])
            records.append(temp_manager.allocate(ref, size, strategy=strategy))
        return {
            "strategy": strategy.upper(),
            "blocks": temp_manager.blocks,
            "records": records,
            "metrics": temp_manager.get_metrics(),
        }

