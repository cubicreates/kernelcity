from copy import deepcopy
from typing import Dict, List, Optional, Tuple

from RES.models import ResourceState
from RES.PHASE_4_TESTING.error_handling import ResourceValidationError, ValidationError


class ResourceManager:
    def __init__(self, initial_state: Optional[ResourceState] = None):
        self.state: ResourceState = initial_state or self.create_default_state()

    @staticmethod
    def create_default_state() -> ResourceState:
        resource_types = ["CPU_UNITS", "IO_CHANNELS", "MEMORY_PAGES"]
        available = [3, 3, 2]
        allocation = [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2],
        ]
        maximum = [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3],
        ]
        process_names = ["P0", "P1", "P2", "P3", "P4"]
        need = ResourceManager._compute_need(maximum, allocation)
        return ResourceState(
            resource_types=resource_types,
            available=available,
            allocation=allocation,
            maximum=maximum,
            need=need,
            process_names=process_names,
        )

    @staticmethod
    def _compute_need(maximum: List[List[int]], allocation: List[List[int]]) -> List[List[int]]:
        return [
            [maximum[i][j] - allocation[i][j] for j in range(len(maximum[i]))]
            for i in range(len(maximum))
        ]

    def configure_state(
        self,
        resource_types: List[str],
        available: List[int],
        allocation: List[List[int]],
        maximum: List[List[int]],
        process_names: Optional[List[str]] = None,
    ) -> ResourceState:
        if not resource_types or not allocation or not maximum:
            raise ValidationError("Resource types, allocation, and maximum matrices cannot be empty.")
        num_procs = len(allocation)
        num_res = len(resource_types)
        if len(available) != num_res or len(maximum) != num_procs:
            raise ValidationError("Matrix dimensions do not match resource types or process count.")
        for idx in range(num_procs):
            if len(allocation[idx]) != num_res or len(maximum[idx]) != num_res:
                raise ValidationError(f"Row {idx} dimension mismatch.")
            for j in range(num_res):
                if allocation[idx][j] < 0 or maximum[idx][j] < 0:
                    raise ResourceValidationError("Allocation and maximum values cannot be negative.")
                if allocation[idx][j] > maximum[idx][j]:
                    raise ResourceValidationError(f"Allocation exceeds maximum for process {idx}, resource {j}.")
        if any(val < 0 for val in available):
            raise ResourceValidationError("Available resources cannot be negative.")
        names = process_names or [f"P{i}" for i in range(num_procs)]
        need = self._compute_need(maximum, allocation)
        self.state = ResourceState(
            resource_types=list(resource_types),
            available=list(available),
            allocation=deepcopy(allocation),
            maximum=deepcopy(maximum),
            need=need,
            process_names=list(names),
        )
        return self.state

    def check_safety(self, state: Optional[ResourceState] = None) -> Tuple[bool, List[str], List[str]]:
        target = state or self.state
        num_procs = len(target.allocation)
        num_res = len(target.available)
        work = list(target.available)
        finish = [False] * num_procs
        safe_sequence: List[str] = []
        trace: List[str] = [f"Initial Work = {work}"]

        while len(safe_sequence) < num_procs:
            progressed = False
            for i in range(num_procs):
                if finish[i]:
                    continue
                if all(target.need[i][j] <= work[j] for j in range(num_res)):
                    for j in range(num_res):
                        work[j] += target.allocation[i][j]
                    finish[i] = True
                    proc_label = target.process_names[i] if i < len(target.process_names) else f"P{i}"
                    safe_sequence.append(proc_label)
                    trace.append(f"{proc_label} can finish -> Work becomes {work}")
                    progressed = True
            if not progressed:
                break

        is_safe = all(finish)
        if not is_safe:
            blocked = [
                target.process_names[i] if i < len(target.process_names) else f"P{i}"
                for i, done in enumerate(finish)
                if not done
            ]
            trace.append(f"No safe sequence: blocked processes = {', '.join(blocked)}")
        return is_safe, safe_sequence, trace

    def request_resources(self, process_index: int, request: List[int]) -> Dict[str, object]:
        num_procs = len(self.state.allocation)
        num_res = len(self.state.available)

        if process_index < 0 or process_index >= num_procs:
            raise ResourceValidationError(f"Invalid process index: {process_index}.")
        if len(request) != num_res:
            raise ResourceValidationError(f"Request vector must have length {num_res}.")
        if any(val < 0 for val in request):
            raise ResourceValidationError("Resource request values cannot be negative.")

        proc_name = self.state.process_names[process_index] if process_index < len(self.state.process_names) else f"P{process_index}"

        for j in range(num_res):
            if request[j] > self.state.need[process_index][j]:
                return {
                    "granted": False,
                    "reason": f"{proc_name} request {request} exceeds remaining need {self.state.need[process_index]}.",
                    "safe_sequence": [],
                    "trace": [],
                }
            if request[j] > self.state.available[j]:
                return {
                    "granted": False,
                    "reason": f"{proc_name} must wait: request {request} exceeds available {self.state.available}.",
                    "safe_sequence": [],
                    "trace": [],
                }

        candidate = deepcopy(self.state)
        for j in range(num_res):
            candidate.available[j] -= request[j]
            candidate.allocation[process_index][j] += request[j]
            candidate.need[process_index][j] -= request[j]

        is_safe, safe_sequence, trace = self.check_safety(candidate)
        if is_safe:
            self.state = candidate
            return {
                "granted": True,
                "reason": f"Request granted to {proc_name}. System remains in a SAFE state.",
                "safe_sequence": safe_sequence,
                "trace": trace,
            }

        return {
            "granted": False,
            "reason": f"Request denied for {proc_name}: proposed allocation leads to an UNSAFE state.",
            "safe_sequence": [],
            "trace": trace,
        }

