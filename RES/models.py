from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class JobState(str, Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class NavigationMode(str, Enum):
    EXPLORE = "EXPLORE"
    QUICK = "QUICK"
    SKIP = "SKIP"


@dataclass
class Job:
    job_id: str
    name: str
    job_type: str
    priority: int = 1
    arrival_time: int = 0
    burst_time: int = 1
    memory_required: int = 64
    state: JobState = JobState.NEW
    input_path: Optional[str] = None
    output_path: Optional[str] = None
    submission_timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    start_timestamp: Optional[str] = None
    completion_timestamp: Optional[str] = None
    exit_status: Optional[int] = None
    error_details: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessInfo:
    job_id: str
    host_pid: Optional[int]
    process_status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    exit_code: Optional[int] = None
    duration_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0


@dataclass
class SchedulingResultEntry:
    job_id: str
    name: str
    arrival_time: int
    burst_time: int
    priority: int
    start_time: int
    completion_time: int
    turnaround_time: int
    waiting_time: int
    response_time: int


@dataclass
class GanttSlice:
    job_id: str
    start_time: int
    end_time: int


@dataclass
class SchedulingReport:
    algorithm: str
    quantum: Optional[int]
    entries: List[SchedulingResultEntry]
    gantt_chart: List[GanttSlice]
    avg_waiting_time: float
    avg_turnaround_time: float
    avg_response_time: float
    throughput: float
    total_time: int


@dataclass
class MemoryBlock:
    block_id: str
    size: int
    allocated_to: Optional[str] = None
    requested_size: int = 0
    internal_fragmentation: int = 0


@dataclass
class MemoryAllocationRecord:
    allocation_id: str
    reference: str
    requested_size: int
    allocated_block_id: Optional[str]
    remaining_free_space: int
    status: str
    strategy: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class ResourceState:
    resource_types: List[str]
    available: List[int]
    allocation: List[List[int]]
    maximum: List[List[int]]
    need: List[List[int]]
    process_names: List[str] = field(default_factory=list)


@dataclass
class ExecutionRecord:
    job_id: str
    execution_timestamp: str
    duration: float
    outcome: str
    exit_code: Optional[int]
    resource_observations: str
    output_location: Optional[str]

