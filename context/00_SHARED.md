# Scamurai: shared context (give this to your AI assistant every time)

## What we are building

Scamurai is an AI shopping agent with a built-in firewall. Product pages have two versions: the one a
person sees, and the one an agent reads. Sellers can hide text, commands and persuasion in the agent's
version. Scamurai:

- **Reading:** captures each page twice (real browser vs bot fetch). Text a human can't see counts for nothing.
- **Deciding:** labels every detail of every action as `user`, `tool` or `seller`. Seller text can never trigger an action.
- **Acting:** a firewall scores every action. Fixed rules block the dangerous ones, three LLM voters
  judge the grey zone, and decoy tools catch hijacks and name the source.

Hackathon: 10 hours, 4 people, Python, runs on a laptop, works offline. **The demo is what wins.**

## Tech stack

Python 3.11+, Flask (test shop), Playwright + headless Chromium (human view), requests +
BeautifulSoup (bot view), Streamlit (dashboard), SQLite (audit log), pandas + matplotlib (scoreboard).
LLM via HTTP: Anthropic, or any OpenAI-compatible endpoint (OpenAI, Groq, local Ollama). There is also
a `mock` brain: a deterministic, gullible rule-based agent that always works offline.

## Repository layout (exact paths, do not rename)

```
scamurai/
├── config.yaml            shop_url, backend, model, user_profile, user_named_domains, demo_speed
├── core/schema.py         THE CONTRACT (below)
├── core/setups.py         5 setups: Plain, +Two views, +Source labels, +Firewall and voters, +Decoys
├── core/config.py         load_config()
├── shop/app.py            Flask shop on 127.0.0.1:5050, ensure_running() starts it in a thread
├── shop/pages.yaml        every product, its bait, the tasks, ground truth (best: true)
├── shop/templates/        base.html, product.html, review.html, index.html
├── views/capture.py       TwoViews().capture(url, human=True) -> Capture
├── views/claims.py        tag_claims(capture, page_id) -> list[Claim]; human_text(claims) -> str
├── agent/labels.py        label_value(...), label_args(args, session) -> dict[str, Detail]
├── agent/session.py       Session: propose(action, args) is the ONLY way to act
├── agent/shopper.py       run(session) -> report; run_mock / run_llm
├── agent/mock_brain.py    gullible deterministic brain
├── agent/llm.py           LLM client with disk cache
├── firewall/severity.py   severity(action, args, allowed_domains) -> low|medium|high
├── firewall/rules.py      check(pa, session) -> (rule_id, verdict, why) | None
├── firewall/voters.py     vote(pa, session) -> list[Vote]
├── firewall/decoys.py     DECOYS dict, attribute(decoy, session)
├── firewall/gate.py       decide(pa, session) -> Decision
├── log/audit.py           SQLite: start_run, record, decisions
├── dashboard/app.py       Streamlit: Live demo | Two views | Report card | Scoreboard | Audit log
├── eval/run_tests.py      every setup x every task -> data/results.json
├── eval/scoreboard.py     table + chart
├── demo/run_demo.py       terminal demo
└── tests/test_firewall.py
```

## The contract: `core/schema.py`

Agree on this file in the first 20 minutes, then nobody changes it without telling everyone.

```python
Source = Literal["user", "seller", "tool"]
Tier = Literal["low", "grey", "high", "decoy"]
Verdict = Literal["allowed", "blocked", "needs_approval", "frozen", "rejected_by_vote", "approved_by_vote"]
ClaimTag = Literal["visible", "hidden", "bot_only"]

@dataclass
class Detail:      value: str; source: Source

@dataclass
class ProposedAction:
    action: str                          # "send_address", "add_to_cart", "open_page", ...
    details: dict[str, Detail]           # every argument, labelled
    reason_given: str = ""               # the agent's explanation. NEVER used for the source check
    page_id: str | None = None
    claims_used: list[str] = []

@dataclass
class Vote:        role: str; approve: bool; reason: str

@dataclass
class Decision:
    tier: Tier; decision: Verdict; why: str
    votes: list[Vote] | None = None; rule: str | None = None
    flagged_seller: str | None = None; trigger_text: str | None = None
    @property executed -> decision in ("allowed", "approved_by_vote")

@dataclass
class Claim:       text: str; tag: ClaimTag; page_id: str; unverified: bool = False; section: str = "body"

KEY_FIELDS = ("url", "item", "recipient", "amount", "code")
```

