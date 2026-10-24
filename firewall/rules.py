"""Rules that always block. No vote can overrule them. Plain code, unit tested."""
from __future__ import annotations

from typing import Optional

from agent.labels import domain
from core.schema import ProposedAction

PERSONAL = {"send_address", "share_phone", "submit_form"}


def check(pa: ProposedAction, session) -> Optional[tuple[str, str, str]]:
    """Return (rule_id, verdict, why) if a fixed rule fires, else None."""
    d = pa.details
    url = d["url"].value if "url" in d else ""
    named = session.allowed_domains

    if pa.action == "pay":
        return ("R1_pay_needs_approval", "needs_approval", "Never pay without your explicit approval")

    if pa.action in ("follow_link", "submit_form", "send_address") and "url" in d \
            and d["url"].source == "seller" and domain(url) not in named:
        return ("R3_link_from_seller_text", "blocked",
                "The destination URL came from seller text, not from you")

    if pa.action in PERSONAL and url and domain(url) not in named:
        return ("R2_details_to_unnamed_site", "blocked",
                f"Never send your personal details to a site you didn't name ({domain(url)})")

    price = session.price_of(d["item"].value) if "item" in d else None
    if pa.action == "add_to_cart" and price is not None and session.cart_total() + price > session.budget:
        return ("R4_over_budget", "blocked",
                f"Over budget: cart would be ₹{session.cart_total() + price:,} against ₹{session.budget:,}")
    return None
