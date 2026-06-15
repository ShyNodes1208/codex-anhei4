from __future__ import annotations

from dataclasses import dataclass

import cv2
import mss
import numpy as np


@dataclass(frozen=True)
class Frame:
    image: np.ndarray
    left: int
    top: int

    @property
    def width(self) -> int:
        return int(self.image.shape[1])

    @property
    def height(self) -> int:
        return int(self.image.shape[0])


class ScreenCapture:
    def __init__(self, monitor_number: int = 1) -> None:
        self._mss = mss.mss()
        self._monitor_number = monitor_number

    def grab(self) -> Frame:
        monitor = self._mss.monitors[self._monitor_number]
        raw = np.asarray(self._mss.grab(monitor))
        return Frame(
            image=cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR),
            left=int(monitor["left"]),
            top=int(monitor["top"]),
        )

    def close(self) -> None:
        self._mss.close()

