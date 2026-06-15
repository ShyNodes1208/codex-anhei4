from __future__ import annotations

import itertools
import time

from .capture import Frame
from .config import normalized_point
from .input import InputController


class RouteController:
    def __init__(self, config: dict, controller: InputController) -> None:
        self.config = config
        self.controller = controller
        self._points = itertools.cycle(config.get("points", [[0.5, 0.5]]))
        self._last_move = 0.0

    def tick(self, frame: Frame, cursor_only: bool = False) -> bool:
        if not self.config.get("enabled", False):
            return False
        now = time.monotonic()
        if now - self._last_move < float(self.config.get("pulse_seconds", 1.2)):
            return False
        x, y = normalized_point(next(self._points), frame.width, frame.height)
        if cursor_only:
            succeeded = self.controller.move_to(frame.left + x, frame.top + y)
        else:
            succeeded = self.controller.move_and_click(frame.left + x, frame.top + y)
        if not succeeded:
            return False
        self._last_move = now
        return True
