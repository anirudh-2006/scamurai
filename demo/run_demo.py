"""Terminal version of the demo: the same task, plain agent vs Scamurai.

    python -m demo.run_demo                 # demo goal (phones)
    python -m demo.run_demo --task earbuds  # any task from shop/pages.yaml
    python -m demo.run_demo --no-cache      # real LLM: fresh replies, not the cache
    python -m demo.run_demo --memory        # Scamurai remembers what it caught (data/memory.db)
    python -m demo.run_demo --memory --forget   # wipe memory first (do this before every rehearsal)
"""
from __future__ import annotations

import argparse

from agent.llm import from_config, voter_from_config
from agent.session import Session
from agent.shopper import run
from core.config import load_config
from core.setups import PLAIN, SCAMURAI, SETUPS
from memory import Memory
from shop.app import TASKS, ensure_running
from views.capture import TwoViews

ICON = {"low": "🟢", "grey": "🟡", "high": "🔴", "decoy": "🟣"}


def printer(ev: dict) -> None:
    if ev["kind"] == "action":
        icon = ICON[ev["tier"]] if ev["decision"] != "allowed" or ev["tier"] != "low" else "🟢"
        print(f"  {icon} {ev['text']:<55} {ev['decision'].upper():<16} {ev['why']}")
        for v in ev["votes"]:
            print(f"        vote {v['role']:<12} {'APPROVE' if v['approve'] else 'REJECT ':<8} {v['reason']}")
    elif ev["kind"] == "bait":
        print(f"  👻 {ev['text']}")
    elif ev["kind"] == "info":
        print(f"  ·  {ev['text']}")


def summary(rep: dict) -> None:
    r = rep["recommendation"]
    print(f"\n  Recommended: {r['item'] if r else '-'}   Paid automatically: {rep['paid']}   Frozen: {rep['frozen']}")
    for l in rep["leaks"]:
        print(f"  ❌ {l}")
    for f in rep["flagged"]:
        print(f"  🚩 Flagged {f['seller']} for '{f['decoy']}'" if f["seller"] else f"  ⚠️  '{f['decoy']}' touched, no page asked for it (agent error)")
    if rep["seller_trust"]:
        print("  Seller trust:", ", ".join(f"{k} {v}" for k, v in rep["seller_trust"].items()))
    print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default="phones", choices=list(TASKS))
    ap.add_argument("--all-setups", action="store_true", help="run all five setups, not just plain vs Scamurai")
    ap.add_argument("--memory", action="store_true", help="Scamurai runs use and update memory")
    ap.add_argument("--forget", action="store_true", help="wipe memory before running")
    ap.add_argument("--no-cache", action="store_true", help="real LLM: ignore cached replies (fresh runs)")
    a = ap.parse_args()
    cfg = load_config()
    if a.no_cache:
        cfg["llm_cache"] = False
    ensure_running()
    goal = TASKS[a.task]
    if a.forget:
        Memory().forget()
        print("  🧠 Memory wiped")
    with TwoViews() as views:
        for setup in (SETUPS if a.all_setups else [PLAIN, SCAMURAI]):
            print(f"\n=== {setup.name} ===\n  Goal: {goal}")
            s = Session(goal, setup, cfg, views, llm=from_config(cfg), voter_llm=voter_from_config(cfg), on_event=printer,
                        use_memory=a.memory and setup is SCAMURAI)
            summary(run(s))
    if a.memory:
        st = Memory().stats()
        print(f"  🧠 Memory: {st['threats']} threats, {st['sellers']} sellers")


if __name__ == "__main__":
    main()
