from __future__ import annotations

import argparse
import logging
from pathlib import Path

import cv2
import yaml

from .capture import ScreenCapture
from .config import load_config, normalized_point, normalized_region
from .engine import AutomationEngine
from .vision import VisionEngine


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def _calibrate(config_path: str) -> None:
    config = load_config(config_path)
    capture = ScreenCapture(config.section("capture").get("monitor", 1))
    try:
        frame = capture.grab()
    finally:
        capture.close()
    image = frame.image.copy()
    colors = {
        "health_region": (0, 0, 255),
        "inventory_region": (255, 0, 0),
        "nearby_enemy_region": (0, 255, 255),
        "loot_region": (0, 255, 0),
    }
    for name, color in colors.items():
        left, top, right, bottom = normalized_region(
            config.section("vision")[name], frame.width, frame.height
        )
        cv2.rectangle(image, (left, top), (right, bottom), color, 2)
        cv2.putText(
            image,
            name,
            (left, max(20, top - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )
    boss_path = config.path.parent / "bosses" / "butcher.yaml"
    with boss_path.open("r", encoding="utf-8") as handle:
        boss_config = yaml.safe_load(handle) or {}
    markers = [
        (
            "butcher_summon",
            normalized_point(
                boss_config["summon"]["device_position"], frame.width, frame.height
            ),
            (255, 0, 255),
        ),
        (
            "room_corner",
            normalized_point(
                boss_config["summon"]["room_corner_position"],
                frame.width,
                frame.height,
            ),
            (255, 128, 0),
        ),
        (
            "boss_chest",
            normalized_point(
                boss_config["loot"]["chest_position"], frame.width, frame.height
            ),
            (0, 128, 255),
        ),
        (
            "town_stash",
            normalized_point(
                config.section("inventory")["stash_world_position"],
                frame.width,
                frame.height,
            ),
            (255, 255, 0),
        ),
        (
            "return_portal",
            normalized_point(
                config.section("inventory")["return_portal_position"],
                frame.width,
                frame.height,
            ),
            (128, 0, 255),
        ),
    ]
    for label, point, color in markers:
        cv2.drawMarker(
            image,
            point,
            color,
            markerType=cv2.MARKER_CROSS,
            markerSize=32,
            thickness=3,
        )
        cv2.putText(
            image,
            label,
            (point[0] + 12, point[1] - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )
    output = Path("runtime/calibration.jpg")
    output.parent.mkdir(exist_ok=True)
    cv2.imwrite(str(output), image)
    observation = VisionEngine(
        config.section("vision"), config.section("inventory")
    ).observe(frame)
    print(f"Saved {output.resolve()}")
    print(f"Observation: {observation}")


def main() -> None:
    parser = argparse.ArgumentParser(description="D4 Barbarian screen assistant")
    parser.add_argument("--config", default="config/default.yaml")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("run")
    subparsers.add_parser("calibrate")
    args = parser.parse_args()
    _configure_logging(args.verbose)
    if args.command == "calibrate":
        _calibrate(args.config)
        return
    AutomationEngine(load_config(args.config)).run()


if __name__ == "__main__":
    main()
