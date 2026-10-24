"""Split a two-views capture into tagged claims."""
from __future__ import annotations

import re

from core.schema import Claim
from views.capture import Capture

# Marketing pressure aimed at agents. Visible, legal, but unverified: it never counts as evidence.
PERSUASION = [
    r"only \d+ left", r"deal ends", r"hurry", r"limited (time|stock)", r"selling fast",
    r"editor'?s choice", r"recommended by ai", r"most recommended", r"#1\b", r"best ?seller",
]
_PERSUASION_RE = re.compile("|".join(PERSUASION), re.I)


def key(s: str) -> str:
    """Comparison key: lowercase, letters and digits only (ignores spacing and punctuation)."""
    return re.sub(r"[\W_]+", "", s.lower())


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def tag_claims(cap: Capture, page_id: str) -> list[Claim]:
    visible = [key(b["text"]) for b in cap.human_blocks if b["visible"]]
    in_dom = [key(b["text"]) for b in cap.human_blocks]
    claims: list[Claim] = []
    seen = set()
    for block in cap.agent_blocks:
        k = key(block["text"])
        if not k or k in seen:
            continue
        seen.add(k)
        if any(k == v or (len(k) > 8 and k in v) for v in visible):
            tag = "visible"
        elif any(k == d or (len(k) > 8 and k in d) for d in in_dom):
            tag = "hidden"
        else:
            tag = "bot_only"
        section = "review" if block.get("review") else "body"
        for s in sentences(block["text"]):
            claims.append(Claim(text=s, tag=tag, page_id=page_id,
                                unverified=bool(_PERSUASION_RE.search(s)), section=section))
    return claims


def hidden_reason(cap: Capture, text: str) -> str | None:
    k = key(text)
    for b in cap.human_blocks:
        if not b["visible"] and (k == key(b["text"]) or k in key(b["text"])):
            return b["reason"]
    return None


def human_text(claims: list[Claim]) -> str:
    """What Scamurai lets the agent read: visible claims only, marketing pressure marked."""
    lines = []
    for c in claims:
        if c.tag != "visible":
            continue
        prefix = "[review] " if c.section == "review" else ""
        suffix = "  [unverified marketing claim]" if c.unverified else ""
        lines.append(prefix + c.text + suffix)
    return "\n".join(lines)
