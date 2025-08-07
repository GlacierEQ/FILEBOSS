import pytest
from casebuilder.services.upgrade_combo import UpgradeManager, ComboService


def test_upgrade_manager_register_and_apply():
    calls = []

    def step_a():
        calls.append("a")

    def step_b():
        calls.append("b")

    manager = UpgradeManager()
    manager.register("step_a", step_a)
    manager.register("step_b", step_b)

    applied = manager.apply_all()

    assert calls == ["a", "b"]
    assert applied == ["step_a", "step_b"]


def test_combo_service_create_and_retrieve():
    service = ComboService()
    service.create_combo("combo1", ["e1", "e2"])

    assert service.get_combo("combo1") == ["e1", "e2"]
    assert service.list_combos() == {"combo1": ["e1", "e2"]}


def test_combo_service_duplicate():
    service = ComboService()
    service.create_combo("combo1", ["e1"])

    with pytest.raises(ValueError):
        service.create_combo("combo1", ["e2"])
