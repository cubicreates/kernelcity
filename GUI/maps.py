from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from GUI.widgets import prompt_text


DISTRICT_BUILDINGS = {
    "OPERATIONS DISTRICT": ["Job House", "Scheduling Plaza", "Process Garage"],
    "MEMORY DISTRICT": ["Memory Centre", "Allocation Laboratory", "Memory Analytics Office"],
    "RESOURCE DISTRICT": ["Resource Allocation Office", "Banker's Algorithm Centre", "Deadlock Court"],
    "INTELLIGENCE DISTRICT": [
        "Analytics Hall",
        "History Museum",
        "Report Centre",
        "System Watchtower",
        "Storage Depot",
    ],
}


def show_city_map(console: Console) -> Optional[str]:
    console.clear()
    map_art = (
        "                  [CITY GATE]\n"
        "                       |\n"
        "     +-----------------+-----------------+\n"
        "     |                 |                 |\n"
        "[1] OPERATIONS    [2] MEMORY      [3] RESOURCE\n"
        "                       |\n"
        "                [4] INTELLIGENCE"
    )
    console.print(Panel(map_art, title="KERNEL CITY MAP", border_style="cyan"))
    table = Table(border_style="blue")
    table.add_column("Key", style="bold yellow")
    table.add_column("District", style="bold white")
    table.add_column("Buildings")
    districts = list(DISTRICT_BUILDINGS.keys())
    for idx, name in enumerate(districts, start=1):
        table.add_row(str(idx), name, ", ".join(DISTRICT_BUILDINGS[name]))
    table.add_row("B", "Back", "Return to previous screen")
    console.print(table)

    choice = prompt_text(console, "Jump to district (1-4) or B to go back", "B").upper()
    if choice in ("1", "2", "3", "4"):
        return districts[int(choice) - 1]
    return None


def show_district_map(console: Console, district_name: str) -> Optional[str]:
    console.clear()
    buildings = DISTRICT_BUILDINGS.get(district_name, [])
    table = Table(title=f"{district_name} MAP", border_style="cyan")
    table.add_column("Key", style="bold yellow")
    table.add_column("Building", style="bold white")
    for idx, bld in enumerate(buildings, start=1):
        table.add_row(str(idx), bld)
    table.add_row("B", "Back")
    console.print(table)

    choice = prompt_text(console, f"Jump to building (1-{len(buildings)}) or B", "B").upper()
    if choice.isdigit() and 1 <= int(choice) <= len(buildings):
        return buildings[int(choice) - 1]
    return None
