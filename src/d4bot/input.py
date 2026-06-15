from __future__ import annotations

import ctypes
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def foreground_window_title() -> str:
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value


@dataclass
class InputSafety:
    expected_window_title: str
    enabled: bool = False
    stopped: bool = False

    def ready(self) -> bool:
        return (
            self.enabled
            and not self.stopped
            and self.expected_window_title.lower() in foreground_window_title().lower()
        )


class InputController:
    def __init__(self, mode: str, safety: InputSafety) -> None:
        self.mode = mode
        self.safety = safety
        self._driver = None

    def _load_driver(self):
        if self._driver is None:
            import pydirectinput

            pydirectinput.PAUSE = 0.03
            pydirectinput.FAILSAFE = True
            self._driver = pydirectinput
        return self._driver

    def _allowed(self, action: str) -> bool:
        if self.mode == "dry_run":
            logger.info("DRY RUN: %s", action)
            return False
        if not self.safety.ready():
            logger.warning("Input blocked by safety gate: %s", action)
            return False
        return True

    def press(self, key: str, duration: float = 0.05) -> bool:
        if not self._allowed(f"press {key}"):
            return False
        driver = self._load_driver()
        driver.keyDown(key)
        try:
            time.sleep(duration)
        finally:
            driver.keyUp(key)
        return True

    def click(self, x: int, y: int, button: str = "left") -> bool:
        if not self._allowed(f"click {button} at ({x}, {y})"):
            return False
        self._load_driver().click(x=x, y=y, button=button)
        return True

    def move_and_click(self, x: int, y: int, button: str = "left") -> bool:
        if not self._allowed(f"move and click {button} at ({x}, {y})"):
            return False
        driver = self._load_driver()
        driver.moveTo(x, y, duration=0.12)
        driver.click(button=button)
        return True

    def move_to(self, x: int, y: int, duration: float = 0.12) -> bool:
        if not self._allowed(f"move cursor to ({x}, {y})"):
            return False
        self._load_driver().moveTo(x, y, duration=duration)
        return True

    def modified_click(
        self, x: int, y: int, modifier: str, button: str = "left"
    ) -> bool:
        if not self._allowed(
            f"{modifier}+click {button} at ({x}, {y})"
        ):
            return False
        driver = self._load_driver()
        driver.keyDown(modifier)
        try:
            driver.click(x=x, y=y, button=button)
        finally:
            driver.keyUp(modifier)
        return True
