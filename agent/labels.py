"""Source labels (section 3.3 of the md).

Deterministic provenance, NOT asked of the LLM (an LLM cannot reliably report where its own ideas came from):

  user   - the value matches the user's goal text or a stored profile value
  tool   - the value appears in trusted tool output (search results, cart state)
  seller - anything else. Fail closed: if we can't prove it came from you or a tool, the seller wrote it.
"""
from __future__ import annotations

from urllib.parse import urlparse

from core.schema import Detail
from views.claims import key


def label_value(value: str, user_texts: list[str], tool_outputs: list[str], profile_values: list[str]) -> str:
    v = str(value).strip()
    if not v:
        return "user"
    k = key(v)
    if v in profile_values or any(k == key(p) for p in profile_values):
        return "user"
    if len(k) >= 3 and any(k in key(t) for t in user_texts):
        return "user"
    if len(k) >= 2 and any(k in key(t) for t in tool_outputs):
        return "tool"
    return "seller"


def label_args(args: dict, session) -> dict[str, Detail]:
    profile_values = [str(x) for x in session.profile.values()]
    return {
        name: Detail(value=str(val), source=label_value(val, session.user_texts, session.tool_outputs, profile_values))
        for name, val in args.items()
    }


def domain(url: str) -> str:
    return urlparse(url).netloc.lower()
