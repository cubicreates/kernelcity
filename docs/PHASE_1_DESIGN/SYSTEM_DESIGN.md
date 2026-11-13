# Phase 1 — System Design and Planning (20 Marks)

**Author:** Adit Ghosh | **Roll Number:** 2401350016 | **Semester:** V | **Course:** B.Tech CSE Full Stack Development

## 1. Problem Statement
Operating systems concepts—CPU scheduling, memory allocation, deadlock analysis, process management, and system monitoring—are frequently taught as isolated exercises. **KERNEL CITY** unifies these concepts into one cohesive, interactive terminal environment backed by a shared resource engine.

## 2. Project Objectives
- Provide a retro 16-bit overworld terminal interface (`GUI/`) connected to a modular resource engine (`RES/`).
- Focus deeply on three core OS modules:
  1. **Process Management & CPU Scheduling** (Job House, Scheduling Plaza, Process Garage)
  2. **Memory Management** (Memory Centre, Allocation Laboratory, Memory Analytics Office)
  3. **Resource Allocation & Deadlock Management** (Resource Allocation Office, Banker's Algorithm Centre, Deadlock Court)
- Support these core modules with lightweight host monitoring (`psutil`), storage management, SQLite persistence, `pandas`/`numpy` analytics, `matplotlib` charts, and application-wide CSV exports.

## 3. Scope & Engineering Boundaries
- **Included:** 4-district 2D terminal overworld, Free-Drive Kart navigation (`K`), validated subprocess execution (`shell=False` and frozen `--kc-worker`), 4 CPU schedulers, 3 memory strategies, Banker's Algorithm, multi-instance deadlock detection, SQLite persistence, and CSV/JSON/TXT/PNG exports.
- **Explicit Boundaries:** CPU scheduling and memory allocation operate on application-managed workloads and memory pools rather than modifying the host OS kernel scheduler or physical RAM.

## 4. Architecture Diagram
```
+-------------------------------------------------------------------+
|                             main.py                               |
|   Initialises KernelEngine once -> injects into KernelCityGUI     |
|   Supports frozen .exe (--kc-worker) and source Python execution  |
+---------------------------------+---------------------------------+
                                  |
         +------------------------+------------------------+
         v                                                 v
+-------------------------+                       +-------------------------+
|          GUI/           |  calls public APIs    |          RES/           |
|  overworld.py, city.py  | --------------------> |  kernel.py (KernelEngine)|
|  dashboard.py, maps.py  |                       |  PHASE_1_DESIGN/        |
|  districts.py, menus.py | <-------------------- |  PHASE_2_CORE_MODULES/  |
|  buildings.py, widgets  |  returns models/data  |  PHASE_3_ANALYSIS/      |
+-------------------------+                       |  PHASE_4_TESTING/       |
                                                  |  PHASE_5_DEMONSTRATION/ |
                                                  +------------+------------+
                                                               |
                                  +----------------------------+----------------------------+
                                  v                            v                            v
                        +-------------------+        +-------------------+        +-------------------+
                        | SQLite Database   |        | Host OS / psutil  |        | Analytics & Files |
                        | kernel_city.db    |        | subprocess (safe) |        | pandas, PNG, CSV  |
                        +-------------------+        +-------------------+        +-------------------+
```

## 5. Input / Output Workflow
`USER INPUT -> InputValidator -> KernelEngine -> Core Module -> Result + SQLite/Log Recording -> Rich Display + Optional CSV/JSON/PNG Export`

## 6. Key Data Structures (`RES/models.py`)
- `Job` & `JobState` (`NEW`, `READY`, `RUNNING`, `WAITING`, `COMPLETED`, `TERMINATED`, `FAILED`, `CANCELLED`) with `VALID_STATE_TRANSITIONS`
- `ProcessInfo`, `SchedulingResultEntry`, `GanttSlice`, `SchedulingReport`
- `MemoryBlock`, `MemoryAllocationRecord`
- `ResourceState` (`resource_types`, `available`, `allocation`, `maximum`, `need`, `process_names`)
- `ExecutionRecord`
