from rich.console import Console
from rich.panel import Panel

from GUI.overworld import CITY_NODES, build_city_overworld_text
from GUI.widgets import is_compact_terminal
from RES.kernel import KernelEngine


def render_city_gate(console: Console, kernel: KernelEngine) -> None:
    console.clear()
    cfg = kernel.config_manager.config
    job_count = len(kernel.process_manager.list_jobs())
    hud_top = (
        f"[bold cyan]KERNEL CITY OVERWORLD[/bold cyan]  "
        f"[bold yellow]MODE:[/bold yellow] {cfg.navigation_mode}  "
        f"[bold green]JOBS:[/bold green] {job_count}  "
        f"[bold white]WHERE WOULD YOU LIKE TO GO?[/bold white]"
    )

    if is_compact_terminal(console):
        console.print(Panel(hud_top, border_style="cyan"))
        console.print(
            "[bold yellow][1][/bold yellow] Operations  "
            "[bold yellow][2][/bold yellow] Memory  "
            "[bold yellow][3][/bold yellow] Resource  "
            "[bold yellow][4][/bold yellow] Intelligence\n"
            "[bold yellow][D][/bold yellow] Demo Arena  "
            "[bold yellow][A][/bold yellow] City Hall  "
            "[bold yellow][M][/bold yellow] Map  "
            "[bold yellow][Q][/bold yellow] Quit"
        )
        return

    overworld = build_city_overworld_text(kart_pos=CITY_NODES["CITY GATE"])
    console.print(Panel(overworld, title=hud_top, border_style="bright_cyan"))
    hud_controls = (
        "[bold yellow][1][/bold yellow] Operations District   "
        "[bold yellow][2][/bold yellow] Memory District   "
        "[bold yellow][3][/bold yellow] Resource District   "
        "[bold yellow][4][/bold yellow] Intelligence District\n"
        "[bold green][K][/bold green] Free-Drive Kart (WASD/Arrows)   "
        "[bold yellow][D][/bold yellow] Demo Arena   "
        "[bold yellow][A][/bold yellow] City Hall   "
        "[bold yellow][M][/bold yellow] City Map   "
        "[bold red][Q][/bold red] Exit"
    )
    console.print(Panel(hud_controls, border_style="blue", title="[bold white]16-BIT KART HUD[/bold white]"))
