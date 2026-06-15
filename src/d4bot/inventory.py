from __future__ import annotations

import logging
import time

import cv2
import numpy as np

from .capture import Frame
from .config import normalized_point, normalized_region
from .input import InputController

logger = logging.getLogger(__name__)


class InventoryController:
    def __init__(self, config: dict, controller: InputController) -> None:
        self.config = config
        self.controller = controller

    def open_inventory(self) -> bool:
        return self.controller.press(self.config.get("open_key", "i"))

    def close_inventory(self) -> bool:
        return self.controller.press(self.config.get("open_key", "i"))

    def return_to_town(self) -> bool:
        return self.controller.press(self.config.get("return_to_town_key", "t"))

    def move_to_stash(self, frame: Frame) -> bool:
        x, y = normalized_point(
            self.config["stash_world_position"], frame.width, frame.height
        )
        return self.controller.move_and_click(frame.left + x, frame.top + y)

    def open_stash(self) -> bool:
        return self.controller.press("f")

    def move_to_return_portal(self, frame: Frame) -> bool:
        x, y = normalized_point(
            self.config["return_portal_position"], frame.width, frame.height
        )
        return self.controller.move_and_click(frame.left + x, frame.top + y)

    def use_return_portal(self) -> bool:
        return self.controller.press("f")

    def deposit_items(self, frame: Frame, slots_region: list[float]) -> int:
        left, top, right, bottom = normalized_region(
            slots_region, frame.width, frame.height
        )
        rows = int(self.config.get("rows", 4))
        columns = int(self.config.get("columns", 10))
        crop = frame.image[top:bottom, left:right]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        edge_threshold = float(self.config.get("slot_edge_ratio", 0.055))
        transferred = 0
        for row in range(rows):
            for column in range(columns):
                cell_top = round(row * gray.shape[0] / rows)
                cell_bottom = round((row + 1) * gray.shape[0] / rows)
                cell_left = round(column * gray.shape[1] / columns)
                cell_right = round((column + 1) * gray.shape[1] / columns)
                cell = gray[cell_top:cell_bottom, cell_left:cell_right]
                inset_y = max(1, round(cell.shape[0] * 0.15))
                inset_x = max(1, round(cell.shape[1] * 0.15))
                interior = cell[
                    inset_y : cell.shape[0] - inset_y,
                    inset_x : cell.shape[1] - inset_x,
                ]
                edges = cv2.Canny(interior, 70, 150)
                edge_ratio = float(cv2.countNonZero(edges) / edges.size)
                if (
                    self.config.get("conservative_mode", True)
                    and edge_ratio < edge_threshold
                ):
                    continue
                x = frame.left + left + round((column + 0.5) * (right - left) / columns)
                y = frame.top + top + round((row + 0.5) * (bottom - top) / rows)
                succeeded = self.controller.modified_click(
                    x,
                    y,
                    modifier=self.config.get("transfer_modifier", "shift"),
                    button=self.config.get("transfer_button", "left"),
                )
                if not succeeded:
                    logger.warning("Inventory transfer input was blocked")
                    return transferred
                transferred += 1
                time.sleep(float(self.config.get("transfer_interval", 0.08)))
        logger.info("Transferred %d inventory slots to stash", transferred)
        return transferred
