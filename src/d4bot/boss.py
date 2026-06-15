from __future__ import annotations

from .capture import Frame
from .config import normalized_point
from .input import InputController


class BossSummoner:
    def __init__(self, config: dict, controller: InputController) -> None:
        self.config = config
        self.controller = controller

    def move_to_summon_device(self, frame: Frame) -> bool:
        summon = self.config["summon"]
        x, y = normalized_point(summon["device_position"], frame.width, frame.height)
        return self.controller.move_and_click(
            frame.left + x,
            frame.top + y,
            button=summon.get("click_button", "left"),
        )

    def interact(self) -> bool:
        return self.controller.press(
            self.config["summon"].get("force_interact_key", "f")
        )

    def move_to_room_corner(self, frame: Frame) -> bool:
        x, y = normalized_point(
            self.config["summon"]["room_corner_position"], frame.width, frame.height
        )
        return self.controller.move_and_click(frame.left + x, frame.top + y)

    def move_to_chest(self, frame: Frame) -> bool:
        x, y = normalized_point(
            self.config["loot"]["chest_position"], frame.width, frame.height
        )
        return self.controller.move_and_click(frame.left + x, frame.top + y)

    def open_chest(self) -> bool:
        return self.controller.press(
            self.config["loot"].get("force_interact_key", "f")
        )
