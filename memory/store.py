"""Memory: "learns from itself" (P1 Part B).

Scamurai remembers what it caught and uses it on the next run. It learns ONLY from its own verdicts:
decoy hits it could attribute to a page, hidden or bot-only text, and commands it blocked. Never from page
text on its own, never from `reason_given`, never from the LLM's opinion. Otherwise an attacker could
teach it, which is the exact attack we defend against.

Trust only goes down automatically (min of stored and new); only forget() resets it.
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Optional

from core.config import ROOT
from views.claims import key, sentences

DB = ROOT / "data" / "memory.db"
MIN_FINGERPRINT = 20   # "Great phone!" must never match anything

SCHEMA = """
CREATE TABLE IF NOT EXISTS threats(fingerprint TEXT PRIMARY KEY, text TEXT, kind TEXT, seller TEXT,
                                   page_id TEXT, run_id INT, hits INT DEFAULT 0);
CREATE TABLE IF NOT EXISTS sellers(name TEXT PRIMARY KEY, trust INT);
CREATE TABLE IF NOT EXISTS user_rules(action TEXT, item TEXT, verdict TEXT, ts REAL);
"""


def fingerprint(sentence: str) -> Optional[str]:
    k = key(sentence)
    return k if len(k) >= MIN_FINGERPRINT else None


class Memory:
    def __init__(self, path: Path | str = DB):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    # ------------------------------------------------------------ learning
    def _store(self, text: str, kind: str, seller: Optional[str], page_id: Optional[str], run_id) -> None:
        for s in sentences(text):
            fp = fingerprint(s)
            if fp:
                self.db.execute("INSERT OR IGNORE INTO threats(fingerprint, text, kind, seller, page_id, run_id, hits) "
                                "VALUES (?, ?, ?, ?, ?, ?, 0)", (fp, s, kind, seller, page_id, run_id))

    def next_run_id(self) -> int:
        return (self.db.execute("SELECT MAX(run_id) FROM threats").fetchone()[0] or 0) + 1

    def remember_run(self, session, run_id=None) -> None:
        run_id = run_id or self.next_run_id()
        pages_by_id = {p["page_id"]: p for p in session.pages.values()}

        # 1. Decoy hits Scamurai attributed to a page. Unattributed hits (seller None) teach nothing.
        for f in session.flagged:
            if f.get("seller") and f.get("text"):
                page_id = next((p["page_id"] for p in session.pages.values()
                                if any(b["text"] == f["text"] for b in p["capture"].agent_blocks)), None)
                self._store(f["text"], "decoy", f["seller"], page_id, run_id)

        # 2. Hidden or bot-only text found by the two views ("unverified" is too generic).
        for b in session.bait_found:
            if b.get("tag") in ("hidden", "bot_only"):
                self._store(b["text"], b["tag"], b.get("seller"), b.get("page_id"), run_id)

        # 3. Commands the firewall stopped, where a key detail was seller-sourced. The block of page text
        #    that contains that value is the command. reason_given is never looked at.
        for h in session.history:
            if h["decision"]["decision"] not in ("blocked", "rejected_by_vote"):
                continue
            page = pages_by_id.get(h["action"].get("page_id"))
            if not page:
                continue
            for d in h["action"]["details"].values():
                if d["source"] != "seller" or not key(d["value"]):
                    continue
                for block in page["capture"].agent_blocks:
                    if key(d["value"]) in key(block["text"]):
                        self._store(block["text"], "command", page["seller"], page["page_id"], run_id)

        # 4. Trust never rises automatically.
        for seller, t in session.trust.items():
            old = self.trust_of(seller)
            self.db.execute("INSERT OR REPLACE INTO sellers(name, trust) VALUES (?, ?)",
                            (seller, t if old is None else min(old, t)))
        self.db.commit()

    # ------------------------------------------------------------ recall
    def known_threat(self, text: str) -> Optional[dict]:
        k = key(text)
        if not k:
            return None
        for row in self.db.execute("SELECT * FROM threats"):
            if row["fingerprint"] in k:
                self.db.execute("UPDATE threats SET hits = hits + 1 WHERE fingerprint = ?", (row["fingerprint"],))
                self.db.commit()
                return dict(row)
        return None

    def trust_of(self, seller: str) -> Optional[int]:
        row = self.db.execute("SELECT trust FROM sellers WHERE name = ?", (seller,)).fetchone()
        return None if row is None else row["trust"]

    def all_trust(self) -> dict[str, int]:
        return {r["name"]: r["trust"] for r in self.db.execute("SELECT name, trust FROM sellers")}

    def stats(self) -> dict:
        n = lambda t: self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        return {"threats": n("threats"), "sellers": n("sellers"), "rules": n("user_rules")}

    def forget(self) -> None:
        self.db.executescript("DELETE FROM threats; DELETE FROM sellers; DELETE FROM user_rules;")
        self.db.commit()

    # ------------------------------------------------------------ the user's own decisions
    def record_user_decision(self, action: str, item: str, verdict: str) -> None:
        self.db.execute("INSERT INTO user_rules(action, item, verdict, ts) VALUES (?, ?, ?, ?)",
                        (action, item or "", verdict, time.time()))
        self.db.commit()

    def user_verdict(self, action: str, item: str) -> Optional[str]:
        row = self.db.execute("SELECT verdict FROM user_rules WHERE action = ? AND item = ? ORDER BY ts DESC LIMIT 1",
                              (action, item or "")).fetchone()
        return None if row is None else row["verdict"]

    def voter_context(self, action: str, item: str) -> str:
        v = self.user_verdict(action, item)
        if v is None:
            return ""
        return f"The user {v} this same action ({action} {item}) before."
