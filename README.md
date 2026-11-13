# KERNEL CITY

**An Integrated Operating System Resource Management and Monitoring Environment**

- **Author:** Adit Ghosh
- **Roll Number:** 2401350016
- **Semester:** V
- **Course:** B.Tech CSE Full Stack Development

KERNEL CITY is a 16-bit overworld-inspired terminal application written in Python and Bash for the Operating Systems Lab Capstone. It unifies three core operating-system modules—**Process Management & CPU Scheduling**, **Memory Management**, and **Resource Allocation & Deadlock Management**—with live host monitoring, SQLite persistence, `pandas`/`numpy` analytics, `matplotlib` charts, and application-wide CSV exports.

## Project Structure
```
OSCAPSTONE/
├── main.py
├── launch.sh
├── requirements.txt
├── KernelCity.spec
├── assets/
│   └── KernelCity.ico
├── dist/KernelCity/
│   └── KernelCity.exe
├── GUI/
│   ├── animations.py, buildings.py, city.py, dashboard.py, districts.py
│   ├── maps.py, menus.py, navigation.py, overworld.py, themes.py, widgets.py
├── RES/
│   ├── kernel.py, models.py, configuration.py, database.py, event_logger.py
│   ├── PHASE_1_DESIGN/
│   ├── PHASE_2_CORE_MODULES/
│   ├── PHASE_3_ANALYSIS/
│   ├── PHASE_4_TESTING/
│   └── PHASE_5_DEMONSTRATION/
├── data/
│   ├── demo/
│   ├── jobs/
│   └── configuration/
├── docs/
│   ├── FINAL_TECHNICAL_REPORT.md
│   ├── PHASE_1_DESIGN/SYSTEM_DESIGN.md
│   ├── PHASE_3_ANALYSIS/ANALYSIS_REPORT.md
│   ├── PHASE_4_TESTING/TEST_REPORT.md
│   └── PHASE_5_DEMONSTRATION/DEMO_EVIDENCE.md
├── logs/
├── reports/
└── tests/
```

## City Navigation & Districts
1. **Operations District:** Job House, Scheduling Plaza, Process Garage
2. **Memory District:** Memory Centre, Allocation Laboratory, Memory Analytics Office
3. **Resource District:** Resource Allocation Office, Banker's Algorithm Centre, Deadlock Court
4. **Intelligence District:** Analytics Hall, History Museum, Report Centre, System Watchtower, Storage Depot
- **Special Locations:** Demo Centre (`D`), City Administration (`A`), City/District Maps (`M`), Free-Drive Kart Mode (`K` with WASD/Arrows)

## Installation
```bash
pip install -r requirements.txt
```
*(On Windows: `py -m pip install -r requirements.txt`)*

## Execution Instructions
- **Windows Standalone Executable:** Double-click `dist\KernelCity\KernelCity.exe` or run `.\dist\KernelCity\KernelCity.exe`
- **Python Source (Windows):** `py main.py`
- **Bash Launcher (Linux / WSL):**
  ```bash
  chmod +x launch.sh
  ./launch.sh
  ```

## Automated Testing
```bash
py -m pytest -v
```

## Academic Phase Evidence Map (100 Marks)
| Phase | Title | Marks | Evidence |
| --- | --- | --- | --- |
| Phase 1 | System Design and Planning | 20 | `RES/PHASE_1_DESIGN/`, `docs/PHASE_1_DESIGN/SYSTEM_DESIGN.md` |
| Phase 2 | Core Resource-Management Modules | 20 | `RES/PHASE_2_CORE_MODULES/`, `GUI/`, `launch.sh` |
| Phase 3 | Analysis and Comparison | 20 | `RES/PHASE_3_ANALYSIS/`, `docs/PHASE_3_ANALYSIS/ANALYSIS_REPORT.md`, `reports/*.png`, `reports/*.csv` |
| Phase 4 | Testing and Reliability | 20 | `RES/PHASE_4_TESTING/`, `tests/`, `docs/PHASE_4_TESTING/TEST_REPORT.md`, `logs/kernel_city.log` |
| Phase 5 | Documentation and Demonstration | 20 | `RES/PHASE_5_DEMONSTRATION/`, `docs/PHASE_5_DEMONSTRATION/DEMO_EVIDENCE.md`, `docs/FINAL_TECHNICAL_REPORT.md`, `README.md` |
