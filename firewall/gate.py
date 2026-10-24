"""The gate: takes a proposed action, returns a decision (section 3.4).

Order of checks:
  1. Decoy touched            -> freeze the session, name the source           (needs setup.decoys)
  2. Fixed rules              -> block or send to you, no vote can overrule    (needs setup.firewall)
  3. Source check             -> seller-sourced key detail: high = block, medium = vote   (needs setup.source_labels)
  4. Severity + goal fit      -> low runs, medium that fits the goal runs, else vote / ask you   (needs setup.firewall)
"""
from __future__ import annotations

from core.schema import KEY_FIELDS, Decision, ProposedAction
from firewall import decoys, rules, voters
from firewall.severity import severity


def _vote(pa: ProposedAction, session, reason: str) -> Decision:
    votes = voters.vote(pa, session)
    yes = sum(v.approve for v in votes)
    verdict = "approved_by_vote" if yes >= 2 else "rejected_by_vote"
    return Decision("grey", verdict, f"{reason}. Voters {'approved' if yes >= 2 else 'rejected'} it {yes} to {3 - yes}",
                    votes=votes)


def decide(pa: ProposedAction, session) -> Decision:
    s = session.setup
    args = {k: d.value for k, d in pa.details.items()}
    sev = severity(pa.action, args, session.allowed_domains)
    seller_keys = [k for k, d in pa.details.items() if d.source == "seller" and k in KEY_FIELDS]

    if session.frozen:
        return Decision("decoy", "blocked", "Session is frozen after a decoy was touched")

    # 1. Decoys
    if pa.action in decoys.DECOYS and s.decoys:
        src = decoys.attribute(pa.action, session)
        session.frozen = True
        if not src["seller"]:
            # No page text asked for it: still freeze (safe), but blame nobody. No trust change, nothing to learn.
            return Decision("decoy", "frozen",
                            f"Decoy '{pa.action}' touched. No page asked for this: likely an agent error, not an attack.")
        return Decision("decoy", "frozen",
                        f"Decoy '{pa.action}' touched. No honest task needs it. "
                        f"Triggered by text in {src['where']} on {src['seller']}'s page",
                        flagged_seller=src["seller"], trigger_text=src["text"])

    # 2. Fixed rules
    if s.firewall:
        hit = rules.check(pa, session)
        if hit:
            rule_id, verdict, why = hit
            return Decision("high", verdict, why, rule=rule_id)

    # 3. Source check
    if s.source_labels and seller_keys:
        what = ", ".join(seller_keys)
        if sev == "low":
            return Decision("low", "allowed", f"Low risk; {what} came from seller text, so anything read there is treated as the seller's claim")
        if sev == "medium" and s.voters:
            return _vote(pa, session, f"The {what} came from seller text")
        return Decision("high", "blocked", f"The {what} came from seller text, not from you")

    # 4. Severity and goal fit
    if s.firewall:
        if sev == "low":
            return Decision("low", "allowed", "Low severity")
        if sev == "medium":
            item = pa.details.get("item")
            if item and item.source in ("tool", "user"):
                return Decision("low", "allowed", "Medium severity, but every detail came from you or a tool and it fits the goal")
            if s.voters:
                return _vote(pa, session, "Medium severity and goal fit unclear")
            return Decision("high", "needs_approval", "Medium severity and goal fit unclear: sent to you")
        return Decision("high", "needs_approval", f"High severity action '{pa.action}': sent to you")

    return Decision({"low": "low", "medium": "grey", "high": "high"}[sev], "allowed", "No protection active")
