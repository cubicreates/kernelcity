from pathlib import Path
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from RES.models import SchedulingReport


class ChartGenerator:
    def __init__(self, reports_dir: Path):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_scheduling_comparison_chart(
        self,
        reports: Dict[str, SchedulingReport],
        filename: str = "scheduling_comparison.png",
    ) -> Path:
        algorithms = list(reports.keys())
        avg_wait = np.array([reports[a].avg_waiting_time for a in algorithms], dtype=float)
        avg_turn = np.array([reports[a].avg_turnaround_time for a in algorithms], dtype=float)
        avg_resp = np.array([reports[a].avg_response_time for a in algorithms], dtype=float)

        x = np.arange(len(algorithms))
        width = 0.25

        fig, ax = plt.subplots(figsize=(9, 5))
        bars_w = ax.bar(x - width, avg_wait, width=width, label="Avg Waiting Time (units)")
        bars_t = ax.bar(x, avg_turn, width=width, label="Avg Turnaround Time (units)")
        bars_r = ax.bar(x + width, avg_resp, width=width, label="Avg Response Time (units)")

        for bars in (bars_w, bars_t, bars_r):
            ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)

        ax.set_title("CPU Scheduling Algorithm Performance Comparison")
        ax.set_xlabel("Scheduling Algorithm")
        ax.set_ylabel("Time (CPU units)")
        ax.set_xticks(x)
        ax.set_xticklabels(algorithms)
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        out_path = self.reports_dir / filename
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def generate_memory_comparison_chart(
        self,
        memory_results: Dict[str, Dict[str, object]],
        filename: str = "memory_comparison.png",
    ) -> Path:
        strategies = list(memory_results.keys())
        allocated = np.array([memory_results[s]["metrics"]["allocated_memory"] for s in strategies], dtype=float)
        internal_frag = np.array([memory_results[s]["metrics"]["internal_fragmentation"] for s in strategies], dtype=float)
        free_mem = np.array([memory_results[s]["metrics"]["free_memory"] for s in strategies], dtype=float)

        x = np.arange(len(strategies))
        width = 0.25

        fig, ax = plt.subplots(figsize=(9, 5))
        bars_a = ax.bar(x - width, allocated, width=width, label="Allocated Memory (KB)")
        bars_i = ax.bar(x, internal_frag, width=width, label="Internal Fragmentation (KB)")
        bars_f = ax.bar(x + width, free_mem, width=width, label="Remaining Free (KB)")

        for bars in (bars_a, bars_i, bars_f):
            ax.bar_label(bars, fmt="%.0f", padding=2, fontsize=8)

        ax.set_title("Memory Allocation Strategy Comparison")
        ax.set_xlabel("Allocation Strategy")
        ax.set_ylabel("Memory (KB)")
        ax.set_xticks(x)
        ax.set_xticklabels(strategies)
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        out_path = self.reports_dir / filename
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def generate_gantt_chart_png(
        self,
        report: SchedulingReport,
        filename: str = "gantt_chart.png",
    ) -> Path:
        job_ids = list(dict.fromkeys(sl.job_id for sl in report.gantt_chart))
        y_map = {jid: idx for idx, jid in enumerate(job_ids)}

        fig, ax = plt.subplots(figsize=(9, max(3.5, len(job_ids) * 0.7 + 1.5)))
        for sl in report.gantt_chart:
            y_pos = y_map[sl.job_id]
            duration = sl.end_time - sl.start_time
            ax.broken_barh([(sl.start_time, duration)], (y_pos - 0.3, 0.6))
            ax.text(sl.start_time + duration / 2, y_pos, sl.job_id, ha="center", va="center", color="white", fontsize=8)

        ax.set_yticks(list(y_map.values()))
        ax.set_yticklabels(job_ids)
        ax.set_xlabel("CPU Time (units)")
        ax.set_ylabel("Process / Job")
        title_q = f" (Quantum={report.quantum})" if report.quantum is not None else ""
        ax.set_title(f"Gantt Timeline — {report.algorithm}{title_q}")
        ax.grid(axis="x", linestyle="--", alpha=0.4)

        out_path = self.reports_dir / filename
        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path
