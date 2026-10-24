"""Audit log (SQLite). Every decision stored with its reason."""
from __future__ import annotations

import json
import sqlite3
import time

from core.config import ROOT

DB = ROOT / "data" / "audit.db"


def _conn():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, goal TEXT, setup TEXT, backend TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS decisions (
        run_id INTEGER, step INTEGER, action TEXT, tier TEXT, decision TEXT, why TEXT, payload TEXT)""")
    return c


def start_run(goal: str, setup: str, backend: str) -> int:
    with _conn() as c:
        cur = c.execute("INSERT INTO runs (ts, goal, setup, backend) VALUES (?,?,?,?)", (time.time(), goal, setup, backend))
        return cur.lastrowid


def record(run_id: int, step: int, action: dict, decision: dict) -> None:
    with _conn() as c:
        c.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?,?)",
                  (run_id, step, action["action"], decision["tier"], decision["decision"], decision["why"],
                   json.dumps({"action": action, "decision": decision}, ensure_ascii=False, default=str)))


def decisions(run_id: int) -> list[dict]:
    with _conn() as c:
        rows = c.execute("SELECT step, action, tier, decision, why FROM decisions WHERE run_id=? ORDER BY step", (run_id,))
        return [dict(zip(["step", "action", "tier", "decision", "why"], r)) for r in rows]
