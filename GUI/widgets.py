from pathlib import Path
from typing import Callable, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from GUI.themes import COMPACT_WIDTH_THRESHOLD
from RES.models import GanttSlice, MemoryBlock
from RES.PHASE_4_TESTING.error_handling import KernelCityError


def is_compact_terminal(console: Console) -> bool:
    return console.size.width < COMPACT_WIDTH_THRESHOLD


def render_header(console: Console, title: str, subtitle: str = "", badge: str = "") -> None:
    right = f" [{badge}]" if badge else ""
    body = f"[title]{title}[/title]{right}"
    if subtitle:
        body = f"{body}\n[muted]{subtitle}[/muted]"
    console.print(Panel(body, border_style="blue", expand=True))


def prompt_text(console: Console, label: str, default: Optional[str] = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    raw = console.input(f"[nav]{label}{suffix}:[/nav] ").strip()
    if not raw and default is not None:
        return default
    return raw


def prompt_int(console: Console, label: str, default: Optional[int] = None) -> Optional[int]:
    raw = prompt_text(console, label, str(default) if default is not None else None)
    try:
        return int(raw)
    except ValueError:
        console.print("[error]Invalid integer input.[/error]")
        return None


def pause(console: Console, message: str = "Press Enter to continue...") -> None:
    console.input(f"\n[muted]{message}[/muted]")


def render_gantt_chart(console: Console, slices: List[GanttSlice]) -> None:
    if not slices:
        console.print("[muted]No Gantt slices available.[/muted]")
        return
    bar_parts = []
    time_parts = [f"{slices[0].start_time}"]
    for sl in slices:
        segment = f" {sl.job_id} "
        bar_parts.append(segment)
        time_parts.append(f"{sl.end_time:>4}")
    console.print("[info]Gantt Timeline:[/info]")
    console.print("|" + "|".join(bar_parts) + "|")
    console.print(" ".join(time_parts))


def render_memory_blocks(console: Console, blocks: List[MemoryBlock]) -> None:
    table = Table(title="Memory Pool Layout", border_style="cyan")
    table.add_column("Block", style="bold white")
    table.add_column("Size (KB)", justify="right")
    table.add_column("Status", style="cyan")
    table.add_column("Allocated To")
    table.add_column("Requested (KB)", justify="right")
    table.add_column("Internal Frag (KB)", justify="right")

    visual_cells = []
    for block in blocks:
        if block.allocated_to:
            status = "[warning]OCCUPIED[/warning]"
            visual_cells.append(f"[yellow][{block.block_id}: {block.allocated_to} ({block.requested_size}/{block.size} KB)][/yellow]")
        else:
            status = "[success]FREE[/success]"
            visual_cells.append(f"[green][{block.block_id}: FREE {block.size} KB][/green]")
        table.add_row(
            block.block_id,
            str(block.size),
            status,
            block.allocated_to or "-",
            str(block.requested_size),
            str(block.internal_fragmentation),
        )

    console.print(" ".join(visual_cells))
    console.print(table)


def run_export_menu(
    console: Console,
    default_stem: str,
    default_dir: Path,
    csv_fn: Optional[Callable[[str, Optional[str], bool], Path]] = None,
    json_fn: Optional[Callable[[str, Optional[str], bool], Path]] = None,
    txt_fn: Optional[Callable[[str, Optional[str], bool], Path]] = None,
    chart_fn: Optional[Callable[[], Path]] = None,
) -> None:
    while True:
        console.print("\n[info]EXPORT RESULTS:[/info] 1=Export CSV | 2=Export JSON | 3=Export TXT | 4=Generate Chart | 5=Return")
        choice = prompt_text(console, "Export option", "5").strip()
        if choice == "5":
            return
        if choice == "4":
            if chart_fn is None:
                console.print("[warning]Chart generation is not applicable for this view.[/warning]")
            else:
                try:
                    out = chart_fn()
                    console.print(f"[success]Chart generated: {out}[/success]")
                except KernelCityError as exc:
                    console.print(f"[error]{exc}[/error]")
            continue

        handler = {"1": csv_fn, "2": json_fn, "3": txt_fn}.get(choice)
        if handler is None:
            console.print("[warning]Selected export format is not available here.[/warning]")
            continue

        filename = prompt_text(console, "Filename (without extension)", default_stem)
        out_dir = prompt_text(console, "Output directory", str(default_dir))
        try:
            out_path = handler(filename, out_dir, False)
            console.print(f"[success]Exported successfully: {out_path}[/success]")
        except KernelCityError as exc:
            if "already exists" in str(exc):
                confirm = prompt_text(console, f"{exc} Overwrite? (YES/NO)", "NO").upper()
                if confirm == "YES":
                    try:
                        out_path = handler(filename, out_dir, True)
                        console.print(f"[success]Overwritten and exported: {out_path}[/success]")
                    except KernelCityError as inner_exc:
                        console.print(f"[error]{inner_exc}[/error]")
            else:
                console.print(f"[error]{exc}[/error]")
