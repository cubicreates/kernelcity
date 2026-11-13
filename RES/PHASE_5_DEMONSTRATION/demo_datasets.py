from pathlib import Path
from typing import Dict, List

from RES.models import Job, JobState


def get_demo_scheduling_jobs() -> List[Job]:
    return [
        Job(job_id="DEMO-P1", name="Indexer", job_type="system_info_task", priority=2, arrival_time=0, burst_time=6, memory_required=120, state=JobState.READY),
        Job(job_id="DEMO-P2", name="LogParser", job_type="process_csv", priority=1, arrival_time=1, burst_time=3, memory_required=80, state=JobState.READY),
        Job(job_id="DEMO-P3", name="Archiver", job_type="compress_file", priority=4, arrival_time=2, burst_time=8, memory_required=200, state=JobState.READY),
        Job(job_id="DEMO-P4", name="Verifier", job_type="backup_directory", priority=3, arrival_time=3, burst_time=2, memory_required=60, state=JobState.READY),
    ]


def get_demo_memory_scenario() -> Dict[str, object]:
    return {
        "label": "DEMO",
        "block_sizes": [100, 500, 200, 300, 600],
        "requests": [
            {"reference": "DEMO-PROC-1", "size": 212},
            {"reference": "DEMO-PROC-2", "size": 417},
            {"reference": "DEMO-PROC-3", "size": 112},
            {"reference": "DEMO-PROC-4", "size": 426},
        ],
    }


def get_demo_banker_scenario() -> Dict[str, object]:
    return {
        "label": "DEMO",
        "resource_types": ["CPU_UNITS", "IO_CHANNELS", "MEMORY_PAGES"],
        "process_names": ["P0", "P1", "P2", "P3", "P4"],
        "available": [3, 3, 2],
        "allocation": [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2],
        ],
        "maximum": [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3],
        ],
        "safe_request": {"process_index": 1, "request": [1, 0, 2]},
        "unsafe_request": {"process_index": 0, "request": [0, 2, 0]},
    }


def get_demo_deadlock_scenario() -> Dict[str, object]:
    return {
        "label": "DEMO",
        "resource_types": ["R0", "R1", "R2"],
        "process_names": ["P0", "P1", "P2"],
        "available": [0, 0, 0],
        "allocation": [
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
        ],
        "request": [
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 0],
        ],
    }


def ensure_demo_input_files(demo_dir: Path) -> Dict[str, Path]:
    demo_dir.mkdir(parents=True, exist_ok=True)
    csv_path = demo_dir / "sample_metrics.csv"
    if not csv_path.exists():
        csv_path.write_text(
            "process,cpu_burst,memory_kb,priority\n"
            "Indexer,6,120,2\n"
            "LogParser,3,80,1\n"
            "Archiver,8,200,4\n"
            "Verifier,2,60,3\n",
            encoding="utf-8",
        )
    script_path = demo_dir / "sample_worker.py"
    if not script_path.exists():
        script_path.write_text(
            "import os\n"
            "print('KERNEL CITY DEMO WORKER EXECUTED, PID:', os.getpid())\n",
            encoding="utf-8",
        )
    backup_src = demo_dir / "sample_docs"
    backup_src.mkdir(exist_ok=True)
    note_file = backup_src / "readme_demo.txt"
    if not note_file.exists():
        note_file.write_text("KERNEL CITY sample document for backup and compression demos.\n", encoding="utf-8")
    return {
        "csv": csv_path,
        "script": script_path,
        "docs_dir": backup_src,
    }

