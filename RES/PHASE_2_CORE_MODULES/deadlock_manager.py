from copy import deepcopy
from typing import Dict, List, Optional

from RES.PHASE_4_TESTING.error_handling import ValidationError


class DeadlockManager:
    NECESSARY_CONDITIONS = [
        "Mutual Exclusion: At least one resource is held in a non-shareable mode.",
        "Hold and Wait: A process holds at least one resource while waiting for additional resources.",
        "No Preemption: Resources cannot be forcibly taken from a process holding them.",
        "Circular Wait: A closed chain of processes exists where each waits for a resource held by the next.",
    ]

    def __init__(self):
        self.reset_default_scenario()

    def reset_default_scenario(self) -> None:
        self.resource_types = ["R0", "R1", "R2"]
        self.process_names = ["P0", "P1", "P2"]
        self.available = [0, 0, 0]
        self.allocation = [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ]
        self.request = [
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ]

    def configure_scenario(
        self,
        resource_types: List[str],
        process_names: List[str],
        available: List[int],
        allocation: List[List[int]],
        request: List[List[int]],
    ) -> None:
        if not resource_types or not process_names:
            raise ValidationError("Resource types and process names cannot be empty.")
        num_p = len(process_names)
        num_r = len(resource_types)
        if len(available) != num_r or len(allocation) != num_p or len(request) != num_p:
            raise ValidationError("Deadlock matrix dimensions do not match.")
        for i in range(num_p):
            if len(allocation[i]) != num_r or len(request[i]) != num_r:
                raise ValidationError(f"Row {i} length mismatch.")
            if any(v < 0 for v in allocation[i]) or any(v < 0 for v in request[i]):
                raise ValidationError("Allocation and request counts cannot be negative.")
        if any(v < 0 for v in available):
            raise ValidationError("Available vector cannot contain negative values.")
        self.resource_types = list(resource_types)
        self.process_names = list(process_names)
        self.available = list(available)
        self.allocation = deepcopy(allocation)
        self.request = deepcopy(request)

    def detect_deadlock(self) -> Dict[str, object]:
        num_p = len(self.process_names)
        num_r = len(self.resource_types)
        work = list(self.available)
        finish = [all(self.allocation[i][j] == 0 for j in range(num_r)) for i in range(num_p)]
        trace: List[str] = [f"Initial Work = {work}"]

        while True:
            progressed = False
            for i in range(num_p):
                if finish[i]:
                    continue
                if all(self.request[i][j] <= work[j] for j in range(num_r)):
                    for j in range(num_r):
                        work[j] += self.allocation[i][j]
                    finish[i] = True
                    trace.append(f"{self.process_names[i]} request {self.request[i]} satisfied -> Work = {work}")
                    progressed = True
            if not progressed:
                break

        deadlocked = [self.process_names[i] for i in range(num_p) if not finish[i]]
        is_deadlocked = len(deadlocked) > 0
        summary = (
            f"DEADLOCK DETECTED involving processes: {', '.join(deadlocked)}."
            if is_deadlocked
            else "NO DEADLOCK DETECTED. All processes can complete."
        )
        return {
            "deadlocked": is_deadlocked,
            "deadlocked_processes": deadlocked,
            "finish_flags": finish,
            "trace": trace,
            "summary": summary,
        }

    def build_resource_allocation_graph(self) -> Dict[str, List[str]]:
        assignment_edges: List[str] = []
        request_edges: List[str] = []
        for i, proc in enumerate(self.process_names):
            for j, res in enumerate(self.resource_types):
                if self.allocation[i][j] > 0:
                    assignment_edges.append(f"{res} --(x{self.allocation[i][j]})--> {proc}")
                if self.request[i][j] > 0:
                    request_edges.append(f"{proc} --(x{self.request[i][j]})--> {res}")
        return {
            "assignment_edges": assignment_edges,
            "request_edges": request_edges,
        }

    def recover_by_terminating(self, process_name: str) -> Dict[str, object]:
        if process_name not in self.process_names:
            raise ValidationError(f"Unknown process '{process_name}' in deadlock scenario.")
        idx = self.process_names.index(process_name)
        released = list(self.allocation[idx])
        for j in range(len(self.resource_types)):
            self.available[j] += self.allocation[idx][j]
            self.allocation[idx][j] = 0
            self.request[idx][j] = 0
        detection = self.detect_deadlock()
        return {
            "terminated_process": process_name,
            "released_resources": released,
            "new_available": list(self.available),
            "post_recovery_detection": detection,
        }

