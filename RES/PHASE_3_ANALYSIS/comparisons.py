from typing import Dict, List

import numpy as np
import pandas as pd

from RES.models import Job, SchedulingReport
from RES.PHASE_2_CORE_MODULES.memory_manager import MemoryManager
from RES.PHASE_2_CORE_MODULES.scheduler import Scheduler


def compare_scheduling_algorithms(
    scheduler: Scheduler,
    jobs: List[Job],
    quantum: int = 2,
) -> Dict[str, object]:
    reports: Dict[str, SchedulingReport] = {}
    rows: List[Dict[str, object]] = []
    for algo in Scheduler.SUPPORTED_ALGORITHMS:
        rep = scheduler.schedule(jobs, algorithm=algo, quantum=quantum)
        reports[algo] = rep
        waits = np.array([e.waiting_time for e in rep.entries], dtype=float)
        rows.append(
            {
                "algorithm": algo,
                "quantum": rep.quantum if rep.quantum is not None else np.nan,
                "job_count": len(rep.entries),
                "avg_waiting_time": rep.avg_waiting_time,
                "std_waiting_time": round(float(np.std(waits)), 3),
                "avg_turnaround_time": rep.avg_turnaround_time,
                "avg_response_time": rep.avg_response_time,
                "throughput": rep.throughput,
                "total_time": rep.total_time,
            }
        )

    df = pd.DataFrame(rows)
    best_wait_algo = str(df.loc[df["avg_waiting_time"].idxmin(), "algorithm"])
    best_turn_algo = str(df.loc[df["avg_turnaround_time"].idxmin(), "algorithm"])
    best_resp_algo = str(df.loc[df["avg_response_time"].idxmin(), "algorithm"])

    observations = [
        f"{best_wait_algo} achieved the lowest average waiting time ({reports[best_wait_algo].avg_waiting_time:.3f}) for this workload.",
        f"{best_turn_algo} achieved the lowest average turnaround time ({reports[best_turn_algo].avg_turnaround_time:.3f}).",
        f"{best_resp_algo} achieved the lowest average response time ({reports[best_resp_algo].avg_response_time:.3f}).",
    ]
    if best_wait_algo == "SJF":
        observations.append(
            "SJF minimized average waiting time on this dataset, though in dynamic workloads it can cause starvation for longer jobs."
        )
    if reports["ROUND_ROBIN"].avg_response_time <= reports["FCFS"].avg_response_time:
        observations.append(
            f"Round Robin (quantum={quantum}) bounded initial response latency by rotating ready jobs."
        )

    return {
        "reports": reports,
        "dataframe": df,
        "best_waiting": best_wait_algo,
        "best_turnaround": best_turn_algo,
        "best_response": best_resp_algo,
        "observations": observations,
    }


def compare_memory_strategies(
    memory_manager: MemoryManager,
    block_sizes: List[int],
    requests: List[Dict[str, object]],
) -> Dict[str, object]:
    results: Dict[str, Dict[str, object]] = {}
    rows: List[Dict[str, object]] = []
    for strategy in MemoryManager.STRATEGIES:
        sim = memory_manager.simulate_strategy(block_sizes, requests, strategy)
        results[strategy] = sim
        m = sim["metrics"]
        total_mem = max(1, m["total_memory"])
        utilisation_pct = round(float(np.divide(m["allocated_memory"], total_mem) * 100.0), 2)
        rows.append(
            {
                "strategy": strategy,
                "allocations_succeeded": m["allocations_succeeded"],
                "allocations_failed": m["allocations_failed"],
                "allocated_memory_kb": m["allocated_memory"],
                "free_memory_kb": m["free_memory"],
                "utilisation_percent": utilisation_pct,
                "internal_fragmentation_kb": m["internal_fragmentation"],
                "external_fragmentation_kb": m["external_fragmentation"],
            }
        )

    df = pd.DataFrame(rows)
    best_alloc = str(df.loc[df["allocations_succeeded"].idxmax(), "strategy"])
    least_internal = str(df.loc[df["internal_fragmentation_kb"].idxmin(), "strategy"])

    observations = [
        f"{best_alloc} satisfied the highest number of requests ({results[best_alloc]['metrics']['allocations_succeeded']}/{len(requests)}).",
        f"{least_internal} produced the lowest internal fragmentation ({results[least_internal]['metrics']['internal_fragmentation']} KB).",
    ]
    return {
        "results": results,
        "dataframe": df,
        "best_allocation_rate": best_alloc,
        "lowest_internal_fragmentation": least_internal,
        "observations": observations,
    }
