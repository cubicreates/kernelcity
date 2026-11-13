from collections import deque
from typing import Dict, List, Optional

from RES.models import GanttSlice, Job, SchedulingReport, SchedulingResultEntry
from RES.PHASE_4_TESTING.error_handling import ValidationError


class Scheduler:
    SUPPORTED_ALGORITHMS = ("FCFS", "SJF", "PRIORITY", "ROUND_ROBIN")

    def schedule(self, jobs: List[Job], algorithm: str, quantum: int = 2) -> SchedulingReport:
        algo = (algorithm or "").strip().upper()
        if algo not in self.SUPPORTED_ALGORITHMS:
            raise ValidationError(f"Unsupported scheduling algorithm: {algorithm}")
        if not jobs:
            raise ValidationError("Cannot schedule an empty workload.")
        for job in jobs:
            if job.burst_time <= 0:
                raise ValidationError(f"Job '{job.job_id}' must have burst_time > 0.")
            if job.arrival_time < 0:
                raise ValidationError(f"Job '{job.job_id}' cannot have negative arrival_time.")
        if algo == "ROUND_ROBIN" and quantum <= 0:
            raise ValidationError("Round Robin time quantum must be >= 1.")

        if algo == "FCFS":
            return self._run_fcfs(jobs)
        if algo == "SJF":
            return self._run_non_preemptive(jobs, key_fn=lambda item: (item[1].burst_time, item[1].arrival_time, item[0]), algorithm="SJF")
        if algo == "PRIORITY":
            return self._run_non_preemptive(jobs, key_fn=lambda item: (item[1].priority, item[1].arrival_time, item[0]), algorithm="PRIORITY")
        return self._run_round_robin(jobs, quantum=quantum)

    def _run_fcfs(self, jobs: List[Job]) -> SchedulingReport:
        indexed = sorted(enumerate(jobs), key=lambda item: (item[1].arrival_time, item[0]))
        current_time = 0
        entries: List[SchedulingResultEntry] = []
        gantt: List[GanttSlice] = []

        for _, job in indexed:
            if current_time < job.arrival_time:
                current_time = job.arrival_time
            start_time = current_time
            completion_time = start_time + job.burst_time
            current_time = completion_time
            gantt.append(GanttSlice(job_id=job.job_id, start_time=start_time, end_time=completion_time))
            entries.append(self._build_entry(job, start_time, completion_time))

        return self._build_report("FCFS", None, entries, gantt)

    def _run_non_preemptive(self, jobs: List[Job], key_fn, algorithm: str) -> SchedulingReport:
        remaining = list(enumerate(jobs))
        current_time = 0
        entries: List[SchedulingResultEntry] = []
        gantt: List[GanttSlice] = []

        while remaining:
            arrived = [item for item in remaining if item[1].arrival_time <= current_time]
            if not arrived:
                next_arrival = min(item[1].arrival_time for item in remaining)
                current_time = next_arrival
                arrived = [item for item in remaining if item[1].arrival_time <= current_time]
            chosen = min(arrived, key=key_fn)
            remaining.remove(chosen)
            _, job = chosen
            start_time = current_time
            completion_time = start_time + job.burst_time
            current_time = completion_time
            gantt.append(GanttSlice(job_id=job.job_id, start_time=start_time, end_time=completion_time))
            entries.append(self._build_entry(job, start_time, completion_time))

        return self._build_report(algorithm, None, entries, gantt)

    def _run_round_robin(self, jobs: List[Job], quantum: int) -> SchedulingReport:
        indexed = sorted(enumerate(jobs), key=lambda item: (item[1].arrival_time, item[0]))
        remaining_burst: Dict[str, int] = {job.job_id: job.burst_time for _, job in indexed}
        first_start: Dict[str, Optional[int]] = {job.job_id: None for _, job in indexed}
        completion_times: Dict[str, int] = {}
        gantt: List[GanttSlice] = []

        ready_queue: deque = deque()
        next_idx = 0
        current_time = 0
        total_jobs = len(indexed)

        while len(completion_times) < total_jobs:
            while next_idx < total_jobs and indexed[next_idx][1].arrival_time <= current_time:
                ready_queue.append(indexed[next_idx][1])
                next_idx += 1

            if not ready_queue:
                current_time = indexed[next_idx][1].arrival_time
                while next_idx < total_jobs and indexed[next_idx][1].arrival_time <= current_time:
                    ready_queue.append(indexed[next_idx][1])
                    next_idx += 1

            current_job = ready_queue.popleft()
            if first_start[current_job.job_id] is None:
                first_start[current_job.job_id] = current_time

            exec_time = min(quantum, remaining_burst[current_job.job_id])
            slice_start = current_time
            current_time += exec_time
            remaining_burst[current_job.job_id] -= exec_time
            gantt.append(GanttSlice(job_id=current_job.job_id, start_time=slice_start, end_time=current_time))

            while next_idx < total_jobs and indexed[next_idx][1].arrival_time <= current_time:
                ready_queue.append(indexed[next_idx][1])
                next_idx += 1

            if remaining_burst[current_job.job_id] > 0:
                ready_queue.append(current_job)
            else:
                completion_times[current_job.job_id] = current_time

        entries: List[SchedulingResultEntry] = []
        for _, job in indexed:
            start_t = first_start[job.job_id] if first_start[job.job_id] is not None else 0
            comp_t = completion_times[job.job_id]
            entries.append(self._build_entry(job, start_t, comp_t))

        return self._build_report("ROUND_ROBIN", quantum, entries, gantt)

    def _build_entry(self, job: Job, start_time: int, completion_time: int) -> SchedulingResultEntry:
        turnaround_time = completion_time - job.arrival_time
        waiting_time = turnaround_time - job.burst_time
        response_time = start_time - job.arrival_time
        return SchedulingResultEntry(
            job_id=job.job_id,
            name=job.name,
            arrival_time=job.arrival_time,
            burst_time=job.burst_time,
            priority=job.priority,
            start_time=start_time,
            completion_time=completion_time,
            turnaround_time=turnaround_time,
            waiting_time=waiting_time,
            response_time=response_time,
        )

    def _build_report(
        self,
        algorithm: str,
        quantum: Optional[int],
        entries: List[SchedulingResultEntry],
        gantt: List[GanttSlice],
    ) -> SchedulingReport:
        count = len(entries)
        avg_waiting = sum(e.waiting_time for e in entries) / count
        avg_turnaround = sum(e.turnaround_time for e in entries) / count
        avg_response = sum(e.response_time for e in entries) / count
        min_arrival = min(e.arrival_time for e in entries)
        max_completion = max(e.completion_time for e in entries)
        total_span = max_completion - min_arrival
        throughput = (count / total_span) if total_span > 0 else 0.0
        return SchedulingReport(
            algorithm=algorithm,
            quantum=quantum,
            entries=entries,
            gantt_chart=gantt,
            avg_waiting_time=round(avg_waiting, 3),
            avg_turnaround_time=round(avg_turnaround, 3),
            avg_response_time=round(avg_response, 3),
            throughput=round(throughput, 4),
            total_time=max_completion,
        )

