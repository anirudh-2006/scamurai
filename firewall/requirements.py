"""Numeric requirements in the goal ("at least 20 W") checked against an item's specs.

Specs come only from search results (tool output), never from page text. The ₹ budget is not a
requirement here: the budget has its own rule.
"""
from __future__ import annotations

import re
from typing import Optional

_QTY = re.compile(r"(\d+(?:\.\d+)?)\s*(mAh|GB|W|hours?)\b")


def _unit(u: str) -> str:
    return "hours" if u.lower().startswith("hour") else u


def requirements(goal: str) -> list[tuple[float, str]]:
    """Every number-with-unit in the goal, read as a minimum: "at least 20 W" -> [(20.0, "W")]."""
    return [(float(n), _unit(u)) for n, u in _QTY.findall(goal)]


def describe(reqs: list[tuple[float, str]]) -> str:
    return ", ".join(f"at least {n:g} {u}" for n, u in reqs)


def shortfall(goal: str, specs: list[str]) -> Optional[str]:
    """None if the specs meet every requirement in the goal, else a short reason."""
    have: dict[str, float] = {}
    for spec in specs:
        for n, u in _QTY.findall(spec):
            have[_unit(u)] = max(have.get(_unit(u), 0.0), float(n))
    for n, u in requirements(goal):
        if u not in have:
            return f"no {u} figure in its specs; the goal needs at least {n:g} {u}"
        if have[u] < n:
            return f"{have[u]:g} {u}; the goal needs at least {n:g} {u}"
    return None
