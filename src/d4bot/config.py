from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AppConfig:
    path: Path
    data: dict[str, Any]

    def section(self, name: str) -> dict[str, Any]:
        value = self.data.get(name, {})
        if not isinstance(value, dict):
            raise ValueError(f"Config section {name!r} must be a mapping")
        return value


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path).resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError("Root configuration must be a mapping")
    mode = data.get("runtime", {}).get("mode", "dry_run")
    if mode not in {"dry_run", "native", "macro_hotkey"}:
        raise ValueError(f"Unsupported runtime.mode: {mode}")
    return AppConfig(path=config_path, data=data)


def normalized_point(point: list[float], width: int, height: int) -> tuple[int, int]:
    if len(point) != 2 or not all(0 <= value <= 1 for value in point):
        raise ValueError(f"Invalid normalized point: {point}")
    return round(point[0] * width), round(point[1] * height)


def normalized_region(
    region: list[float], width: int, height: int
) -> tuple[int, int, int, int]:
    if len(region) != 4 or not all(0 <= value <= 1 for value in region):
        raise ValueError(f"Invalid normalized region: {region}")
    left, top, right, bottom = region
    if left >= right or top >= bottom:
        raise ValueError(f"Invalid normalized region bounds: {region}")
    return (
        round(left * width),
        round(top * height),
        round(right * width),
        round(bottom * height),
    )

