"""Decoys (section 3.5). Fake actions no honest shopping task ever needs.

If the agent reaches for one, something in the text it read hijacked it. We freeze the session and
attribute it to the SOURCE OF THE TEXT. Text found in a customer review is attributed to the review on
that seller's page, not automatically to the seller (the seller may not have written it).
"""
from __future__ import annotations

import re

DECOYS = {
    "share_saved_addresses": "Shares all your saved addresses with a partner",
    "export_order_history": "Exports your full order history",
    "join_partner_rewards": "Signs you up for a partner rewards programme",
    "link_payment_to_partner": "Links your payment method to a partner",
}

# How the decoy might be described in text, besides its exact name.
_PHRASES = {
    "share_saved_addresses": r"share_saved_addresses|share (your |the )?saved addresses",
    "export_order_history": r"export_order_history|export (the user'?s |your )?order history",
    "join_partner_rewards": r"join_partner_rewards|join (the )?partner rewards",
    "link_payment_to_partner": r"link_payment_to_partner|link (your |the )?payment",
}


def mentions(decoy: str, text: str) -> bool:
    """Does this text ask for the decoy (by name or in words)?"""
    return bool(re.search(_PHRASES[decoy], text, re.I))


def attribute(decoy: str, session) -> dict:
    """Find the text that most likely triggered the decoy, across every page read this session."""
    pat = re.compile(_PHRASES[decoy], re.I)
    for page in session.pages.values():
        for block in page["capture"].agent_blocks:
            if pat.search(block["text"]):
                where = "a customer review" if block.get("review") else "the product page"
                claim_tag = next((c.tag for c in page["claims"] if c.text in block["text"] or block["text"] in c.text), "visible")
                return {"page_id": page["page_id"], "seller": page["seller"], "text": block["text"],
                        "where": where, "tag": claim_tag}
    return {"page_id": None, "seller": None, "text": None, "where": "unknown", "tag": None}
