from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from .capture import Frame
from .input import InputController

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Skill:
    name: str
    key: str
    cooldown: float
    priority: int


class BarbarianCombat:
    """Controller for toggle-channel Whirlwind Barbarian builds."""

    def __init__(
        self,
        config: dict,
        controller: InputController,
        input_mode: str,
    ) -> None:
        self.config = config
        self.controller = controller
        self.input_mode = input_mode
        self.skills = sorted(
            (Skill(**entry) for entry in config["cooldown_skills"]),
            key=lambda skill: skill.priority,
            reverse=True,
        )
        self.last_used: dict[str, float] = {}
        self.run_started = False
        self.opener_used = False
        self.whirlwind_active = False
        self.last_toggle = 0.0
        self.last_macro = 0.0
        self.last_potion = 0.0

    def begin_run(self, frame: Frame | None = None) -> bool:
        if self.whirlwind_active and not self.stop_whirlwind(frame):
            return False
        self.run_started = True
        self.opener_used = False
        self.last_used.clear()
        if not self._use_opener():
            self.run_started = False
            return False
        return self.ensure_whirlwind(frame)

    def end_run(self, frame: Frame | None = None) -> bool:
        if not self.stop_whirlwind(frame):
            return False
        self.run_started = False
        return True

    def _use_opener(self) -> bool:
        if self.opener_used:
            return True
        opener = self.config["opener"]
        if not self.controller.press(opener["key"]):
            return False
        self.opener_used = True
        logger.info("Dungeon opener: %s", opener["name"])
        return True

    def _toggle_whirlwind(self, frame: Frame | None = None) -> bool:
        key = self.config["whirlwind"]["toggle_key"]
        if key in {"left", "right", "middle"}:
            if frame is None:
                logger.warning("Cannot toggle mouse-bound Whirlwind without a frame")
                return False
            succeeded = self.controller.click(
                frame.left + frame.width // 2,
                frame.top + int(frame.height * 0.45),
                button=key,
            )
        else:
            succeeded = self.controller.press(key)
        if not succeeded:
            return False
        self.whirlwind_active = not self.whirlwind_active
        self.last_toggle = time.monotonic()
        logger.info("Whirlwind active: %s", self.whirlwind_active)
        return True

    def ensure_whirlwind(self, frame: Frame | None = None) -> bool:
        if not self.run_started:
            return False
        if not self.opener_used:
            if not self._use_opener():
                return False
        if not self.whirlwind_active:
            return self._toggle_whirlwind(frame)
        return True

    def stop_whirlwind(self, frame: Frame | None = None) -> bool:
        if self.whirlwind_active:
            return self._toggle_whirlwind(frame)
        return True

    def tick(self, frame: Frame, health_ratio: float) -> str:
        now = time.monotonic()
        if health_ratio <= float(self.config["retreat_health_ratio"]):
            return "retreat"
        if (
            health_ratio <= float(self.config["potion_health_ratio"])
            and now - self.last_potion
            >= float(self.config.get("potion_cooldown", 1.0))
        ):
            if self.controller.press(self.config["potion_key"]):
                self.last_potion = now

        if not self.ensure_whirlwind(frame):
            return "input_blocked"
        if now - self.last_toggle < float(
            self.config["whirlwind"].get("restart_delay", 0.25)
        ):
            return "fighting"
        if self.input_mode == "macro_hotkey":
            if now - self.last_macro >= 0.65:
                self.controller.press(self.config["macro_hotkeys"]["combat_rotation"])
                self.last_macro = now
            return "fighting"

        for skill in self.skills:
            if now - self.last_used.get(skill.name, 0.0) < skill.cooldown:
                continue
            if not self.controller.press(skill.key):
                return "input_blocked"
            self.last_used[skill.name] = now
            logger.info("Cooldown skill: %s", skill.name)
            return "fighting"
        return "fighting"

    def evade(self) -> None:
        self.controller.press(self.config["evade_key"])
