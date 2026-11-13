import sys
import time
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from GUI.widgets import is_compact_terminal
from RES.models import NavigationMode

CITY_CANVAS_WIDTH = 74
CITY_CANVAS_HEIGHT = 17

CITY_NODES: Dict[str, Tuple[int, int]] = {
    "CITY GATE": (35, 8),
    "OPERATIONS DISTRICT": (11, 3),
    "MEMORY DISTRICT": (58, 3),
    "RESOURCE DISTRICT": (11, 13),
    "INTELLIGENCE DISTRICT": (58, 13),
    "DEMO CENTRE": (35, 2),
    "CITY ADMINISTRATION": (35, 14),
}

CITY_ROUTES: Dict[str, List[Tuple[int, int]]] = {
    "OPERATIONS DISTRICT": [(35, 8), (22, 8), (22, 3), (11, 3)],
    "MEMORY DISTRICT": [(35, 8), (48, 8), (48, 3), (58, 3)],
    "RESOURCE DISTRICT": [(35, 8), (22, 8), (22, 13), (11, 13)],
    "INTELLIGENCE DISTRICT": [(35, 8), (48, 8), (48, 13), (58, 13)],
    "DEMO CENTRE": [(35, 8), (35, 2)],
    "CITY ADMINISTRATION": [(35, 8), (35, 14)],
}


def _create_grass_grid(width: int, height: int) -> List[List[Tuple[str, str]]]:
    grid: List[List[Tuple[str, str]]] = []
    for y in range(height):
        row: List[Tuple[str, str]] = []
        for x in range(width):
            ch = "." if (x + y) % 7 == 0 else " "
            row.append((ch, "green on #0b2e13"))
        grid.append(row)
    return grid


def _draw_road_segment(grid: List[List[Tuple[str, str]]], x1: int, y1: int, x2: int, y2: int) -> None:
    if x1 == x2:
        step = 1 if y2 >= y1 else -1
        for y in range(y1, y2 + step, step):
            for dx in (-1, 0, 1):
                gx = x1 + dx
                if 0 <= y < len(grid) and 0 <= gx < len(grid[0]):
                    ch = ":" if dx == 0 and y % 2 == 0 else " "
                    style = "bold yellow on #2b2b2b" if ch == ":" else "white on #2b2b2b"
                    grid[y][gx] = (ch, style)
    elif y1 == y2:
        step = 1 if x2 >= x1 else -1
        for x in range(x1, x2 + step, step):
            for dy in (-1, 0, 1):
                gy = y1 + dy
                if 0 <= gy < len(grid) and 0 <= x < len(grid[0]):
                    ch = "-" if dy == 0 and x % 2 == 0 else " "
                    style = "bold yellow on #2b2b2b" if ch == "-" else "white on #2b2b2b"
                    grid[gy][x] = (ch, style)


def _stamp_sprite(grid: List[List[Tuple[str, str]]], x: int, y: int, lines: List[str], style: str) -> None:
    for dy, line in enumerate(lines):
        gy = y + dy
        if not (0 <= gy < len(grid)):
            continue
        for dx, ch in enumerate(line):
            gx = x + dx
            if 0 <= gx < len(grid[0]) and ch != "\0":
                grid[gy][gx] = (ch, style)


def build_city_overworld_text(kart_pos: Optional[Tuple[int, int]] = None, active_target: str = "") -> Text:
    grid = _create_grass_grid(CITY_CANVAS_WIDTH, CITY_CANVAS_HEIGHT)

    _draw_road_segment(grid, 11, 3, 58, 3)
    _draw_road_segment(grid, 11, 13, 58, 13)
    _draw_road_segment(grid, 22, 3, 22, 13)
    _draw_road_segment(grid, 48, 3, 48, 13)
    _draw_road_segment(grid, 35, 2, 35, 14)
    _draw_road_segment(grid, 22, 8, 48, 8)

    trees = [(2, 8), (69, 8), (29, 5), (41, 5), (29, 11), (41, 11), (4, 15), (68, 1)]
    for tx, ty in trees:
        _stamp_sprite(grid, tx, ty, ["^", "|"], "bold bright_green on #0b2e13")

    _stamp_sprite(grid, 2, 1, ["  /========\\  ", " |[1] OPS   | ", " | []  [][] | "], "bold white on #103b66")
    _stamp_sprite(grid, 55, 1, ["  /========\\  ", " |[2] MEMORY| ", " | [][]  [] | "], "bold white on #4a1e5e")
    _stamp_sprite(grid, 2, 11, ["  /========\\  ", " |[3] RESOUR| ", " | []  [][] | "], "bold white on #663c00")
    _stamp_sprite(grid, 55, 11, ["  /========\\  ", " |[4] INTEL | ", " | [][]  [] | "], "bold white on #0e4f4f")

    _stamp_sprite(grid, 29, 0, [" [D] DEMO ARENA "], "bold black on bright_yellow")
    _stamp_sprite(grid, 29, 15, [" [A] CITY HALL  "], "bold white on #333344")
    _stamp_sprite(grid, 31, 7, ["[GATE]"], "bold cyan on #1f1f1f")

    if active_target and active_target in CITY_NODES:
        tx, ty = CITY_NODES[active_target]
        if 0 <= ty < CITY_CANVAS_HEIGHT and 0 <= tx < CITY_CANVAS_WIDTH:
            grid[ty][tx] = ("*", "bold bright_yellow on #2b2b2b")

    if kart_pos is not None:
        kx, ky = kart_pos
        _stamp_sprite(grid, max(0, kx - 2), ky, ["[o=o]>"], "bold bright_green on #2b2b2b")

    text = Text()
    for y, row in enumerate(grid):
        for ch, style in row:
            text.append(ch, style=style)
        if y < len(grid) - 1:
            text.append("\n")
    return text


