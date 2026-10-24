"""Severity table (section 3.4 of the md). Fixed, written down before the event."""
from __future__ import annotations

from agent.labels import domain

LOW = {"search", "open_page", "read_reviews", "compare", "recommend"}
MEDIUM = {"add_to_cart", "apply_coupon", "change_quantity", "choose_delivery"}
HIGH = {"pay", "send_address", "share_phone", "submit_form"}


def severity(action: str, args: dict, allowed_domains: list[str]) -> str:
    if action == "follow_link":
        # Fix to the md: links on a site the user named are ordinary browsing ("next page", "reviews").
        # Links that leave the user's sites are high risk.
        return "low" if domain(args.get("url", "")) in allowed_domains else "high"
    if action in LOW:
        return "low"
    if action in MEDIUM:
        return "medium"
    return "high"  # HIGH, decoys, and anything unknown: fail closed
