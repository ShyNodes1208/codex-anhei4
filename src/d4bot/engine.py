from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

import cv2
import keyboard
import yaml

from .boss import BossSummoner
from .capture import Frame, ScreenCapture
from .combat import BarbarianCombat
from .config import AppConfig
from .input import InputController, InputSafety
from .inventory import InventoryController
from .loot import LootController
from .route import RouteController
from .vision import Observation, VisionEngine

logger = logging.getLogger(__name__)


class State(Enum):
    OBSERVE = auto()
    SUMMON_BOSS = auto()
    SUMMON_TRAVEL = auto()
    INTERACT_SUMMON = auto()
    POST_SUMMON_WAIT = auto()
    MOVE_CORNER = auto()
    CORNER_TRAVEL = auto()
    CORNER_WAIT = auto()
    COMBAT = auto()
    MOVE_CHEST = auto()
    CHEST_TRAVEL = auto()
    OPEN_CHEST = auto()
    WAIT_CHEST_LOOT = auto()
    LOOT_CHEST = auto()
    OPEN_INVENTORY = auto()
    WAIT_INVENTORY = auto()
    RETURN_TOWN = auto()
    WAIT_TOWN = auto()
    MOVE_STASH = auto()
    STASH_TRAVEL = auto()
    OPEN_STASH = auto()
    WAIT_STASH = auto()
    DEPOSIT_STASH = auto()
    VERIFY_DEPOSIT = auto()
    MOVE_RETURN_PORTAL = auto()
    PORTAL_TRAVEL = auto()
    USE_RETURN_PORTAL = auto()
    WAIT_RETURN = auto()
    RETREAT = auto()
    PAUSED = auto()
    STOPPED = auto()


@dataclass
class Runtime:
    state: State = State.OBSERVE
    previous_state: State = State.OBSERVE
    state_started: float = 0.0
    last_enemy_seen: float = 0.0
    enemy_clear_frames: int = 0
    boss_seen: bool = False
    boss_requested: bool = False
    cycle_count: int = 0
    chest_loot_attempts: int = 0
    loot_clear_frames: int = 0


class AutomationEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.runtime_config = config.section("runtime")
        self.inventory_config = config.section("inventory")
        self.vision_config = config.section("vision")
        self.safety = InputSafety(self.runtime_config["game_window_title"])
        self.controller = InputController(self.runtime_config["mode"], self.safety)
        self.capture = ScreenCapture(config.section("capture").get("monitor", 1))
        self.vision = VisionEngine(self.vision_config, self.inventory_config)
        self.combat = BarbarianCombat(
            config.section("barbarian"),
            self.controller,
            self.runtime_config["mode"],
        )
        self.loot = LootController(config.section("loot"), self.controller)
        self.route = RouteController(config.section("route"), self.controller)
        self.inventory = InventoryController(self.inventory_config, self.controller)
        boss_path = config.path.parent / "bosses" / "butcher.yaml"
        with boss_path.open("r", encoding="utf-8") as handle:
            self.boss_config = yaml.safe_load(handle) or {}
        self.boss = BossSummoner(self.boss_config, self.controller)
        self.runtime = Runtime(state_started=time.monotonic())
        self.latest_frame: Frame | None = None
        self.output_dir = Path("runtime")
        self.output_dir.mkdir(exist_ok=True)

    def install_hotkeys(self) -> None:
        keyboard.add_hotkey(self.runtime_config["enable_hotkey"], self._toggle_enabled)
        keyboard.add_hotkey(self.runtime_config["pause_hotkey"], self._toggle_pause)
        keyboard.add_hotkey(
            self.runtime_config["boss_summon_hotkey"], self._request_boss_summon
        )
        keyboard.add_hotkey(
            self.runtime_config["emergency_stop_hotkey"], self._emergency_stop
        )

    def _toggle_enabled(self) -> None:
        if self.safety.enabled:
            self.combat.stop_whirlwind(self.latest_frame)
            self.safety.enabled = False
            if self.runtime.state not in {State.PAUSED, State.STOPPED}:
                self.runtime.previous_state = self.runtime.state
                self._transition(State.PAUSED, self.latest_frame)
        else:
            self.safety.enabled = True
            if self.runtime.state == State.OBSERVE:
                self._transition(State.SUMMON_BOSS, self.latest_frame)
            elif self.runtime.state == State.PAUSED:
                self._transition(self.runtime.previous_state, self.latest_frame)
        logger.warning("Input enabled: %s", self.safety.enabled)

    def _toggle_pause(self) -> None:
        if self.runtime.state == State.PAUSED:
            if not self.safety.enabled:
                logger.warning("Use F8 to re-enable input before resuming")
                return
            self._transition(self.runtime.previous_state, self.latest_frame)
        else:
            self.combat.stop_whirlwind(self.latest_frame)
            self.runtime.previous_state = self.runtime.state
            self._transition(State.PAUSED, self.latest_frame)

    def _request_boss_summon(self) -> None:
        if not self.safety.enabled or self.runtime.state in {State.PAUSED, State.STOPPED}:
            logger.warning("Boss summon ignored: input is not enabled")
            return
        self.runtime.boss_requested = True
        logger.warning("Boss summon requested")

    def _emergency_stop(self) -> None:
        self.combat.stop_whirlwind(self.latest_frame)
        self.safety.stopped = True
        self.safety.enabled = False
        self._transition(State.STOPPED, self.latest_frame)
        logger.critical("Emergency stop triggered")

    def _transition(self, new_state: State, frame: Frame | None = None) -> None:
        if self.runtime.state == new_state:
            return
        logger.info(
            "State: %s -> %s (cycle %d)",
            self.runtime.state.name,
            new_state.name,
            self.runtime.cycle_count,
        )
        self.runtime.previous_state = self.runtime.state
        self.runtime.state = new_state
        self.runtime.state_started = time.monotonic()
        if frame is not None and self.runtime_config.get(
            "screenshot_on_transition", True
        ):
            stamp = time.strftime("%Y%m%d-%H%M%S")
            cv2.imwrite(
                str(
                    self.output_dir
                    / f"{stamp}-c{self.runtime.cycle_count}-{new_state.name}.jpg"
                ),
                frame.image,
            )

    def _elapsed(self) -> float:
        return time.monotonic() - self.runtime.state_started

    def _area_clear(self) -> bool:
        loot_config = self.config.section("loot")
        return (
            time.monotonic() - self.runtime.last_enemy_seen
            >= float(loot_config.get("enemy_clear_seconds", 2.0))
            and self.runtime.enemy_clear_frames
            >= int(loot_config.get("enemy_clear_frames", 8))
        )

    def _pause_with_error(self, message: str, frame: Frame) -> None:
        logger.error(message)
        self.combat.stop_whirlwind(frame)
        self.safety.enabled = False
        self._transition(State.PAUSED, frame)

    def _decide(self, observation: Observation, frame: Frame) -> None:
        state = self.runtime.state
        if state in {State.PAUSED, State.STOPPED, State.OBSERVE}:
            return
        if (
            self.controller.mode != "dry_run"
            and self.safety.enabled
            and not self.safety.ready()
        ):
            self._pause_with_error("Game window lost focus", frame)
            return
        if self.runtime.boss_requested:
            self.runtime.boss_requested = False
            if self.combat.end_run(frame):
                self._transition(State.SUMMON_BOSS, frame)
            return

        if state == State.SUMMON_BOSS:
            if not self.combat.end_run(frame):
                return
            self.runtime.boss_seen = False
            self.runtime.enemy_clear_frames = 0
            if self.boss.move_to_summon_device(frame):
                self._transition(State.SUMMON_TRAVEL, frame)
            return

        if state == State.SUMMON_TRAVEL:
            travel = float(
                self.boss_config["summon"].get("move_to_device_seconds", 2.0)
            )
            if self._elapsed() >= travel:
                self._transition(State.INTERACT_SUMMON, frame)
            return

        if state == State.INTERACT_SUMMON:
            if self.boss.interact():
                self._transition(State.POST_SUMMON_WAIT, frame)
            return

        if state == State.POST_SUMMON_WAIT:
            wait = float(
                self.boss_config["summon"].get("post_interact_wait_seconds", 1.5)
            )
            if self._elapsed() >= wait:
                self._transition(State.MOVE_CORNER, frame)
            return

        if state == State.MOVE_CORNER:
            if self.boss.move_to_room_corner(frame):
                self._transition(State.CORNER_TRAVEL, frame)
            return

        if state == State.CORNER_TRAVEL:
            travel = float(
                self.boss_config["summon"].get("move_to_corner_seconds", 2.5)
            )
            if self._elapsed() >= travel:
                self._transition(State.CORNER_WAIT, frame)
            return

        if state == State.CORNER_WAIT:
            wait = float(self.boss_config["summon"].get("corner_wait_seconds", 3.0))
            if self._elapsed() >= wait:
                self.runtime.last_enemy_seen = time.monotonic()
                if self.combat.begin_run(frame):
                    self._transition(State.COMBAT, frame)
            return

        if state == State.COMBAT:
            self.route.tick(frame, cursor_only=True)
            if observation.health_ratio <= float(
                self.config.section("barbarian")["retreat_health_ratio"]
            ):
                self._transition(State.RETREAT, frame)
                return
            if observation.enemy_visible:
                self.runtime.boss_seen = True
                self.runtime.last_enemy_seen = time.monotonic()
                self.runtime.enemy_clear_frames = 0
            else:
                self.runtime.enemy_clear_frames += 1
            if self.runtime.boss_seen and self._area_clear():
                if self.combat.end_run(frame):
                    self._transition(State.MOVE_CHEST, frame)
                return
            if self._elapsed() >= float(
                self.boss_config["behavior"].get("max_fight_seconds", 240)
            ):
                self._transition(State.RETREAT, frame)
                return
            if (
                not self.runtime.boss_seen
                and self._elapsed()
                >= float(
                    self.boss_config["summon"].get("wait_for_boss_seconds", 12.0)
                )
            ):
                self._pause_with_error("Boss was never detected", frame)
            return

        if state == State.MOVE_CHEST:
            if self.boss.move_to_chest(frame):
                self._transition(State.CHEST_TRAVEL, frame)
            return

        if state == State.CHEST_TRAVEL:
            travel = float(
                self.boss_config["loot"].get("move_to_chest_seconds", 2.0)
            )
            if self._elapsed() >= travel:
                self._transition(State.OPEN_CHEST, frame)
            return

        if state == State.OPEN_CHEST:
            if self.boss.open_chest():
                self._transition(State.WAIT_CHEST_LOOT, frame)
            return

        if state == State.WAIT_CHEST_LOOT:
            wait = float(
                self.boss_config["loot"].get("chest_open_wait_seconds", 1.5)
            )
            if self._elapsed() >= wait:
                self.runtime.chest_loot_attempts = 0
                self.runtime.loot_clear_frames = 0
                self._transition(State.LOOT_CHEST, frame)
            return

        if state == State.LOOT_CHEST:
            if observation.enemy_visible:
                self._pause_with_error("Enemy detected during chest looting", frame)
                return
            loot_config = self.config.section("loot")
            max_attempts = int(loot_config.get("chest_loot_attempts", 12))
            clear_frames = int(loot_config.get("loot_clear_frames", 3))
            if observation.loot_hint:
                self.runtime.loot_clear_frames = 0
                if self.runtime.chest_loot_attempts >= max_attempts:
                    self._pause_with_error(
                        "Loot remains after maximum pickup attempts", frame
                    )
                    return
                if self.loot.collect_once(frame):
                    self.runtime.chest_loot_attempts += 1
                return
            self.runtime.loot_clear_frames += 1
            if self.runtime.loot_clear_frames >= clear_frames:
                self._transition(State.OPEN_INVENTORY, frame)
            return

        if state == State.OPEN_INVENTORY:
            if self.inventory.open_inventory():
                self._transition(State.WAIT_INVENTORY, frame)
            return

        if state == State.WAIT_INVENTORY:
            if self._elapsed() < float(
                self.inventory_config.get("open_wait_seconds", 1.0)
            ):
                return
            if not observation.inventory_open:
                self._pause_with_error("Inventory did not open", frame)
                return
            fill = observation.inventory_fill_ratio
            full = fill >= float(self.inventory_config.get("full_ratio", 0.90))
            logger.info("Inventory fill ratio: %.1f%%; full=%s", fill * 100, full)
            if not self.inventory.close_inventory():
                self._pause_with_error("Could not close inventory", frame)
                return
            if full:
                self._transition(State.RETURN_TOWN, frame)
            else:
                self.runtime.cycle_count += 1
                self._transition(State.SUMMON_BOSS, frame)
            return

        if state == State.RETURN_TOWN:
            if self.inventory.return_to_town():
                self._transition(State.WAIT_TOWN, frame)
            return

        if state == State.WAIT_TOWN:
            if self._elapsed() >= float(
                self.inventory_config.get("town_load_seconds", 8.0)
            ):
                self._transition(State.MOVE_STASH, frame)
            return

        if state == State.MOVE_STASH:
            if self.inventory.move_to_stash(frame):
                self._transition(State.STASH_TRAVEL, frame)
            return

        if state == State.STASH_TRAVEL:
            if self._elapsed() >= float(
                self.inventory_config.get("move_to_stash_seconds", 4.0)
            ):
                self._transition(State.OPEN_STASH, frame)
            return

        if state == State.OPEN_STASH:
            if self.inventory.open_stash():
                self._transition(State.WAIT_STASH, frame)
            return

        if state == State.WAIT_STASH:
            if self._elapsed() >= float(
                self.inventory_config.get("stash_open_wait_seconds", 2.0)
            ):
                if not observation.inventory_open:
                    self._pause_with_error("Stash did not open", frame)
                    return
                self._transition(State.DEPOSIT_STASH, frame)
            return

        if state == State.DEPOSIT_STASH:
            transferred = self.inventory.deposit_items(
                frame, self.vision_config["inventory_slots_region"]
            )
            if transferred == 0:
                self._pause_with_error("No inventory items were transferred", frame)
                return
            self._transition(State.VERIFY_DEPOSIT, frame)
            return

        if state == State.VERIFY_DEPOSIT:
            if self._elapsed() < float(
                self.inventory_config.get("deposit_verify_seconds", 1.0)
            ):
                return
            if observation.inventory_fill_ratio > float(
                self.inventory_config.get("empty_ratio", 0.05)
            ):
                self._pause_with_error(
                    "Inventory is not empty after stash transfer", frame
                )
                return
            if not self.controller.press(
                self.inventory_config.get("close_stash_key", "esc")
            ):
                self._pause_with_error("Could not close stash", frame)
                return
            self._transition(State.MOVE_RETURN_PORTAL, frame)
            return

        if state == State.MOVE_RETURN_PORTAL:
            if self.inventory.move_to_return_portal(frame):
                self._transition(State.PORTAL_TRAVEL, frame)
            return

        if state == State.PORTAL_TRAVEL:
            if self._elapsed() >= float(
                self.inventory_config.get("move_to_portal_seconds", 3.0)
            ):
                self._transition(State.USE_RETURN_PORTAL, frame)
            return

        if state == State.USE_RETURN_PORTAL:
            if self.inventory.use_return_portal():
                self._transition(State.WAIT_RETURN, frame)
            return

        if state == State.WAIT_RETURN:
            if self._elapsed() >= float(
                self.inventory_config.get("return_load_seconds", 8.0)
            ):
                self.runtime.cycle_count += 1
                self._transition(State.SUMMON_BOSS, frame)
            return

        if state == State.RETREAT:
            if not self.combat.end_run(frame):
                self._pause_with_error("Could not stop Whirlwind for retreat", frame)
                return
            self.controller.press(self.config.section("barbarian")["evade_key"])
            if not self.inventory.return_to_town():
                self._pause_with_error("Could not return to town", frame)
                return
            self.safety.enabled = False
            self._transition(State.PAUSED, frame)

    def run(self) -> None:
        self.install_hotkeys()
        logger.warning(
            "Started in %s mode. %s starts the loop; %s pauses; %s stops.",
            self.controller.mode,
            self.runtime_config["enable_hotkey"],
            self.runtime_config["pause_hotkey"],
            self.runtime_config["emergency_stop_hotkey"],
        )
        try:
            while self.runtime.state != State.STOPPED:
                frame = self.capture.grab()
                self.latest_frame = frame
                observation = self.vision.observe(frame)
                logger.debug(
                    "health=%.2f enemy=%s inventory=%s fill=%.2f loot=%s",
                    observation.health_ratio,
                    observation.enemy_visible,
                    observation.inventory_open,
                    observation.inventory_fill_ratio,
                    observation.loot_hint,
                )
                if self.runtime.state == State.COMBAT:
                    result = self.combat.tick(frame, observation.health_ratio)
                    if result == "retreat":
                        self._transition(State.RETREAT, frame)
                    elif result == "input_blocked":
                        self._pause_with_error("Combat input was blocked", frame)
                self._decide(observation, frame)
                time.sleep(float(self.runtime_config.get("tick_seconds", 0.15)))
        finally:
            self.combat.stop_whirlwind(self.latest_frame)
            self.safety.enabled = False
            self.capture.close()
            keyboard.unhook_all_hotkeys()
