import numpy as np

from d4bot.capture import Frame
from d4bot.combat import BarbarianCombat


class FakeInput:
    def __init__(self, succeeds=True) -> None:
        self.actions = []
        self.succeeds = succeeds

    def press(self, key, duration=0.05):
        self.actions.append(("press", key))
        return self.succeeds

    def click(self, x, y, button="left"):
        self.actions.append(("click", button, x, y))
        return self.succeeds


def config():
    return {
        "potion_key": "q",
        "evade_key": "space",
        "retreat_health_ratio": 0.12,
        "potion_health_ratio": 0.42,
        "opener": {"name": "call_of_the_ancients", "key": "1"},
        "whirlwind": {
            "toggle_key": "right",
            "restart_delay": 0.25,
        },
        "macro_hotkeys": {"combat_rotation": "f6"},
        "cooldown_skills": [
            {"name": "iron_skin", "key": "5", "cooldown": 14.0, "priority": 95},
            {
                "name": "challenging_shout",
                "key": "2",
                "cooldown": 25.0,
                "priority": 90,
            },
        ],
    }


def frame():
    return Frame(np.zeros((1080, 1920, 3), dtype=np.uint8), 0, 0)


def test_begin_run_uses_opener_once_then_starts_whirlwind() -> None:
    input_controller = FakeInput()
    combat = BarbarianCombat(config(), input_controller, "native")
    combat.begin_run(frame())
    combat.ensure_whirlwind(frame())
    assert input_controller.actions == [
        ("press", "1"),
        ("click", "right", 960, 486),
    ]
    assert combat.whirlwind_active is True


def test_stop_whirlwind_toggles_only_when_active() -> None:
    input_controller = FakeInput()
    combat = BarbarianCombat(config(), input_controller, "native")
    combat.begin_run(frame())
    combat.stop_whirlwind(frame())
    combat.stop_whirlwind(frame())
    assert input_controller.actions.count(("click", "right", 960, 486)) == 2
    assert combat.whirlwind_active is False


def test_retreat_wins_over_actions() -> None:
    input_controller = FakeInput()
    combat = BarbarianCombat(config(), input_controller, "native")
    assert combat.tick(frame(), 0.10) == "retreat"
    assert input_controller.actions == []


def test_cooldown_skill_fires_while_whirlwind_stays_active() -> None:
    input_controller = FakeInput()
    combat = BarbarianCombat(config(), input_controller, "native")
    combat.begin_run(frame())
    combat.last_toggle = 0.0
    assert combat.tick(frame(), 0.8) == "fighting"
    assert ("press", "5") in input_controller.actions
    assert combat.whirlwind_active is True


def test_whirlwind_restart_delay_defers_other_skills() -> None:
    input_controller = FakeInput()
    combat = BarbarianCombat(config(), input_controller, "native")
    combat.begin_run(frame())
    combat.tick(frame(), 0.8)
    assert ("press", "5") not in input_controller.actions


def test_potion_is_rate_limited() -> None:
    input_controller = FakeInput()
    combat = BarbarianCombat(config(), input_controller, "native")
    combat.begin_run(frame())
    combat.last_toggle = 0.0
    combat.tick(frame(), 0.3)
    combat.tick(frame(), 0.3)
    assert input_controller.actions.count(("press", "q")) == 1


def test_blocked_input_does_not_fake_whirlwind_state() -> None:
    input_controller = FakeInput(succeeds=False)
    combat = BarbarianCombat(config(), input_controller, "native")
    assert combat.begin_run(frame()) is False
    assert combat.opener_used is False
    assert combat.whirlwind_active is False
    assert combat.run_started is False


def test_begin_run_normalizes_an_existing_whirlwind_state() -> None:
    input_controller = FakeInput()
    combat = BarbarianCombat(config(), input_controller, "native")
    combat.run_started = True
    combat.opener_used = True
    combat.whirlwind_active = True
    assert combat.begin_run(frame()) is True
    assert input_controller.actions == [
        ("click", "right", 960, 486),
        ("press", "1"),
        ("click", "right", 960, 486),
    ]
    assert combat.whirlwind_active is True
