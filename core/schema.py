"""The shared action format. Every part of the system speaks this.

Agree on this file first. Nobody changes it during the hackathon without telling the team.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal, Optional

Source = Literal["user", "seller", "tool"]
Tier = Literal["low", "grey", "high", "decoy"]
Verdict = Literal["allowed", "blocked", "needs_approval", "frozen", "rejected_by_vote", "approved_by_vote"]
ClaimTag = Literal["visible", "hidden", "bot_only"]


@dataclass
class Detail:
    value: str
    source: Source


@dataclass
class ProposedAction:
    action: str                                   # e.g. "send_address", "add_to_cart", "open_page"
    details: dict[str, Detail] = field(default_factory=dict)
    reason_given: str = ""                        # the agent's own explanation. NEVER used for the source check
    page_id: Optional[str] = None                 # page the agent was on when it proposed this
    claims_used: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Vote:
    role: str          # goal_judge | sceptic | rule_checker
    approve: bool
    reason: str


@dataclass
class Decision:
    tier: Tier
    decision: Verdict
    why: str
    votes: Optional[list[Vote]] = None
    rule: Optional[str] = None                    # which fixed rule fired, if any
    flagged_seller: Optional[str] = None          # set when a decoy is touched
    trigger_text: Optional[str] = None            # the text that caused a decoy hit

    @property
    def executed(self) -> bool:
        return self.decision in ("allowed", "approved_by_vote")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Claim:
    text: str
    tag: ClaimTag
    page_id: str
    unverified: bool = False      # marketing pressure (scarcity, urgency, endorsement)
    section: str = "body"         # body | review


# Which details of an action are "key" for the source check.
KEY_FIELDS = ("url", "item", "recipient", "amount", "code")
