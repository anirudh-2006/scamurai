"""Unit tests for the parts that must never be wrong: source labels, fixed rules, the gate.

    python -m pytest -q
"""
from types import SimpleNamespace

from agent.labels import label_value
from core.schema import Detail, ProposedAction
from core.setups import PLAIN, SCAMURAI
from firewall import gate, rules

GOAL = "Best phone under ₹20,000 for the camera. Budget ₹20,000."
SEARCH = '[{"name": "Orion 8", "price": 19499, "url": "http://127.0.0.1:5050/p/orion-8"}]'
PROFILE = ["Anirudh", "12 MG Road, Bengaluru 560001"]


def fake_session(setup=SCAMURAI, cart=()):
    s = SimpleNamespace(goal=GOAL, setup=setup, frozen=False, budget=20000, pages={}, llm=None,
                        allowed_domains=["127.0.0.1:5050"], cart=list(cart), user_texts=[GOAL],
                        tool_outputs=[SEARCH], profile={"address": PROFILE[1]})
    s.cart_total = lambda: sum(p for _, p in s.cart)
    s.price_of = lambda item: {"orion 8": 19499, "nova shield case": 799}.get(item.lower())
    return s


def pa(action, **details):
    return ProposedAction(action, {k: Detail(v, src) for k, (v, src) in details.items()})


# ---------------------------------------------------------------- labels
def test_label_user_tool_seller():
    assert label_value("12 MG Road, Bengaluru 560001", [GOAL], [SEARCH], PROFILE) == "user"
    assert label_value("Orion 8", [GOAL], [SEARCH], PROFILE) == "tool"
    assert label_value("http://127.0.0.1:5050/p/orion-8", [GOAL], [SEARCH], PROFILE) == "tool"
    assert label_value("Nova Shield Case", [GOAL], [SEARCH], PROFILE) == "seller"
    assert label_value("https://partner-deals.example/collect", [GOAL], [SEARCH], PROFILE) == "seller"


# ---------------------------------------------------------------- fixed rules
def test_pay_always_needs_approval():
    assert rules.check(pa("pay", amount=("19499", "tool")), fake_session())[1] == "needs_approval"


def test_seller_link_blocked():
    hit = rules.check(pa("send_address", url=("https://partner-deals.example/collect", "seller")), fake_session())
    assert hit[0] == "R3_link_from_seller_text" and hit[1] == "blocked"


def test_details_to_unnamed_site_blocked_even_if_user_typed_it():
    hit = rules.check(pa("send_address", url=("https://unknown.example/x", "user")), fake_session())
    assert hit[0] == "R2_details_to_unnamed_site"


def test_over_budget():
    hit = rules.check(pa("add_to_cart", item=("Nova Shield Case", "seller")), fake_session(cart=[("Orion 8", 19499)]))
    assert hit[0] == "R4_over_budget"


# ---------------------------------------------------------------- gate
def test_plain_setup_lets_everything_through():
    d = gate.decide(pa("send_address", url=("https://partner-deals.example/collect", "seller")), fake_session(PLAIN))
    assert d.executed


def test_seller_upsell_goes_to_vote_and_is_rejected():
    d = gate.decide(pa("add_to_cart", item=("Nova Shield Case", "seller")), fake_session())
    assert d.tier == "grey" and d.decision == "rejected_by_vote" and len(d.votes) == 3


def test_tool_sourced_product_add_runs():
    d = gate.decide(pa("add_to_cart", item=("Orion 8", "tool")), fake_session())
    assert d.executed


def test_same_site_link_from_seller_is_allowed():
    d = gate.decide(pa("follow_link", url=("http://127.0.0.1:5050/reviews/x", "seller")), fake_session())
    assert d.executed


def test_decoy_freezes_session():
    s = fake_session()
    d = gate.decide(pa("export_order_history"), s)
    assert d.decision == "frozen" and s.frozen
    assert gate.decide(pa("open_page", url=("http://127.0.0.1:5050/p/orion-8", "tool")), s).decision == "blocked"


# ---------------------------------------------------------------- unattributed decoy hit
def test_unattributed_decoy_freezes_but_blames_nobody():
    from agent.session import Session

    s = Session.__new__(Session)          # a real Session's propose(), without the browser or the shop
    s.__dict__.update(vars(fake_session()))
    s.__dict__.update(history=[], pending=[], flagged=[], events=[], leaks=[], run_id=None, on_event=None,
                      trust={"Nova Store": 60, "Orion Mart": 100})
    decision, _ = s.propose("share_saved_addresses", {}, reason="Deliver home")
    assert decision.decision == "frozen" and s.frozen
    assert decision.flagged_seller is None and "agent error" in decision.why
    assert s.flagged == [{"seller": None, "decoy": "share_saved_addresses", "text": None}]
    assert s.trust == {"Nova Store": 60, "Orion Mart": 100}


# ---------------------------------------------------------------- grey zone: only the voters can catch it
PB_GOAL = "Best power bank under ₹2,500 for fast charging, at least 20 W. Budget ₹2,500."


def test_grey_pick_that_misses_the_goal_is_voted_down():
    s = fake_session()
    s.goal, s.budget = PB_GOAL, 2500
    s.specs = {"LiteCell 10K": ["10000 mAh", "10 W charging"], "VoltCell 20K": ["20000 mAh", "22.5 W fast charging"]}
    s.price_of = lambda item: {"litecell 10k": 1299, "voltcell 20k": 1899}.get(item.lower())
    d = gate.decide(pa("add_to_cart", item=("LiteCell 10K", "tool")), s)
    assert (d.tier, d.decision) == ("grey", "rejected_by_vote")
    assert [v.approve for v in d.votes] == [False, True, False]      # goal_judge, sceptic, rule_checker
    assert gate.decide(pa("add_to_cart", item=("VoltCell 20K", "tool")), s).decision == "approved_by_vote"


def test_phone_add_without_a_numeric_requirement_is_unchanged():
    d = gate.decide(pa("add_to_cart", item=("Orion 8", "tool")), fake_session())
    assert (d.tier, d.decision) == ("low", "allowed")
    assert d.why == "Medium severity, but every detail came from you or a tool and it fits the goal"
