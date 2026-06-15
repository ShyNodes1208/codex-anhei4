import numpy as np

from d4bot.capture import Frame
from d4bot.inventory import InventoryController
from d4bot.vision import VisionEngine


class FakeInput:
    def __init__(self, succeeds=True) -> None:
        self.actions = []
        self.succeeds = succeeds

    def modified_click(self, x, y, modifier, button="left"):
        self.actions.append((x, y, modifier, button))
        return self.succeeds


def test_inventory_fill_ratio_blank_and_textured() -> None:
    vision = VisionEngine(
        {"thresholds": {"inventory_slot_edge_ratio": 0.02}},
        {"rows": 4, "columns": 10},
    )
    blank = np.zeros((400, 1000, 3), dtype=np.uint8)
    textured = np.zeros_like(blank)
    textured[:, ::4] = 255
    assert vision._inventory_fill_ratio(blank) == 0.0
    assert vision._inventory_fill_ratio(textured) > 0.9


def test_deposit_visits_only_textured_slots() -> None:
    fake_input = FakeInput()
    controller = InventoryController(
        {
            "rows": 1,
            "columns": 2,
            "slot_edge_ratio": 0.01,
            "conservative_mode": True,
            "transfer_modifier": "shift",
            "transfer_button": "left",
            "transfer_interval": 0,
        },
        fake_input,
    )
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    image[:, :100:3] = 255
    transferred = controller.deposit_items(Frame(image, 10, 20), [0, 0, 1, 1])
    assert transferred == 1
    assert fake_input.actions == [(60, 70, "shift", "left")]


def test_deposit_stops_when_input_is_blocked() -> None:
    fake_input = FakeInput(succeeds=False)
    controller = InventoryController(
        {
            "rows": 1,
            "columns": 1,
            "slot_edge_ratio": 0.01,
            "conservative_mode": True,
            "transfer_modifier": "shift",
            "transfer_button": "left",
            "transfer_interval": 0,
        },
        fake_input,
    )
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    image[:, ::3] = 255
    assert controller.deposit_items(Frame(image, 0, 0), [0, 0, 1, 1]) == 0
