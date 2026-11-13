import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from RES.database import DatabaseManager
from RES.event_logger import EventLogger
from RES.models import ExecutionRecord, Job, JobState, ProcessInfo
from RES.PHASE_4_TESTING.error_handling import ProcessExecutionError, ValidationError
from RES.PHASE_4_TESTING.validation import InputValidator


class ProcessManager:
    ALLOWED_JOB_TYPES = (
        "backup_directory",
        "compress_file",
        "run_python_script",
        "process_csv",
        "organise_files",
        "system_info_task",
    )

    VALID_STATE_TRANSITIONS = {
        JobState.NEW: {JobState.READY, JobState.CANCELLED},
        JobState.READY: {JobState.RUNNING, JobState.WAITING, JobState.CANCELLED},
        JobState.RUNNING: {JobState.WAITING, JobState.COMPLETED, JobState.TERMINATED, JobState.FAILED, JobState.CANCELLED},
        JobState.WAITING: {JobState.READY, JobState.CANCELLED, JobState.FAILED},
        JobState.COMPLETED: set(),
        JobState.TERMINATED: set(),
        JobState.FAILED: {JobState.READY},
        JobState.CANCELLED: {JobState.READY},
    }

    def __init__(
        self,
        base_dir: Path,
        jobs_dir: Path,
        demo_dir: Path,
        db: DatabaseManager,
        logger: EventLogger,
        default_timeout: int = 30,
    ):
        self.base_dir = Path(base_dir)
        self.jobs_dir = Path(jobs_dir)
        self.demo_dir = Path(demo_dir)
        self.db = db
        self.logger = logger
        self.default_timeout = default_timeout
        self.jobs: Dict[str, Job] = {}
        self.processes: Dict[str, ProcessInfo] = {}
        self._active_subprocesses: Dict[str, subprocess.Popen] = {}
        self._job_counter = 0
        self._load_existing_jobs()

    def _load_existing_jobs(self) -> None:
        loaded = self.db.load_jobs()
        for job in loaded:
            if job.state == JobState.RUNNING:
                job.state = JobState.FAILED
                job.error_details = "Interrupted by previous application shutdown."
                self.db.save_job(job)
            self.jobs[job.job_id] = job
            if job.job_id.startswith("JOB-"):
                try:
                    num = int(job.job_id.split("-")[1])
                    if num > self._job_counter:
                        self._job_counter = num
                except (IndexError, ValueError):
                    pass

    def submit_job(
        self,
        name: str,
        job_type: str,
        priority: int = 1,
        arrival_time: int = 0,
        burst_time: int = 2,
        memory_required: int = 64,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> Job:
        clean_name = InputValidator.require_non_empty(name, "Job name")
        clean_type = InputValidator.require_choice(job_type.strip().lower(), self.ALLOWED_JOB_TYPES, "Job type")
        clean_priority = InputValidator.require_int(priority, "Priority", minimum=1, maximum=10)
        clean_arrival = InputValidator.require_int(arrival_time, "Arrival time", minimum=0)
        clean_burst = InputValidator.require_int(burst_time, "Burst time", minimum=1)
        clean_memory = InputValidator.require_int(memory_required, "Memory required", minimum=1)

        allowed_roots = [self.jobs_dir, self.demo_dir]
        validated_input: Optional[str] = None
        if input_path and input_path.strip():
            resolved_in = InputValidator.validate_safe_path(input_path, allowed_roots=allowed_roots, must_exist=True)
            validated_input = str(resolved_in)
        elif clean_type in ("backup_directory", "compress_file", "run_python_script", "process_csv", "organise_files"):
            raise ValidationError(f"Job type '{clean_type}' requires a valid input path inside data/jobs or data/demo.")

        if job_id and job_id.strip():
            resolved_id = InputValidator.require_non_empty(job_id, "Job ID").upper()
            if resolved_id in self.jobs:
                raise ValidationError(f"Job ID '{resolved_id}' already exists.")
            assigned_id = resolved_id
        else:
            self._job_counter += 1
            assigned_id = f"JOB-{self._job_counter:04d}"
            while assigned_id in self.jobs:
                self._job_counter += 1
                assigned_id = f"JOB-{self._job_counter:04d}"

        if output_path and output_path.strip():
            resolved_out = InputValidator.validate_safe_path(output_path, allowed_roots=[self.jobs_dir], must_exist=False)
            validated_output = str(resolved_out)
        else:
            validated_output = str((self.jobs_dir / f"{assigned_id}_output").resolve())

        job = Job(
            job_id=assigned_id,
            name=clean_name,
            job_type=clean_type,
            priority=clean_priority,
            arrival_time=clean_arrival,
            burst_time=clean_burst,
            memory_required=clean_memory,
            state=JobState.READY,
            input_path=validated_input,
            output_path=validated_output,
        )
        self.jobs[job.job_id] = job
        self.db.save_job(job)
        self.logger.log_event("JOB", f"Submitted job {job.job_id} ({job.name}, type={job.job_type})")
        return job

    def transition_job_state(self, job_id: str, new_state: JobState) -> Job:
        job = self.get_job(job_id)
        allowed = self.VALID_STATE_TRANSITIONS.get(job.state, set())
        if new_state not in allowed:
            raise ValidationError(f"Invalid state transition for {job_id}: {job.state.value} -> {new_state.value}.")
        job.state = new_state
        self.db.save_job(job)
        self.logger.log_event("JOB", f"Job {job_id} transitioned to {new_state.value}")
        return job

    def filter_jobs(self, state_filter: Optional[JobState] = None, query: str = "") -> List[Job]:
        items = self.list_jobs(state_filter=state_filter)
        q = (query or "").strip().lower()
        if not q:
            return items
        return [j for j in items if q in j.job_id.lower() or q in j.name.lower() or q in j.job_type.lower()]

    def list_jobs(self, state_filter: Optional[JobState] = None) -> List[Job]:
        items = list(self.jobs.values())
        if state_filter is not None:
            items = [j for j in items if j.state == state_filter]
        return items

    def get_job(self, job_id: str) -> Job:
        if job_id not in self.jobs:
            raise ValidationError(f"Job '{job_id}' not found.")
        return self.jobs[job_id]

    def _wrap_python_code(self, code: str, *args: str) -> List[str]:
        if getattr(sys, "frozen", False):
            return [sys.executable, "--kc-worker", "exec_code", code, *args]
        return [sys.executable, "-c", code, *args]

    def _build_worker_command(self, job: Job) -> List[str]:
        out_path = Path(job.output_path or str(self.jobs_dir / f"{job.job_id}_output"))
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if job.job_type == "run_python_script":
            assert job.input_path is not None
            if getattr(sys, "frozen", False):
                return [sys.executable, "--kc-worker", "exec_script", job.input_path]
            return [sys.executable, job.input_path]

        if job.job_type == "backup_directory":
            code = (
                "import shutil, sys; from pathlib import Path; "
                "src=Path(sys.argv[1]); dst=Path(sys.argv[2]); "
                "shutil.copytree(src, dst, dirs_exist_ok=True); "
                "print(f'Backed up {src} to {dst}')"
            )
            return self._wrap_python_code(code, job.input_path or "", str(out_path))

        if job.job_type == "compress_file":
            archive_base = str(out_path)
            code = (
                "import shutil, sys; from pathlib import Path; "
                "src=Path(sys.argv[1]); base=sys.argv[2]; "
                "root=src if src.is_dir() else src.parent; "
                "target='.' if src.is_dir() else src.name; "
                "out=shutil.make_archive(base, 'zip', root_dir=str(root), base_dir=target); "
                "print(f'Compressed to {out}')"
            )
            return self._wrap_python_code(code, job.input_path or "", archive_base)

        if job.job_type == "process_csv":
            report_file = out_path.with_suffix(".txt")
            code = (
                "import sys, pandas as pd; from pathlib import Path; "
                "src=Path(sys.argv[1]); dst=Path(sys.argv[2]); "
                "df=pd.read_csv(src); num=df.select_dtypes(include='number'); "
                "stats=num.agg(['mean','min','max']).round(3).to_string() if not num.empty else 'No numeric columns'; "
                "summary=f'File: {src.name}\\nRows: {len(df)}\\nColumns: {len(df.columns)}\\nHeaders: {list(df.columns)}\\nNumeric Summary:\\n{stats}\\n'; "
                "dst.write_text(summary, encoding='utf-8'); "
                "print(summary.strip())"
            )
            job.output_path = str(report_file)
            return self._wrap_python_code(code, job.input_path or "", str(report_file))

        if job.job_type == "organise_files":
            code = (
                "import shutil, sys; from pathlib import Path; "
                "src=Path(sys.argv[1]); dst=Path(sys.argv[2]); dst.mkdir(parents=True, exist_ok=True); "
                "count=0\n"
                "for p in src.iterdir():\n"
                " if p.is_file():\n"
                "  ext=(p.suffix.lstrip('.') or 'no_ext').lower()\n"
                "  sub=dst / ext; sub.mkdir(exist_ok=True)\n"
                "  shutil.copy2(p, sub / p.name); count+=1\n"
                "print(f'Organised {count} files into {dst}')"
            )
            return self._wrap_python_code(code, job.input_path or "", str(out_path))

        info_file = out_path.with_suffix(".txt")
        job.output_path = str(info_file)
        code = (
            "import os, platform, sys; from pathlib import Path; "
            "dst=Path(sys.argv[1]); "
            "text=f'System: {platform.system()} {platform.release()}\\nPython: {sys.version.split()[0]}\\nPID: {os.getpid()}\\n'; "
            "dst.write_text(text, encoding='utf-8'); print(text.strip())"
        )
        return self._wrap_python_code(code, str(info_file))

    def execute_job(self, job_id: str, timeout: Optional[int] = None) -> ExecutionRecord:
        job = self.get_job(job_id)
        if job.state in (JobState.CANCELLED, JobState.RUNNING):
            raise ProcessExecutionError(f"Job '{job_id}' cannot be executed in state {job.state.value}.")

        cmd = self._build_worker_command(job)
        exec_timeout = timeout or self.default_timeout
        job.state = JobState.RUNNING
        job.start_timestamp = datetime.now().isoformat(timespec="seconds")
        job.error_details = None
        self.db.save_job(job)

        started = time.perf_counter()
        proc_info = ProcessInfo(
            job_id=job.job_id,
            host_pid=None,
            process_status="RUNNING",
            start_time=job.start_timestamp,
        )
        self.processes[job.job_id] = proc_info

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            proc_info.host_pid = process.pid
            self._active_subprocesses[job.job_id] = process
            stdout, stderr = process.communicate(timeout=exec_timeout)
            duration = round(time.perf_counter() - started, 4)
            exit_code = process.returncode

            proc_info.end_time = datetime.now().isoformat(timespec="seconds")
            proc_info.exit_code = exit_code
            proc_info.duration_seconds = duration
            job.completion_timestamp = proc_info.end_time
            job.exit_status = exit_code

            if exit_code == 0:
                job.state = JobState.COMPLETED
                proc_info.process_status = "COMPLETED"
                outcome = "COMPLETED"
                obs = (stdout or "Completed cleanly.").strip()[:300]
            else:
                job.state = JobState.FAILED
                proc_info.process_status = "FAILED"
                outcome = "FAILED"
                job.error_details = (stderr or f"Exited with code {exit_code}").strip()[:300]
                obs = job.error_details

        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            duration = round(time.perf_counter() - started, 4)
            job.state = JobState.FAILED
            job.completion_timestamp = datetime.now().isoformat(timespec="seconds")
            job.exit_status = -1
            job.error_details = f"Timed out after {exec_timeout}s."
            proc_info.end_time = job.completion_timestamp
            proc_info.exit_code = -1
            proc_info.duration_seconds = duration
            proc_info.process_status = "TIMEOUT"
            outcome = "FAILED"
            obs = job.error_details
        except OSError as exc:
            duration = round(time.perf_counter() - started, 4)
            job.state = JobState.FAILED
            job.completion_timestamp = datetime.now().isoformat(timespec="seconds")
            job.exit_status = -1
            job.error_details = str(exc)
            proc_info.end_time = job.completion_timestamp
            proc_info.exit_code = -1
            proc_info.duration_seconds = duration
            proc_info.process_status = "ERROR"
            outcome = "FAILED"
            obs = str(exc)
        finally:
            self._active_subprocesses.pop(job.job_id, None)

        self.db.save_job(job)
        record = ExecutionRecord(
            job_id=job.job_id,
            execution_timestamp=job.completion_timestamp or datetime.now().isoformat(timespec="seconds"),
            duration=duration,
            outcome=outcome,
            exit_code=job.exit_status,
            resource_observations=obs,
            output_location=job.output_path,
        )
        self.db.record_execution(record)
        self.logger.log_event(
            "PROCESS",
            f"Job {job.job_id} finished with {outcome} (exit={job.exit_status}, duration={duration}s)",
            level="ERROR" if outcome == "FAILED" else "INFO",
        )
        return record

    def cancel_job(self, job_id: str) -> Job:
        job = self.get_job(job_id)
        if job.state in (JobState.COMPLETED, JobState.CANCELLED):
            raise ValidationError(f"Job '{job_id}' is already {job.state.value}.")
        active_proc = self._active_subprocesses.get(job_id)
        if active_proc is not None and active_proc.poll() is None:
            active_proc.terminate()
            try:
                active_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                active_proc.kill()
            self._active_subprocesses.pop(job_id, None)
        job.state = JobState.CANCELLED
        job.completion_timestamp = datetime.now().isoformat(timespec="seconds")
        self.db.save_job(job)
        self.logger.log_event("JOB", f"Cancelled job {job_id}")
        return job

    def retry_job(self, job_id: str) -> ExecutionRecord:
        job = self.get_job(job_id)
        if job.state not in (JobState.FAILED, JobState.CANCELLED):
            raise ValidationError("Only FAILED or CANCELLED jobs can be retried.")
        job.state = JobState.READY
        job.error_details = None
        job.exit_status = None
        self.db.save_job(job)
        return self.execute_job(job_id)

    def get_tracked_pids(self) -> set[int]:
        return {p.host_pid for p in self.processes.values() if p.host_pid is not None}

    def list_process_infos(self) -> List[ProcessInfo]:
        return list(self.processes.values())

    def terminate_all_active(self) -> None:
        for job_id, proc in list(self._active_subprocesses.items()):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
            self._active_subprocesses.pop(job_id, None)