def build_district_street_text(
    district_name: str,
    buildings: List[str],
    kart_index: int = -1,
) -> Text:
    width = 74
    height = 11
    grid = _create_grass_grid(width, height)
    _draw_road_segment(grid, 2, 8, width - 3, 8)

    colors = ["#103b66", "#4a1e5e", "#663c00", "#0e4f4f", "#5e1e2b"]
    spacing = max(13, (width - 6) // max(1, len(buildings)))
    for idx, bld in enumerate(buildings):
        bx = 3 + idx * spacing
        if bx + 11 >= width:
            break
        short = bld[:9].upper()
        bg = colors[idx % len(colors)]
        _stamp_sprite(
            grid,
            bx,
            2,
            [
                " /=======\\ ",
                f"|[{idx + 1}] {short:<5}|",
                "| []   [] |",
                "|___[ ]___|",
            ],
            f"bold white on {bg}",
        )
        if idx == kart_index:
            _stamp_sprite(grid, bx + 2, 8, ["[o=o]>"], "bold bright_green on #2b2b2b")

    if kart_index < 0:
        _stamp_sprite(grid, 3, 8, ["[o=o]>"], "bold bright_green on #2b2b2b")

    text = Text()
    for y, row in enumerate(grid):
        for ch, style in row:
            text.append(ch, style=style)
        if y < len(grid) - 1:
            text.append("\n")
    return text


def _interpolate_waypoints(waypoints: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    points: List[Tuple[int, int]] = []
    for idx in range(len(waypoints) - 1):
        x1, y1 = waypoints[idx]
        x2, y2 = waypoints[idx + 1]
        dx = 0 if x2 == x1 else (1 if x2 > x1 else -1)
        dy = 0 if y2 == y1 else (1 if y2 > y1 else -1)
        cx, cy = x1, y1
        while (cx, cy) != (x2, y2):
            points.append((cx, cy))
            if cx != x2:
                cx += dx * min(2, abs(x2 - cx))
            elif cy != y2:
                cy += dy
        points.append((x2, y2))
    return points


def animate_city_drive(console: Console, destination: str, mode: str) -> None:
    if mode == NavigationMode.SKIP.value or is_compact_terminal(console):
        return
    waypoints = CITY_ROUTES.get(destination)
    if not waypoints:
        return
    path = _interpolate_waypoints(waypoints)
    if mode == NavigationMode.QUICK.value:
        path = path[::3] or path
        delay = 0.015
    else:
        delay = 0.025

    with Live(console=console, refresh_per_second=30, transient=True) as live:
        for pt in path:
            map_text = build_city_overworld_text(kart_pos=pt, active_target=destination)
            live.update(
                Panel(
                    map_text,
                    title=f"[bold yellow]DRIVING TO {destination}[/bold yellow]",
                    border_style="bright_cyan",
                )
            )
            time.sleep(delay)


def read_single_key_if_tty() -> Optional[str]:
    if not sys.stdin.isatty():
        return None
    try:
        import msvcrt

        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            ext = msvcrt.getwch()
            arrow_map = {"H": "UP", "P": "DOWN", "K": "LEFT", "M": "RIGHT"}
            return arrow_map.get(ext, "")
        return ch
    except ImportError:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
            if ch == "\x1b":
                seq = sys.stdin.read(2)
                arrow_map = {"[A": "UP", "[B": "DOWN", "[D": "LEFT", "[C": "RIGHT"}
                return arrow_map.get(seq, "")
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)


def run_free_drive_overworld(console: Console) -> Optional[str]:
    if not sys.stdin.isatty() or is_compact_terminal(console):
        return None
    kx, ky = CITY_NODES["CITY GATE"]
    node_keys = {
        "OPERATIONS DISTRICT": (11, 3),
        "MEMORY DISTRICT": (58, 3),
        "RESOURCE DISTRICT": (11, 13),
        "INTELLIGENCE DISTRICT": (58, 13),
        "DEMO CENTRE": (35, 2),
        "CITY ADMINISTRATION": (35, 14),
    }

    def nearest_destination(x: int, y: int) -> Optional[str]:
        for name, (nx, ny) in node_keys.items():
            if abs(x - nx) <= 4 and abs(y - ny) <= 1:
                return name
        return None

    with Live(console=console, refresh_per_second=20, transient=True) as live:
        while True:
            nearby = nearest_destination(kx, ky)
            status = f"AT: {nearby} (Press ENTER to enter!)" if nearby else "Use WASD / Arrows to drive | ENTER=Enter | ESC/Q=Back"
            live.update(
                Panel(
                    build_city_overworld_text(kart_pos=(kx, ky), active_target=nearby or ""),
                    title="[bold green]FREE-DRIVE KART MODE[/bold green]",
                    subtitle=f"[bold yellow]{status}[/bold yellow]",
                    border_style="bright_green",
                )
            )
            key = read_single_key_if_tty()
            if key is None:
                return None
            upper = key.upper()
            if upper in ("Q", "\x1b"):
                return None
            if upper in ("\r", "\n"):
                if nearby:
                    return nearby
            elif upper in ("W", "UP"):
                ky = max(1, ky - 1)
            elif upper in ("S", "DOWN"):
                ky = min(CITY_CANVAS_HEIGHT - 2, ky + 1)
            elif upper in ("A", "LEFT"):
                kx = max(3, kx - 2)
            elif upper in ("D", "RIGHT"):
                kx = min(CITY_CANVAS_WIDTH - 6, kx + 2)

