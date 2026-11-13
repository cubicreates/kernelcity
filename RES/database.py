import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from RES.models import ExecutionRecord, Job, JobState


class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                job_type TEXT NOT NULL,
                priority INTEGER NOT NULL,
                arrival_time INTEGER NOT NULL,
                burst_time INTEGER NOT NULL,
                memory_required INTEGER NOT NULL,
                state TEXT NOT NULL,
                input_path TEXT,
                output_path TEXT,
                submission_timestamp TEXT NOT NULL,
                start_timestamp TEXT,
                completion_timestamp TEXT,
                exit_status INTEGER,
                error_details TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                execution_timestamp TEXT NOT NULL,
                duration REAL NOT NULL,
                outcome TEXT NOT NULL,
                exit_code INTEGER,
                resource_observations TEXT,
                output_location TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                category TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduling_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                algorithm TEXT NOT NULL,
                quantum INTEGER,
                job_count INTEGER NOT NULL,
                avg_waiting REAL NOT NULL,
                avg_turnaround REAL NOT NULL,
                avg_response REAL NOT NULL,
                throughput REAL NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                strategy TEXT NOT NULL,
                reference TEXT NOT NULL,
                requested_size INTEGER NOT NULL,
                allocated_block_id TEXT,
                remaining_free INTEGER NOT NULL,
                status TEXT NOT NULL
            )
            """
        )
        self.connection.commit()

    def save_job(self, job: Job) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO jobs (
                job_id, name, job_type, priority, arrival_time, burst_time,
                memory_required, state, input_path, output_path,
                submission_timestamp, start_timestamp, completion_timestamp,
                exit_status, error_details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(job_id) DO UPDATE SET
                name=excluded.name,
                job_type=excluded.job_type,
                priority=excluded.priority,
                arrival_time=excluded.arrival_time,
                burst_time=excluded.burst_time,
                memory_required=excluded.memory_required,
                state=excluded.state,
                input_path=excluded.input_path,
                output_path=excluded.output_path,
                start_timestamp=excluded.start_timestamp,
                completion_timestamp=excluded.completion_timestamp,
                exit_status=excluded.exit_status,
                error_details=excluded.error_details
            """,
            (
                job.job_id,
                job.name,
                job.job_type,
                job.priority,
                job.arrival_time,
                job.burst_time,
                job.memory_required,
                job.state.value,
                job.input_path,
                job.output_path,
                job.submission_timestamp,
                job.start_timestamp,
                job.completion_timestamp,
                job.exit_status,
                job.error_details,
            ),
        )
        self.connection.commit()

    def load_jobs(self) -> List[Job]:
        cursor = self.connection.cursor()
        rows = cursor.execute("SELECT * FROM jobs ORDER BY submission_timestamp ASC").fetchall()
        jobs: List[Job] = []
        for row in rows:
            jobs.append(
                Job(
                    job_id=row["job_id"],
                    name=row["name"],
                    job_type=row["job_type"],
                    priority=row["priority"],
                    arrival_time=row["arrival_time"],
                    burst_time=row["burst_time"],
                    memory_required=row["memory_required"],
                    state=JobState(row["state"]),
                    input_path=row["input_path"],
                    output_path=row["output_path"],
                    submission_timestamp=row["submission_timestamp"],
                    start_timestamp=row["start_timestamp"],
                    completion_timestamp=row["completion_timestamp"],
                    exit_status=row["exit_status"],
                    error_details=row["error_details"],
                )
            )
        return jobs

    def record_execution(self, record: ExecutionRecord) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO execution_records (
                job_id, execution_timestamp, duration, outcome, exit_code,
                resource_observations, output_location
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.job_id,
                record.execution_timestamp,
                record.duration,
                record.outcome,
                record.exit_code,
                record.resource_observations,
                record.output_location,
            ),
        )
        self.connection.commit()

    def get_execution_records(self, limit: int = 100) -> List[ExecutionRecord]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            "SELECT * FROM execution_records ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [
            ExecutionRecord(
                job_id=row["job_id"],
                execution_timestamp=row["execution_timestamp"],
                duration=row["duration"],
                outcome=row["outcome"],
                exit_code=row["exit_code"],
                resource_observations=row["resource_observations"] or "",
                output_location=row["output_location"],
            )
            for row in rows
        ]

    def record_event(self, category: str, level: str, message: str, details: str = "") -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO events (timestamp, category, level, message, details)
            VALUES (?, ?, ?, ?, ?)
            """,
            (datetime.now().isoformat(timespec="seconds"), category, level, message, details),
        )
        self.connection.commit()

    def get_events(self, limit: int = 100, category: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        if category:
            rows = cursor.execute(
                "SELECT * FROM events WHERE category = ? ORDER BY id DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = cursor.execute(
                "SELECT * FROM events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def record_scheduling_run(
        self,
        algorithm: str,
        quantum: Optional[int],
        job_count: int,
        avg_waiting: float,
        avg_turnaround: float,
        avg_response: float,
        throughput: float,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO scheduling_runs (
                timestamp, algorithm, quantum, job_count, avg_waiting,
                avg_turnaround, avg_response, throughput
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                algorithm,
                quantum,
                job_count,
                avg_waiting,
                avg_turnaround,
                avg_response,
                throughput,
            ),
        )
        self.connection.commit()

    def get_scheduling_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            "SELECT * FROM scheduling_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def record_memory_event(
        self,
        strategy: str,
        reference: str,
        requested_size: int,
        allocated_block_id: Optional[str],
        remaining_free: int,
        status: str,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO memory_events (
                timestamp, strategy, reference, requested_size,
                allocated_block_id, remaining_free, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().isoformat(timespec="seconds"),
                strategy,
                reference,
                requested_size,
                allocated_block_id,
                remaining_free,
                status,
            ),
        )
        self.connection.commit()

    def get_memory_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        rows = cursor.execute(
            "SELECT * FROM memory_events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.connection.close()

