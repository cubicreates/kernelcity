from typing import Dict, List


def get_workflow_specifications() -> Dict[str, List[str]]:
    return {
        "startup_sequence": [
            "1. Initialise ConfigurationManager and directory layout",
            "2. Initialise DatabaseManager (SQLite schema)",
            "3. Initialise EventLogger",
            "4. Construct single shared KernelEngine instance",
            "5. Pass KernelEngine to KernelCityGUI",
            "6. Display startup banner and vehicle arrival at City Gate",
        ],
        "job_lifecycle": [
            "1. User submits job in Job House (validated by InputValidator)",
            "2. Job is registered in ProcessManager and persisted in SQLite",
            "3. Scheduler determines dispatch order (FCFS, SJF, Priority, RR)",
            "4. ResourceManager / MemoryManager validate application-level allocations",
            "5. ProcessManager executes approved subprocess safely (shell=False)",
            "6. SystemMonitor observes host CPU/RAM/process metrics",
            "7. StorageManager organises output files and execution logs",
            "8. History Museum and Report Centre record and export outcomes",
        ],
        "navigation_hierarchy": [
            "CITY GATE -> DISTRICT -> BUILDING -> FUNCTION",
            "Optional M shortcut opens City Map or District Map",
        ],
    }