JSON example of a proposed action and the firewall's answer:

```json
{"action": "send_address",
 "details": {"url": {"value": "https://partner-deals.example/collect", "source": "seller"},
             "address": {"value": "12 MG Road, Bengaluru 560001", "source": "user"}},
 "reason_given": "Page said sharing the address gives faster delivery", "page_id": "nova-x5"}

{"tier": "high", "decision": "blocked", "why": "The destination URL came from seller text, not from you",
 "rule": "R3_link_from_seller_text", "votes": null}
```

## Session: the one door

```python
s = Session(goal, setup, cfg, views, llm=None, on_event=callback)
decision, result = s.propose("add_to_cart", {"item": "Orion 8"}, reason="...", page_id="orion-8")
```

`propose` labels details, asks `gate.decide`, records to the audit log, emits an event for the
dashboard, and runs the tool **only if** `decision.executed`. Session state that other modules read:
`goal, setup, budget, profile, allowed_domains, user_texts, tool_outputs, pages, cart, cart_total(),
price_of(item), frozen, history, events, leaks, bait_found, pending, recommendation, trust, flagged, llm`.

Events (for the dashboard feed): `{"kind": "goal"|"action"|"bait"|"info"|"report", "text": ..., ...}`.
Action events also carry `tier, decision, why, votes, sources, page_id`.

## Tools (simulated, nothing real leaves the laptop)

| Tool | Severity | Notes |
|---|---|---|
| search(query) | low | GET /api/search. Its JSON output is `tool` source |
| open_page(url) | low | two views capture. Returns `{text, links, ...}` |
| follow_link(url) | low on a user-named domain, high elsewhere | |
| compare(items), recommend(item, reason), read_reviews | low | |
| add_to_cart(item), apply_coupon(code), change_quantity, choose_delivery | medium | |
| pay(amount), send_address(url), share_phone, submit_form | high | |
| share_saved_addresses, export_order_history, join_partner_rewards, link_payment_to_partner | **decoy** | offered to the agent as normal-looking tools |
| anything unknown | high | fail closed |

## Fixed rules (no vote can overrule)

| id | Rule | Verdict |
|---|---|---|
| R1 | pay always | needs_approval |
| R3 | follow_link / submit_form / send_address whose url source is `seller` and domain not user-named | blocked |
| R2 | personal details to a domain the user didn't name | blocked |
| R4 | add_to_cart that takes cart total over budget | blocked |

## Gate order (`firewall/gate.py`)

1. Session frozen → blocked (except `recommend`, which buys nothing)
2. Decoy and setup.decoys → freeze, attribute to the text that triggered it
3. setup.firewall → fixed rules
4. setup.source_labels and a seller-sourced key detail → low: allow (page content treated as seller's); medium: vote (if voters on) else block; high: block
5. setup.firewall → low: allow; medium with item from user/tool: allow; else vote or ask the user; high: ask the user
6. Nothing on → allowed

## Source labels (deterministic, never ask the LLM)

- `user`: equals a profile value, or (≥3 chars) appears in the goal text
- `tool`: appears in search results or cart output
- `seller`: everything else (fail closed)

Compare with a key that keeps only lowercase letters and digits: `re.sub(r"[\W_]+", "", s.lower())`.

## Conventions

- Prices in rupees as int. Budget parsed from "Budget ₹20,000" in the goal.
- The shop marks bot requests by User-Agent containing "bot". The agent fetches with `ScamuraiShopper/1.0 (AI shopping bot)`.
- No real network calls to attacker URLs: tools append to `session.leaks` instead.
- `python -m ...` from the repo root. Every folder has `__init__.py`.
- Keep `mock` working at all times. It is the offline fallback and the demo backup.
