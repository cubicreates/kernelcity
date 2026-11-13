import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn

from GUI.overworld import animate_city_drive
from GUI.widgets import is_compact_terminal
from RES.models import NavigationMode


def play_startup_sequence(console: Console, mode: str) -> None:
    console.clear()
    logo = (
        "[bold cyan]"
        "█▄▀ █▀▀ █▀█ █▄░█ █▀▀ █░░   █▀▀ █ ▀█▀ █▄█\n"
        "█░█ ██▄ █▀▄ █░▀█ ██▄ █▄▄   █▄▄ █ ░█░ ░█░"
        "[/bold cyan]\n"
        "[white]16-BIT OPERATING SYSTEM RESOURCE OVERWORLD[/white]\n"
        "[bold yellow]YOUR SYSTEM. YOUR RESOURCES. YOUR CONTROL.[/bold yellow]"
    )
    console.print(Panel(logo, border_style="bright_cyan"))

    if mode == NavigationMode.SKIP.value:
        return

    with Progress(
        TextColumn("[info]{task.description}[/info]"),
        BarColumn(bar_width=28 if is_compact_terminal(console) else 44),
        TextColumn("{task.percentage:>3.0f}%"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("BOOTING KERNEL ENGINE...", total=16)
        delay = 0.012 if mode == NavigationMode.QUICK.value else 0.022
        for _ in range(16):
            time.sleep(delay)
            progress.advance(task, 1)

    if mode == NavigationMode.EXPLORE.value:
        lights = [
            "[bold red](o)[/bold red] ( ) ( )  READY...",
            "( ) [bold yellow](o)[/bold yellow] ( )  SET...",
            "( ) ( ) [bold green](o)[/bold green]  GO! [bold green][o=o]>[/bold green]",
        ]
        for frame in lights:
            console.print(f"  {frame}", end="\r")
            time.sleep(0.18)
        console.print("")


def travel_vehicle(console: Console, origin: str, destination: str, mode: str) -> None:
    if mode == NavigationMode.SKIP.value:
        return

    if origin == "CITY GATE" and not is_compact_terminal(console):
        animate_city_drive(console, destination, mode)
        return

    width = 16 if is_compact_terminal(console) else 28
    steps = 4 if mode == NavigationMode.QUICK.value else 7
    delay = 0.03 if mode == NavigationMode.QUICK.value else 0.04

    console.print(f"\n[nav]Driving: {origin} ---> {destination}[/nav]")
    for step in range(steps + 1):
        pos = int((step / steps) * width)
        road = "-" * pos + "[o=o]>" + "-" * (width - pos)
        console.print(f"  [road]|{road}|[/road]", end="\r")
        time.sleep(delay)
    console.print(f"  [success]|{'=' * width}[o=o]> PARKED AT {destination}|[/success]")
    time.sleep(0.1)
