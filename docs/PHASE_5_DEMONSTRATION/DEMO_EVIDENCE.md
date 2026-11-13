# Phase 5 — Demonstration Evidence (20 Marks)

## 1. Reproducible Sample Inputs (`data/demo/`)
- `data/demo/sample_metrics.csv`:
  ```csv
  process,cpu_burst,memory_kb,priority
  Indexer,6,120,2
  LogParser,3,80,1
  Archiver,8,200,4
  Verifier,2,60,3
  ```
- `data/demo/sample_worker.py` (approved Python worker script)
- `data/demo/sample_docs/readme_demo.txt` (backup/compression sample)

## 2. Observed Execution Trace (`KernelCity.exe` / `main.py`)
Running Demo Centre Option `1` (**Complete City Walkthrough**) and Option `8` (**Analytics & CSV Export**):
1. Executes `DEMO_CSV_Summary` (`process_csv` using `pandas`) and `DEMO_Python_Worker` (`run_python_script`) as real host subprocesses with real PIDs.
2. Runs FCFS, SJF, Priority, and Round Robin on the common scheduling workload and generates `reports/demo_scheduling_comparison.png`.
3. Runs First Fit, Best Fit, and Worst Fit on independent pool copies and generates `reports/demo_memory_comparison.png`.
4. Verifies Banker's safe sequence (`P1 -> P3 -> P4 -> P0 -> P2`) and rejects unsafe request `[0, 2, 0]` for `P0`.
5. Detects deadlock among `P0, P1, P2` and verifies deadlock-free state after terminating `P0` in the model.
6. Captures LIVE host CPU, RAM, disk, and process counts via `psutil`.
7. Exports `reports/complete_walkthrough_*.txt` and `reports/complete_walkthrough_*.json`.

## 3. Standalone Packaging
- Multi-resolution retro pixel-art icon: `assets/KernelCity.ico`
- Standalone Windows executable: `dist/KernelCity/KernelCity.exe`
