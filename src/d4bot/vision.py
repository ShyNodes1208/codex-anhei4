from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .capture import Frame
from .config import normalized_region


@dataclass(frozen=True)
class Observation:
    health_ratio: float
    enemy_visible: bool
    inventory_open: bool
    inventory_fill_ratio: float
    loot_hint: bool


def _crop(frame: Frame, region: list[float]) -> np.ndarray:
    left, top, right, bottom = normalized_region(region, frame.width, frame.height)
    return frame.image[top:bottom, left:right]


def _dual_hsv_ratio(image: np.ndarray, spec: dict) -> float:
    if image.size == 0:
        return 0.0
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(
        hsv, np.array(spec["lower1"], dtype=np.uint8), np.array(spec["upper1"], dtype=np.uint8)
    )
    mask2 = cv2.inRange(
        hsv, np.array(spec["lower2"], dtype=np.uint8), np.array(spec["upper2"], dtype=np.uint8)
    )
    return float(cv2.countNonZero(mask1 | mask2) / mask1.size)


class VisionEngine:
    def __init__(self, config: dict, inventory_config: dict | None = None) -> None:
        self.config = config
        self.inventory_config = inventory_config or {}

    def observe(self, frame: Frame) -> Observation:
        thresholds = self.config["thresholds"]
        health_crop = _crop(frame, self.config["health_region"])
        enemy_crop = _crop(frame, self.config["nearby_enemy_region"])
        inventory_crop = _crop(frame, self.config["inventory_region"])
        inventory_slots_crop = _crop(frame, self.config["inventory_slots_region"])
        loot_crop = _crop(frame, self.config["loot_region"])

        health_ratio = min(
            1.0, _dual_hsv_ratio(health_crop, self.config["health_red_hsv"]) / 0.52
        )
        enemy_ratio = _dual_hsv_ratio(enemy_crop, self.config["enemy_red_hsv"])

        gray_inventory = cv2.cvtColor(inventory_crop, cv2.COLOR_BGR2GRAY)
        inventory_brightness = float(np.mean(gray_inventory > 145))
        inventory_fill_ratio = self._inventory_fill_ratio(inventory_slots_crop)

        # A cheap first-pass loot hint: bright, low-saturation label-like pixels.
        loot_hsv = cv2.cvtColor(loot_crop, cv2.COLOR_BGR2HSV)
        loot_mask = cv2.inRange(
            loot_hsv,
            np.array([0, 0, 175], dtype=np.uint8),
            np.array([179, 100, 255], dtype=np.uint8),
        )
        loot_ratio = float(cv2.countNonZero(loot_mask) / loot_mask.size)

        return Observation(
            health_ratio=health_ratio,
            enemy_visible=enemy_ratio >= thresholds["enemy_pixel_ratio"],
            inventory_open=inventory_brightness >= thresholds["inventory_brightness_ratio"],
            inventory_fill_ratio=inventory_fill_ratio,
            loot_hint=loot_ratio >= 0.008,
        )

    def _inventory_fill_ratio(self, image: np.ndarray) -> float:
        rows = int(self.inventory_config.get("rows", 4))
        columns = int(self.inventory_config.get("columns", 10))
        edge_threshold = float(
            self.config["thresholds"].get("inventory_slot_edge_ratio", 0.055)
        )
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        occupied = 0
        total = rows * columns
        for row in range(rows):
            for column in range(columns):
                top = round(row * height / rows)
                bottom = round((row + 1) * height / rows)
                left = round(column * width / columns)
                right = round((column + 1) * width / columns)
                cell = gray[top:bottom, left:right]
                inset_y = max(1, round(cell.shape[0] * 0.15))
                inset_x = max(1, round(cell.shape[1] * 0.15))
                interior = cell[
                    inset_y : cell.shape[0] - inset_y,
                    inset_x : cell.shape[1] - inset_x,
                ]
                edges = cv2.Canny(interior, 70, 150)
                edge_ratio = float(cv2.countNonZero(edges) / edges.size)
                if edge_ratio >= edge_threshold:
                    occupied += 1
        return occupied / total
