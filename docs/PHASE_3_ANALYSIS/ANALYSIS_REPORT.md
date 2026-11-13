# Phase 3 — Analysis and Comparison Report (20 Marks)

## 1. CPU Scheduling Comparison (Common Demo Dataset)
**Workload:** `DEMO-P1` (Arr=0, Burst=6, Prio=2), `DEMO-P2` (Arr=1, Burst=3, Prio=1), `DEMO-P3` (Arr=2, Burst=8, Prio=4), `DEMO-P4` (Arr=3, Burst=2, Prio=3), Round Robin Quantum = `2`.

Computed via `AnalyticsEngine.run_scheduling_analysis()` (`pandas.DataFrame` + `numpy`):

| Algorithm | Quantum | Jobs | Avg Waiting | Std Waiting | Avg Turnaround | Avg Response | Throughput | Total Time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FCFS | - | 4 | 6.50 | 5.025 | 11.25 | 6.50 | 0.2105 | 19 |
| SJF | - | 4 | 4.75 | 3.491 | 9.50 | 4.75 | 0.2105 | 19 |
| PRIORITY | - | 4 | 5.00 | 3.240 | 9.75 | 5.00 | 0.2105 | 19 |
| ROUND_ROBIN | 2 | 4 | 7.50 | 1.658 | 12.25 | 2.00 | 0.2105 | 19 |

### Technical Observations
- **SJF** achieved the lowest average waiting time (`4.75`) and lowest average turnaround time (`9.50`) on this workload, though in dynamic workloads it can cause starvation for longer jobs.
- **Round Robin (quantum=2)** achieved the lowest average response time (`2.00`) and lowest waiting-time standard deviation (`1.658`) by rotating ready jobs every time slice.
- **Chart:** `reports/demo_scheduling_comparison.png`

## 2. Memory Allocation Comparison (Common Demo Dataset)
**Partitions (KB):** `[100, 500, 200, 300, 600]` (Total: `1700 KB`)  
**Requests (KB):** `DEMO-PROC-1` (`212`), `DEMO-PROC-2` (`417`), `DEMO-PROC-3` (`112`), `DEMO-PROC-4` (`426`).

Computed via `MemoryManager.simulate_strategy()` on independent copies:

| Strategy | Succeeded | Failed | Allocated (KB) | Free (KB) | Utilisation (%) | Internal Frag (KB) | External Frag (KB) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FIRST_FIT | 3 | 1 | 741 | 400 | 43.59 | 559 | 100 |
| BEST_FIT | 4 | 0 | 1167 | 100 | 68.65 | 433 | 0 |
| WORST_FIT | 3 | 1 | 741 | 300 | 43.59 | 659 | 100 |

### Technical Observations
- **Best Fit** satisfied all 4 requests (`4/4`, `68.65%` utilisation) with the lowest internal fragmentation (`433 KB`) because it preserved the `600 KB` block for the `426 KB` request.
- **First Fit** and **Worst Fit** both failed on the final `426 KB` request because earlier allocations consumed the largest blocks.
- **Chart:** `reports/demo_memory_comparison.png`

## 3. Resource Allocation & Deadlock Analysis
- **Banker's Algorithm:** Verifies `Need = Max - Allocation`, generates safe sequences (e.g. `P1 -> P3 -> P4 -> P0 -> P2`), and rolls back unsafe requests.
- **Deadlock Detection:** Multi-instance detection identifies circular waits (e.g. `P0, P1, P2` deadlocked) and demonstrates recovery by releasing simulated process resources.
- **CSV Exports:** All scheduling, memory, resource, deadlock, monitoring, and history results export cleanly via `pandas.DataFrame.to_csv()`.
