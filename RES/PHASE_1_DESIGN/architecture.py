from typing import Any, Dict


def get_architecture_specification() -> Dict[str, Any]:
    return {
        "project": "KERNEL CITY",
        "subtitle": "An Integrated Operating System Resource Management and Monitoring Environment",
        "entry_point": "main.py",
        "layers": {
            "presentation": {
                "package": "GUI",
                "responsibilities": [
                    "Terminal rendering with Rich",
                    "City Gate, 4 Districts, 12 Buildings, Demo Centre, City Administration",
                    "Vehicle travel animations (Explore, Quick, Skip)",
                    "City and District maps",
                    "Input collection and validation forwarding",
                ],
                "constraints": [
                    "Must not implement scheduling, memory, or deadlock algorithms",
                    "Must receive shared KernelEngine instance",
                ],
            },
            "engine": {
                "package": "RES",
                "responsibilities": [
                    "Shared KernelEngine coordinating all OS modules",
                    "Phase 1: Architecture, workflows, and data design specs",
                    "Phase 2: Process, Scheduling, Memory, Resource, Deadlock, Monitor, Storage",
                    "Phase 3: Analytics, algorithm comparisons, Matplotlib charts",
                    "Phase 4: Input validation, error handling, test support",
                    "Phase 5: Demo datasets, demo engine, walkthrough",
                ],
                "constraints": [
                    "Must never import GUI modules",
                    "Must be independently testable",
                ],
            },
            "persistence": {
                "components": ["SQLite database (kernel_city.db)", "JSON configuration", "File logs"],
            },
        },
        "districts": {
            "Operations District": ["Job House", "Scheduling Plaza", "Process Garage"],
            "Resource District": ["Memory Centre", "Resource Allocation Office", "Deadlock Court"],
            "Monitoring District": ["System Watchtower", "Storage Depot", "Process Observatory"],
            "Intelligence District": ["Analytics Hall", "History Museum", "Report Centre"],
        },
    }

