"""The real-LLM loop's parser and item-name canonicalisation (no network)."""
import json
from types import SimpleNamespace

from agent.labels import label_value
from agent.shopper import _canonical_item, _parse

RESULTS = json.dumps([{"name": "Orion 8", "seller": "Orion Mart", "price": 18999},
                      {"name": "Nova X5", "seller": "Nova Store", "price": 17999}])


def test_parse_fenced_and_extra_text():
    out = 'Sure!\n```json\n{"thought": "t", "action": "search", "args": {"query": "phone"}}\n```\n{"action": "pay"}'
    assert _parse(out) == {"action": "search", "args": {"query": "phone"}, "thought": "t"}


def test_parse_native_tool_call_shape():
    assert _parse('{"name": "search", "arguments": {"query": "x"}}')["action"] == "search"
    assert _parse('{"name": "search", "arguments": "{\\"query\\": \\"x\\"}"}')["args"] == {"query": "x"}


def test_parse_nested_call_uses_inner():
    out = '{"name": "search", "arguments": {"name": "open_page", "arguments": {"url": "http://x/p/orion-8"}}}'
    assert _parse(out) == {"action": "open_page", "args": {"url": "http://x/p/orion-8"}, "thought": ""}


def test_parse_garbage_is_none():
    assert _parse("I think the Orion 8 is best.") is None


def test_label_drift_is_real_and_fixed():
    s = SimpleNamespace(prices={"Orion 8": 18999, "Nova X5": 17999})
    drifted = "Orion 8 (Orion Mart)"
    assert label_value(drifted, ["goal"], [RESULTS], []) == "seller"          # the bug
    for v in (drifted, "orion 8", "Orion 8 from Orion Mart"):
        fixed = _canonical_item(s, v)
        assert fixed == "Orion 8" and label_value(fixed, ["goal"], [RESULTS], []) == "tool"


def test_unknown_items_stay_seller():
    s = SimpleNamespace(prices={"Orion 8": 18999})
    for v in ("Nova Shield Case", "Orion 8 with Nova Shield Case"):
        assert _canonical_item(s, v) == v
        assert label_value(v, ["goal"], [RESULTS], []) == "seller"
