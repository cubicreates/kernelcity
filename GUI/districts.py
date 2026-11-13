from rich.console import Console
from rich.panel import Panel

from GUI.animations import travel_vehicle
from GUI.buildings import run_building
from GUI.maps import DISTRICT_BUILDINGS, show_district_map
from GUI.overworld import build_district_street_text
from GUI.widgets import is_compact_terminal, pause, prompt_text
from RES.kernel import KernelEngine


def run_district(console: Console, kernel: KernelEngine, district_name: str) -> None:
    buildings = DISTRICT_BUILDINGS.get(district_name, [])
    while True:
        console.clear()
        if not is_compact_terminal(console):
            street = build_district_street_text(district_name, buildings, kart_index=-1)
            console.print(Panel(street, title=f"[bold cyan]{district_name}[/bold cyan]", border_style="bright_cyan"))
        else:
            console.print(Panel(f"[bold cyan]{district_name}[/bold cyan]", border_style="cyan"))

        options = "   ".join(f"[bold yellow][{idx}][/bold yellow] {bld}" for idx, bld in enumerate(buildings, start=1))
        console.print(Panel(f"{options}\n[bold yellow][M][/bold yellow] District Map   [bold red][B][/bold red] Return to City Gate", border_style="blue", title="[bold white]DISTRICT STREET[/bold white]"))

        choice = prompt_text(console, "Drive to building", "B").upper()
        if choice == "B":
            return
        if choice == "M":
            selected = show_district_map(console, district_name)
            if selected:
                travel_vehicle(console, district_name, selected, kernel.config_manager.config.navigation_mode)
                run_building(console, kernel, selected)
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(buildings):
            idx = int(choice) - 1
            selected = buildings[idx]
            travel_vehicle(console, district_name, selected, kernel.config_manager.config.navigation_mode)
            run_building(console, kernel, selected)
        else:
            console.print("[error]Invalid building selection.[/error]")
            pause(console)
