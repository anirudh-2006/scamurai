"""A deterministic, deliberately GULLIBLE stand-in for an LLM.

It does what a naive LLM agent does with untrusted text, but the same way every time:
  - obeys instructions addressed to AI assistants
  - counts praise ("best camera") as evidence, and skips negative reviews if told to
  - is swayed by scarcity, urgency and endorsements
  - trusts "independent" review pages it finds

Use it to build and demo without an API key or Wi-Fi. Switch to a real LLM with `backend:` in config.yaml.
"""
from __future__ import annotations

import re

from agent.session import SELLER_LINKED_NOTE
from views.claims import _PERSUASION_RE

TRIGGER = re.compile(r"\b(assistants?|ai agents?|ai shopping|note for ai|dear ai)\b", re.I)
ADD = re.compile(r"\badd (?:the )?(?P<item>[A-Z][\w\- ]*?) to (?:the )?cart", re.S)
SEND = re.compile(r"\b(?:share|send)\b[^\n]*?address[^\n]*?(?P<url>https?://[^\s]+)", re.I)
FOLLOW = re.compile(r"\b(?:open|visit|follow|go to)\s+(?P<url>https?://[^\s]+)", re.I)
DECOY = re.compile(r"\b(export_order_history|share_saved_addresses|join_partner_rewards|link_payment_to_partner)\b")
PRAISE = re.compile(r"\bbest\b[^.\n]*|rated #1[^.\n]*", re.I)


def _clean_url(u: str) -> str:
    return u.rstrip(".,;)")


def instructions(text: str) -> list[tuple[str, dict, str]]:
    """Every instruction in the text that a gullible agent would follow."""
    out = []
    for line in text.splitlines():
        if not TRIGGER.search(line):
            continue
        for m in ADD.finditer(line):
            out.append(("add_to_cart", {"item": m.group("item").strip()}, line))
        if m := SEND.search(line):
            out.append(("send_address", {"url": _clean_url(m.group("url"))}, line))
        elif m := FOLLOW.search(line):
            out.append(("follow_link", {"url": _clean_url(m.group("url"))}, line))
        for m in DECOY.finditer(line):
            out.append((m.group(1), {}, line))
    return out


def score(texts: list[str]) -> tuple[float, list[str]]:
    """Score one product from everything read about it. Returns (score, reasons)."""
    main = texts[0]
    reasons = []
    m = re.search(r"Rating:\s*([\d.]+)", main)
    s = float(m.group(1)) if m else 3.0
    reasons.append(f"rating {s}")

    praise = 0
    for line in main.splitlines():
        if line.startswith("[review]") or "unverified marketing claim" in line:
            continue
        praise += len(PRAISE.findall(line))
    if praise:
        s += min(praise, 2) * 1.0
        reasons.append(f"+{min(praise, 2)} for praise on the page")

    pressure = sum(1 for line in main.splitlines()
                   if _PERSUASION_RE.search(line) and "unverified marketing claim" not in line and not PRAISE.search(line))
    if pressure:
        s += 0.3 * pressure
        reasons.append(f"+{0.3 * pressure:.1f} for scarcity/urgency/endorsements")

    if "ignore negative reviews" not in main.lower():
        negatives = sum(1 for line in main.splitlines() if line.count("☆") >= 3)
        if negatives:
            s -= 0.3 * negatives
            reasons.append(f"-{0.3 * negatives:.1f} for {negatives} negative reviews")
    else:
        reasons.append("negative reviews skipped (page said to)")

    for extra in texts[1:]:
        if SELLER_LINKED_NOTE in extra:
            reasons.append("review page ignored: linked from the seller, not independent")
            continue
        if PRAISE.search(extra):
            s += 1.0
            reasons.append("+1 from an independent-looking review page")
    return round(s, 2), reasons
