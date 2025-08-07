import asyncio

import pytest

from casebuilder.services.upgrade_combo import AsyncUpgradeManager


@pytest.mark.asyncio
async def test_async_upgrade_manager():
    calls = []

    async def step_a():
        await asyncio.sleep(0)
        calls.append("a")

    async def step_b():
        await asyncio.sleep(0)
        calls.append("b")

    manager = AsyncUpgradeManager()
    manager.register("step_a", step_a)
    manager.register("step_b", step_b)

    applied = await manager.apply_all()

    assert calls == ["a", "b"]
    assert applied == ["step_a", "step_b"]
