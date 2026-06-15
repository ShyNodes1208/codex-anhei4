from __future__ import annotations

import time

from .capture import Frame
from .input import InputController


class LootController:
    def __init__(self, config: dict, controller: InputController) -> None:
        self.config = config
        self.controller = controller

    def collect(self, frame: Frame, attempts: int | None = None) -> None:
        if not self.config.get("enabled", False):
            return
        total_attempts = (
            int(attempts) if attempts is not None else int(self.config.get("attempts", 1))
        )
        for _ in range(total_attempts):
            if self.config.get("click_center", False):
                self.controller.click(
                    frame.left + frame.width // 2,
                    frame.top + int(frame.height * 0.52),
                )
            else:
                self.controller.press(self.config.get("force_interact_key", "f"))
            time.sleep(float(self.config.get("settle_seconds", 0.3)))

    def collect_once(self, frame: Frame) -> bool:
        if not self.config.get("enabled", False):
            return False
        if self.config.get("click_center", False):
            return self.controller.click(
                frame.left + frame.width // 2,
                frame.top + int(frame.height * 0.52),
            )
        return self.controller.press(self.config.get("force_interact_key", "f"))
