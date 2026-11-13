from typing import Dict, List


def get_data_design_specification() -> Dict[str, Dict[str, List[str]]]:
    return {
        "entities": {
            "Job": [
                "job_id", "name", "job_type", "priority", "arrival_time",
                "burst_time", "memory_required", "state", "input_path",
                "output_path", "submission_timestamp", "start_timestamp",
                "completion_timestamp", "exit_status", "error_details",
            ],
            "ProcessInfo": [
                "job_id", "host_pid", "process_status", "start_time",
                "end_time", "exit_code", "duration_seconds",
                "cpu_percent", "memory_mb",
            ],
            "MemoryBlock": [
                "block_id", "size", "allocated_to",
                "requested_size", "internal_fragmentation",
            ],
            "ResourceState": [
                "resource_types", "available", "allocation",
                "maximum", "need", "process_names",
            ],
            "ExecutionRecord": [
                "job_id", "execution_timestamp", "duration", "outcome",
                "exit_code", "resource_observations", "output_location",
            ],
        },
        "sqlite_tables": {
            "jobs": ["job_id (PK)", "name", "job_type", "priority", "state", "timestamps"],
            "execution_records": ["id (PK)", "job_id", "duration", "outcome", "exit_code"],
            "events": ["id (PK)", "timestamp", "category", "level", "message"],
            "scheduling_runs": ["id (PK)", "algorithm", "quantum", "avg_waiting", "avg_turnaround"],
            "memory_events": ["id (PK)", "strategy", "reference", "requested_size", "status"],
        },
    }

