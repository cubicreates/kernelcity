from rich.console import Console

from GUI.animations import play_startup_sequence, travel_vehicle
from GUI.dashboard import render_city_gate
from GUI.districts import run_district
from GUI.maps import DISTRICT_BUILDINGS, show_city_map
from GUI.menus import run_city_administration, run_demo_centre
from GUI.navigation import NavigationController
from GUI.overworld import run_free_drive_overworld
from GUI.themes import KERNEL_CITY_THEME
from GUI.widgets import pause, prompt_text
from RES.kernel import KernelEngine


class KernelCityGUI:
    def __init__(self, kernel: KernelEngine):
        self.kernel = kernel
        self.console = Console(theme=KERNEL_CITY_THEME)
        self.nav = NavigationController()
        self.districts = list(DISTRICT_BUILDINGS.keys())

    def _enter_destination(self, destination: str, mode: str) -> None:
        if destination in self.districts:
            self.nav.push(destination)
            travel_vehicle(self.console, "CITY GATE", destination, mode)
            run_district(self.console, self.kernel, destination)
            self.nav.reset_to_city_gate()
        elif destination == "DEMO CENTRE":
            travel_vehicle(self.console, "CITY GATE", "DEMO CENTRE", mode)
            run_demo_centre(self.console, self.kernel)
        elif destination == "CITY ADMINISTRATION":
            travel_vehicle(self.console, "CITY GATE", "CITY ADMINISTRATION", mode)
            run_city_administration(self.console, self.kernel)

    def run(self) -> None:
        mode = self.kernel.config_manager.config.navigation_mode
        play_startup_sequence(self.console, mode)

        while True:
            try:
                render_city_gate(self.console, self.kernel)
                choice = prompt_text(self.console, "Enter destination key", "1").upper()
                mode = self.kernel.config_manager.config.navigation_mode

                if choice == "Q":
                    self.console.print("[info]Shutting down Kernel City...[/info]")
                    return
                if choice == "K":
                    selected = run_free_drive_overworld(self.console)
                    if selected:
                        self._enter_destination(selected, mode)
                elif choice in ("1", "2", "3", "4"):
                    self._enter_destination(self.districts[int(choice) - 1], mode)
                elif choice == "D":
                    self._enter_destination("DEMO CENTRE", mode)
                elif choice == "A":
                    self._enter_destination("CITY ADMINISTRATION", mode)
                elif choice == "M":
                    selected_district = show_city_map(self.console)
                    if selected_district:
                        self._enter_destination(selected_district, mode)
                else:
                    self.console.print("[error]Invalid choice. Select 1-4, K, D, A, M, or Q.[/error]")
                    pause(self.console)
            except KeyboardInterrupt:
                self.console.print("\n[warning]Interrupt received. Returning to City Gate (press Q to exit).[/warning]")
                pause(self.console)
            except EOFError:
                self.console.print("\n[info]EOF received. Shutting down Kernel City...[/info]")
                return
