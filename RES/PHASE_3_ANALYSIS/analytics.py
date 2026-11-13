import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from RES.database import DatabaseManager
from RES.models import (
    ExecutionRecord,
    Job,
    MemoryAllocationRecord,
    MemoryBlock,
    ResourceState,
    SchedulingReport,
)
from RES.PHASE_2_CORE_MODULES.memory_manager import MemoryManager
from RES.PHASE_2_CORE_MODULES.scheduler import Scheduler
from RES.PHASE_3_ANALYSIS.comparisons import compare_memory_strategies, compare_scheduling_algorithms
from RES.PHASE_3_ANALYSIS.visualisation import ChartGenerator
from RES.PHASE_4_TESTING.error_handling import ValidationError
from RES.PHASE_4_TESTING.validation import InputValidator


class AnalyticsEngine:
    def __init__(self, reports_dir: Path, db: DatabaseManager, base_dir: Optional[Path] = None):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.base_dir = Path(base_dir) if base_dir else self.reports_dir.parent
        self.db = db
        self.charts = ChartGenerator(self.reports_dir)

    def resolve_export_path(
        self,
        filename: str,
        extension: str,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        clean_name = InputValidator.require_non_empty(filename, "Filename")
        if any(ch in clean_name for ch in ("/", "\\", "..")):
            raise ValidationError("Filename must not contain path separators or '..'.")
        if not clean_name.lower().endswith(extension.lower()):
            clean_name = f"{clean_name}{extension}"

        if output_dir and output_dir.strip():
            target_dir = InputValidator.validate_safe_path(
                output_dir.strip(),
                allowed_roots=[self.reports_dir, self.base_dir],
                must_exist=False,
            )
        else:
            target_dir = self.reports_dir

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValidationError(f"Cannot create output directory '{target_dir}': {exc}") from exc

        out_path = target_dir / clean_name
        if out_path.exists() and not overwrite:
            raise ValidationError(f"File '{out_path}' already exists. Confirm overwrite to replace it.")
        return out_path

    def run_scheduling_analysis(self, scheduler: Scheduler, jobs: List[Job], quantum: int = 2) -> Dict[str, Any]:
        comparison = compare_scheduling_algorithms(scheduler, jobs, quantum=quantum)
        for algo, report in comparison["reports"].items():
            self.db.record_scheduling_run(
                algorithm=algo,
                quantum=report.quantum,
                job_count=len(report.entries),
                avg_waiting=report.avg_waiting_time,
                avg_turnaround=report.avg_turnaround_time,
                avg_response=report.avg_response_time,
                throughput=report.throughput,
            )
        return comparison

    def run_memory_analysis(
        self,
        memory_manager: MemoryManager,
        block_sizes: List[int],
        requests: List[Dict[str, object]],
    ) -> Dict[str, Any]:
        return compare_memory_strategies(memory_manager, block_sizes, requests)

    def export_csv_report(
        self,
        report_name: str,
        rows: List[Dict[str, Any]],
        output_dir: Optional[str] = None,
        overwrite: bool = False,
        use_timestamp: bool = True,
    ) -> Path:
        stem = f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if use_timestamp else report_name
        out_path = self.resolve_export_path(stem, ".csv", output_dir=output_dir, overwrite=overwrite)
        if not rows:
            pd.DataFrame([{"message": "No records available"}]).to_csv(out_path, index=False, encoding="utf-8")
            return out_path
        df = pd.DataFrame(rows)
        df.to_csv(out_path, index=False, encoding="utf-8")
        return out_path

    def export_scheduling_csv(
        self,
        report: SchedulingReport,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        stamp = datetime.now().isoformat(timespec="seconds")
        rows = [
            {
                "timestamp": stamp,
                "algorithm": report.algorithm,
                "quantum": report.quantum if report.quantum is not None else "",
                "process_id": e.job_id,
                "process_name": e.name,
                "arrival_time": e.arrival_time,
                "burst_time": e.burst_time,
                "priority": e.priority,
                "start_time": e.start_time,
                "completion_time": e.completion_time,
                "waiting_time": e.waiting_time,
                "turnaround_time": e.turnaround_time,
                "response_time": e.response_time,
            }
            for e in report.entries
        ]
        name = filename or f"scheduling_{report.algorithm.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_gantt_csv(
        self,
        report: SchedulingReport,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        rows = [
            {
                "algorithm": report.algorithm,
                "quantum": report.quantum if report.quantum is not None else "",
                "process_id": sl.job_id,
                "start_time": sl.start_time,
                "end_time": sl.end_time,
                "duration": sl.end_time - sl.start_time,
            }
            for sl in report.gantt_chart
        ]
        name = filename or f"gantt_{report.algorithm.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_scheduling_comparison_csv(
        self,
        comparison: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        stamp = datetime.now().isoformat(timespec="seconds")
        rows = []
        for algo, rep in comparison["reports"].items():
            rows.append(
                {
                    "timestamp": stamp,
                    "algorithm": algo,
                    "quantum": rep.quantum if rep.quantum is not None else "",
                    "job_count": len(rep.entries),
                    "avg_waiting_time": rep.avg_waiting_time,
                    "avg_turnaround_time": rep.avg_turnaround_time,
                    "avg_response_time": rep.avg_response_time,
                    "throughput": rep.throughput,
                    "total_time": rep.total_time,
                }
            )
        name = filename or f"scheduling_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_memory_csv(
        self,
        records: List[MemoryAllocationRecord],
        blocks: List[MemoryBlock],
        metrics: Dict[str, int],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        block_sizes = {b.block_id: b.size for b in blocks}
        rows = []
        for rec in records:
            rows.append(
                {
                    "timestamp": rec.timestamp,
                    "allocation_id": rec.allocation_id,
                    "process_id": rec.reference,
                    "strategy": rec.strategy,
                    "requested_kb": rec.requested_size,
                    "allocated_block": rec.allocated_block_id or "NONE",
                    "allocated_block_size_kb": block_sizes.get(rec.allocated_block_id, 0) if rec.allocated_block_id else 0,
                    "remaining_free_kb": rec.remaining_free_space,
                    "status": rec.status,
                    "total_internal_frag_kb": metrics["internal_fragmentation"],
                    "total_external_frag_kb": metrics["external_fragmentation"],
                }
            )
        name = filename or f"memory_allocations_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_memory_comparison_csv(
        self,
        comparison: Dict[str, Any],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        stamp = datetime.now().isoformat(timespec="seconds")
        rows = []
        for strategy, data in comparison["results"].items():
            m = data["metrics"]
            rows.append(
                {
                    "timestamp": stamp,
                    "strategy": strategy,
                    "total_memory_kb": m["total_memory"],
                    "requested_memory_kb": m.get("requested_memory", 0),
                    "allocated_memory_kb": m["allocated_memory"],
                    "free_memory_kb": m["free_memory"],
                    "free_blocks_count": m.get("free_blocks_count", 0),
                    "internal_fragmentation_kb": m["internal_fragmentation"],
                    "external_fragmentation_kb": m["external_fragmentation"],
                    "allocations_succeeded": m["allocations_succeeded"],
                    "allocations_failed": m["allocations_failed"],
                }
            )
        name = filename or f"memory_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_resource_allocation_csv(
        self,
        state: ResourceState,
        safety_result: bool,
        safe_sequence: List[str],
        last_request: Optional[List[int]] = None,
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        stamp = datetime.now().isoformat(timespec="seconds")
        res_header = "|".join(state.resource_types)
        avail_str = "|".join(str(x) for x in state.available)
        req_str = "|".join(str(x) for x in last_request) if last_request else ""
        seq_str = " -> ".join(safe_sequence)
        rows = []
        for idx, pname in enumerate(state.process_names):
            rows.append(
                {
                    "timestamp": stamp,
                    "process": pname,
                    "resource_types": res_header,
                    "available_vector": avail_str,
                    "allocation_vector": "|".join(str(x) for x in state.allocation[idx]),
                    "maximum_vector": "|".join(str(x) for x in state.maximum[idx]),
                    "need_vector": "|".join(str(x) for x in state.need[idx]),
                    "last_request": req_str,
                    "is_safe": safety_result,
                    "safe_sequence": seq_str,
                }
            )
        name = filename or f"resource_allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_deadlock_csv(
        self,
        process_names: List[str],
        resource_types: List[str],
        allocation: List[List[int]],
        request: List[List[int]],
        detection_result: Dict[str, Any],
        recovery_summary: str = "",
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        stamp = datetime.now().isoformat(timespec="seconds")
        res_header = "|".join(resource_types)
        deadlocked_set = set(detection_result.get("deadlocked_processes", []))
        rows = []
        for idx, pname in enumerate(process_names):
            rows.append(
                {
                    "timestamp": stamp,
                    "process": pname,
                    "resource_types": res_header,
                    "allocation_vector": "|".join(str(x) for x in allocation[idx]),
                    "request_vector": "|".join(str(x) for x in request[idx]),
                    "in_deadlock": pname in deadlocked_set,
                    "detection_summary": detection_result.get("summary", ""),
                    "recovery_action": recovery_summary,
                }
            )
        name = filename or f"deadlock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_monitoring_csv(
        self,
        snapshots: List[Dict[str, Any]],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        rows = [
            {
                "timestamp": s["timestamp"],
                "source": s.get("source", "LIVE"),
                "cpu_percent": s["cpu_percent"],
                "ram_percent": s["ram_percent"],
                "ram_available_gb": s["ram_available_gb"],
                "disk_percent": s["disk_percent"],
                "active_processes": s["active_processes"],
                "status": s["status"],
            }
            for s in snapshots
        ]
        name = filename or f"system_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_history_csv(
        self,
        records: List[ExecutionRecord],
        filename: Optional[str] = None,
        output_dir: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        rows = [
            {
                "job_id": r.job_id,
                "execution_timestamp": r.execution_timestamp,
                "duration_seconds": r.duration,
                "outcome": r.outcome,
                "exit_code": r.exit_code if r.exit_code is not None else "",
                "resource_observations": r.resource_observations,
                "output_location": r.output_location or "",
            }
            for r in records
        ]
        name = filename or f"execution_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return self.export_csv_report(name, rows, output_dir=output_dir, overwrite=overwrite, use_timestamp=False)

    def export_json_report(
        self,
        report_name: str,
        payload: Dict[str, Any],
        output_dir: Optional[str] = None,
        overwrite: bool = False,
        use_timestamp: bool = True,
    ) -> Path:
        stem = f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if use_timestamp else report_name
        out_path = self.resolve_export_path(stem, ".json", output_dir=output_dir, overwrite=overwrite)
        serializable = {
            "report_name": report_name,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "data": payload,
        }
        out_path.write_text(json.dumps(serializable, indent=2, default=self._json_default), encoding="utf-8")
        return out_path

    def export_text_report(
        self,
        report_name: str,
        title: str,
        sections: Dict[str, List[str]],
        output_dir: Optional[str] = None,
        overwrite: bool = False,
        use_timestamp: bool = True,
    ) -> Path:
        stem = f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if use_timestamp else report_name
        out_path = self.resolve_export_path(stem, ".txt", output_dir=output_dir, overwrite=overwrite)
        lines = [
            f"KERNEL CITY REPORT: {title}",
            f"Generated At: {datetime.now().isoformat(timespec='seconds')}",
            "=" * 60,
        ]
        for heading, items in sections.items():
            lines.append("")
            lines.append(f"[{heading}]")
            lines.extend(items if items else ["(none)"])
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_path

    @staticmethod
    def _json_default(obj: Any) -> Any:
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        return str(obj)
