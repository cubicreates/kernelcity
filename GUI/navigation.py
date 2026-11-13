from typing import List


class NavigationController:
    def __init__(self):
        self.location_stack: List[str] = ["CITY GATE"]

    @property
    def current_location(self) -> str:
        return self.location_stack[-1]

    def push(self, destination: str) -> None:
        self.location_stack.append(destination)

    def pop(self) -> str:
        if len(self.location_stack) > 1:
            return self.location_stack.pop()
        return self.location_stack[0]

    def reset_to_city_gate(self) -> None:
        self.location_stack = ["CITY GATE"]

