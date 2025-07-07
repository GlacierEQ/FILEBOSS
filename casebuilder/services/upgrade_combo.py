"""Upgrade and combo management services."""

from __future__ import annotations

from typing import Awaitable, Callable, Dict, Iterable, List


class UpgradeManager:
    """Manage sequential upgrade steps."""

    def __init__(self) -> None:
        self._upgrades: Dict[str, Callable[[], None]] = {}

    def register(self, name: str, func: Callable[[], None]) -> None:
        """Register a new upgrade function."""
        if name in self._upgrades:
            raise ValueError(f"Upgrade {name} already registered")
        self._upgrades[name] = func

    def apply_all(self) -> List[str]:
        """Apply all registered upgrades in order of registration."""
        applied: List[str] = []
        for name, func in self._upgrades.items():
            func()
            applied.append(name)
        return applied


class AsyncUpgradeManager:
    """Manage sequential asynchronous upgrade steps."""

    def __init__(self) -> None:
        self._upgrades: Dict[str, Callable[[], Awaitable[None]]] = {}

    def register(self, name: str, func: Callable[[], Awaitable[None]]) -> None:
        """Register a new async upgrade function."""
        if name in self._upgrades:
            raise ValueError(f"Upgrade {name} already registered")
        self._upgrades[name] = func

    async def apply_all(self) -> List[str]:
        """Apply all registered async upgrades in order."""
        applied: List[str] = []
        for name, func in self._upgrades.items():
            await func()
            applied.append(name)
        return applied


class ComboService:
    """Manage combos of evidence identifiers."""

    def __init__(self) -> None:
        self._combos: Dict[str, List[str]] = {}

    def create_combo(self, name: str, evidence_ids: Iterable[str]) -> None:
        """Create a combo with the given evidence IDs."""
        if name in self._combos:
            raise ValueError(f"Combo {name} already exists")
        self._combos[name] = list(evidence_ids)

    def get_combo(self, name: str) -> List[str]:
        """Retrieve a combo by name."""
        return self._combos.get(name, [])

    def list_combos(self) -> Dict[str, List[str]]:
        """List all stored combos."""
        return dict(self._combos)
