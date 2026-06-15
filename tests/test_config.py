from pathlib import Path

import pytest

from d4bot.config import load_config, normalized_point, normalized_region


def test_default_config_loads() -> None:
    config = load_config(Path("config/default.yaml"))
    assert config.section("runtime")["mode"] == "dry_run"
    assert config.section("barbarian")["potion_key"] == "q"


def test_normalized_geometry() -> None:
    assert normalized_point([0.5, 0.25], 1920, 1080) == (960, 270)
    assert normalized_region([0.1, 0.2, 0.9, 0.8], 100, 200) == (10, 40, 90, 160)


def test_invalid_region_rejected() -> None:
    with pytest.raises(ValueError):
        normalized_region([0.8, 0.2, 0.1, 0.9], 100, 100)
