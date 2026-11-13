# Phase 4 — Testing and Reliability Evidence (20 Marks)

## 1. Validation, Error Handling & Logging
- **Input Validation (`RES/PHASE_4_TESTING/validation.py`):** `InputValidator` validates non-empty strings, integer/float bounds, choice membership, integer vectors, and project-scoped path sandboxing (`validate_safe_path`).
- **Typed Exceptions (`RES/PHASE_4_TESTING/error_handling.py`):** `KernelCityError`, `ValidationError`, `PathValidationError`, `ResourceValidationError`, and `ProcessExecutionError` ensure failures are caught and reported cleanly without silent swallowing.
- **Activity Logging (`RES/event_logger.py`):** Records startup, shutdown, job submissions, process outcomes, demo runs, report exports, and errors to `logs/kernel_city.log` and SQLite `events`.

## 2. Automated Test Suite (`py -m pytest -v`)
**Observed Result:** **22 passed in 20.66s** across 6 test modules:

| Test File | Coverage |
| --- | --- |
| `tests/test_scheduler.py` | Empty workload, invalid quantum, zero burst, single process, FCFS/SJF/Priority tie-breaking, Round Robin exact metrics |
| `tests/test_memory_manager.py` | Empty/negative blocks, First/Best/Worst Fit, exact fit, deallocation, internal & external fragmentation |
| `tests/test_resource_and_deadlock.py` | Banker's safe/unsafe requests, invalid index/negative/exceeds-available/exceeds-need, deadlock detection, RAG edges, recovery |
| `tests/test_process_storage_monitor.py` | Real subprocesses (`process_csv`, `system_info_task`), non-zero exit code, timeout, cancellation, path traversal block, StorageManager, live `SystemMonitor` |
| `tests/test_persistence_analytics_gui.py` | SQLite persistence across `KernelEngine` restart, complete walkthrough & reports, GUI-to-engine sharing |
| `tests/test_csv_exports_and_v2.py` | V2 4-district map, process state transitions, `create_pool_from_total`, `pandas` DataFrame columns, PNG Gantt chart, and all 7 CSV exporters (headers, escaping, overwrite confirmation, invalid directory) |
