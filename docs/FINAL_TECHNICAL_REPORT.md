# KERNEL CITY — Final Technical Report

**Submitted by:** Adit Ghosh  
**Roll Number:** 2401350016  
**Semester:** V  
**Course:** B.Tech CSE Full Stack Development  

## 1. Executive Summary
**KERNEL CITY** is an integrated terminal-based Operating System Resource Management and Monitoring Environment built in Python and Bash. It pairs a 16-bit overworld navigation experience (`GUI/`) with a modular, independently testable resource engine (`RES/`), focusing on three core OS modules: Process Management & CPU Scheduling, Memory Management, and Resource Allocation & Deadlock Management.

## 2. System Architecture (Phase 1)
- **Entry Point (`main.py`):** Creates a single shared `KernelEngine` instance and passes it to `KernelCityGUI`. Supports both source execution (`py main.py` / `./launch.sh`) and standalone frozen execution (`dist/KernelCity/KernelCity.exe` with `--kc-worker`).
- **Presentation (`GUI/`):** Built with `rich`, featuring a 74×17 2D pixel-art overworld, animated kart driving (`EXPLORE`, `QUICK`, `SKIP`), Free-Drive Kart mode (`K`), 4 districts, 14 functional buildings, City/District maps (`M`), and Demo Centre (`D`).
- **Resource Engine (`RES/`):** Zero imports from `GUI/`. Persists state in SQLite (`data/kernel_city.db`) and logs to `logs/kernel_city.log`.

## 3. Core OS Modules (Phase 2)
1. **Process Management & CPU Scheduling:** Enforces `VALID_STATE_TRANSITIONS` (`NEW`, `READY`, `RUNNING`, `WAITING`, `COMPLETED`, `TERMINATED`, `FAILED`, `CANCELLED`), executes approved subprocesses (`shell=False`), and implements FCFS, non-preemptive SJF, non-preemptive Priority, and Round Robin with exact metric calculations and Gantt charts.
2. **Memory Management:** Implements First Fit, Best Fit, and Worst Fit over configurable partition pools, calculating internal and external fragmentation and running non-mutating comparisons.
3. **Resource Allocation & Deadlock Management:** Implements Banker's Algorithm (`Need = Max - Allocation`) with safe-sequence verification and rollback, plus multi-instance deadlock detection, Resource Allocation Graph edges, and controlled model recovery.

## 4. Analysis, Comparisons & CSV Exports (Phase 3)
Uses `pandas` and `numpy` for comparative tables and statistics, `matplotlib` for labelled comparison and Gantt PNG charts, and `pandas.DataFrame.to_csv()` for application-wide CSV exports with filename, directory, and overwrite validation.

## 5. Testing & Verification (Phase 4 & Phase 5)
- **Automated Tests:** `py -m pytest -v` passed **22/22 tests** covering all core algorithms, validation, error handling, subprocess timeouts/cancellations, SQLite persistence, CSV exports, and GUI-to-engine integration.
- **Executable Verification:** `dist\KernelCity\KernelCity.exe` passed end-to-end walkthrough and analytics/CSV smoke tests (`exit code 0`).

## 6. Known Limitations
- CPU scheduling and memory allocation operate on application-managed workloads and pools rather than replacing the host OS kernel scheduler or physical RAM allocator.
- Host process termination in System Watchtower is restricted to non-protected processes permitted by OS user privileges.
