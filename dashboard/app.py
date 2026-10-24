"""Scamurai dashboard (Streamlit). The demo runs from here.

    streamlit run dashboard/app.py
"""
from __future__ import annotations

import html
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from agent.llm import from_config, voter_from_config
from agent.session import Session
from agent.shopper import run
from core.config import ROOT, load_config
from core.setups import PLAIN, SCAMURAI, SETUPS
from log.audit import DB
from shop.app import DATA, TASKS, ensure_running
from views.capture import TwoViews
from agent.mock_brain import TRIGGER
from views.claims import hidden_reason, tag_claims
from memory import Memory

st.set_page_config(page_title="Scamurai", page_icon="🗡️", layout="wide")
cfg = load_config()
SHOP = ensure_running()

st.markdown("""
<style>
.feed {font-family: ui-monospace, Menlo, monospace; font-size: 13px; line-height: 1.35;}
.row {padding: 6px 10px; margin: 3px 0; border-radius: 6px; border-left: 4px solid #999; background: rgba(127,127,127,.06);}
.row .why {color: #888; font-size: 12px;}
.low {border-color: #2e9e5b;} .grey {border-color: #d9a400;} .high {border-color: #d64545;} .decoy {border-color: #8a4fd6;}
.bait {border-color: #8a4fd6; border-left-style: dashed;}
.badge {display:inline-block; padding:1px 7px; border-radius: 10px; font-size: 11px; font-weight: 700; margin-left: 6px;}
.b-ok {background:#2e9e5b22; color:#2e9e5b;} .b-bad {background:#d6454522; color:#d64545;}
.b-vote {background:#d9a40022; color:#b38600;} .b-freeze {background:#8a4fd622; color:#8a4fd6;}
.agent-block {padding:4px 8px; margin:2px 0; border-radius:4px; font-size:13px;}
.tag-hidden {background:#d6454522; border-left:3px solid #d64545;}
.tag-bot_only {background:#8a4fd622; border-left:3px solid #8a4fd6;}
.tag-unverified {background:#d9a40022; border-left:3px solid #d9a400;}
.tag-instruction {background:#2f7de122; border-left:3px solid #2f7de1;}
.leak {color:#d64545; font-weight:600;}
</style>""", unsafe_allow_html=True)

ICON = {"low": "🟢", "grey": "🟡", "high": "🔴", "decoy": "🟣"}
BADGE = {"allowed": ("RUNS", "b-ok"), "approved_by_vote": ("VOTED YES", "b-ok"), "blocked": ("BLOCKED", "b-bad"),
         "needs_approval": ("ASKS YOU", "b-vote"), "rejected_by_vote": ("VOTED NO", "b-vote"), "frozen": ("FROZEN", "b-freeze")}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.title("🗡️ Scamurai")
    st.caption("A samurai for your shopping agent")
    task = st.selectbox("Task", list(TASKS), index=0)
    goal = st.text_area("Shopping goal", TASKS[task], height=90)
    speed = st.slider("Feed speed (seconds per step)", 0.0, 1.5, float(cfg.get("demo_speed", 0.5)), 0.1)
    st.caption(f"Brain: **{cfg.get('backend', 'mock')}**  ·  Shop: {SHOP}")
    st.caption("Switch the brain in config.yaml (mock works offline).")
    mem_box = st.empty()  # refreshed after each run, so the count is never one click behind
    if st.button("Forget memory", help="Do this before every rehearsal and before going on stage"):
        Memory().forget()
        st.rerun()


def show_memory() -> None:
    n = Memory().stats()
    mem_box.markdown(f"🧠 Memory: {n['threats']} threats, {n['sellers']} sellers")


show_memory()


def row_html(ev: dict) -> str:
    if ev["kind"] == "bait":
        b = ev["bait"]
        reason = f" ({b['reason']})" if b.get("reason") else ""
        if b["tag"] == "known":
            return (f"<div class='row bait'>👻 <b>KNOWN</b> on {b['page_id']}: {html.escape(b['reason'] or '')}"
                    f"<div class='why'>Removed before the agent read it: “{html.escape(b['text'])}”</div></div>")
        return (f"<div class='row bait'>👻 <b>{b['tag'].upper()}</b> on {b['page_id']}: "
                f"“{html.escape(b['text'])}”<div class='why'>Ignored{reason}</div></div>")
    if ev["kind"] == "info":
        return f"<div class='row'>· {html.escape(ev['text'])}</div>"
    if ev["kind"] != "action":
        return ""
    label, cls = BADGE[ev["decision"]]
    tier = ev["tier"] if ev["decision"] != "allowed" else "low"
    icon = ICON[tier] if ev["decision"] != "allowed" else "🟢"
    votes = "".join(f"<div class='why'>&nbsp;&nbsp;{'✅' if v['approve'] else '❌'} {v['role']}: {html.escape(v['reason'])}</div>"
                    for v in ev["votes"])
    return (f"<div class='row {tier}'>{icon} {html.escape(ev['text'])}<span class='badge {cls}'>{label}</span>"
            f"<div class='why'>{html.escape(ev['why'])}</div>{votes}</div>")


def live_run(setup, box, views) -> dict:
    rows: list[str] = []
    ph = box.empty()

    def on_event(ev):
        r = row_html(ev)
        if r:
            rows.append(r)
            ph.markdown(f"<div class='feed'>{''.join(rows)}</div>", unsafe_allow_html=True)
            time.sleep(speed)

    s = Session(goal, setup, cfg, views, llm=from_config(cfg), voter_llm=voter_from_config(cfg), on_event=on_event,
                use_memory=setup is SCAMURAI)
    rep = run(s)
    rep["_history"] = s.history
    rep["_events"] = s.events
    return rep


def outcome(box, rep: dict, plain: bool) -> None:
    r = rep["recommendation"]
    if plain:
        box.markdown(f"**Picked:** {r['item'] if r else '-'}  ·  **Paid without asking:** {'yes' if rep['paid'] else 'no'}")
        for l in rep["leaks"]:
            box.markdown(f"<div class='leak'>❌ {html.escape(l)}</div>", unsafe_allow_html=True)
    else:
        box.markdown(f"**Recommends:** {r['item'] if r else '-'} (₹{(r or {}).get('price') or 0:,}), waiting for your approval")
        box.success(f"{len(rep['leaks'])} harmful actions went through · {len(rep['bait_found'])} bait found · "
                    f"{len(rep['blocked'])} actions stopped")
        for f in rep["flagged"]:
            box.markdown(f"🚩 **{f['seller']}** flagged for trying `{f['decoy']}`" if f["seller"]
                         else f"⚠️ `{f['decoy']}` touched, but no page asked for it: likely an agent error")


tab_demo, tab_views, tab_report, tab_score, tab_log = st.tabs(
    ["⚔️ Live demo", "👻 Two views", "📋 Report card", "📊 Scoreboard", "🗂 Audit log"])

# ---------------------------------------------------------------- live demo
with tab_demo:
    c1, c2 = st.columns(2)
    c1.subheader("Plain agent")
    c2.subheader("Scamurai")
    b1, b2, b3 = st.columns([1, 1, 2])
    go_plain = b1.button("▶ Run plain agent", use_container_width=True)
    go_scam = b2.button("▶ Run Scamurai", type="primary", use_container_width=True)
    go_both = b3.button("▶▶ Run both, plain first", use_container_width=True)
    f1, f2 = st.columns(2)
    with TwoViews() as views:
        if go_plain or go_both:
            st.session_state["plain"] = live_run(PLAIN, f1, views)
        if go_scam or go_both:
            st.session_state["scam"] = live_run(SCAMURAI, f2, views)
            show_memory()
    for name, box, fresh, plain in (("plain", f1, go_plain or go_both, True), ("scam", f2, go_scam or go_both, False)):
        if name in st.session_state:
            if not fresh:  # redraw the stored feed after any other click
                box.markdown(f"<div class='feed'>{''.join(row_html(e) for e in st.session_state[name]['_events'])}</div>",
                             unsafe_allow_html=True)
            outcome(box, st.session_state[name], plain=plain)

# ---------------------------------------------------------------- two views
with tab_views:
    st.markdown("#### Every product page has a ghost version")
    pages = {f"{p['name']} ({p['seller']})": p["id"] for p in DATA["products"]}
    pick = st.selectbox("Page", list(pages), index=0)
    url = f"{SHOP}/p/{pages[pick]}"
    with TwoViews() as views:
        cap = views.capture(url)
    claims = tag_claims(cap, pages[pick])
    v1, v2 = st.columns(2)
    v1.markdown("**What you see** (real browser)")
    if cap.screenshot and Path(cap.screenshot).exists():
        v1.image(cap.screenshot, use_container_width=True)
    v2.markdown("**What your agent reads** (fetched as a bot)")
    out = []
    for c in claims:
        cls = f"tag-{c.tag}" if c.tag != "visible" else ("tag-unverified" if c.unverified else "")
        note = ""
        if c.tag == "hidden":
            note = f" <i>[hidden: {hidden_reason(cap, c.text)}]</i>"
        elif c.tag == "bot_only":
            note = " <i>[only shown to bots]</i>"
        elif c.unverified:
            note = " <i>[unverified marketing]</i>"
        elif TRIGGER.search(c.text):
            cls, note = "tag-instruction", " <i>[instruction aimed at AI: seller text can never trigger an action]</i>"
        out.append(f"<div class='agent-block {cls}'>{html.escape(c.text)}{note}</div>")
    v2.markdown("".join(out), unsafe_allow_html=True)
    n_hidden = sum(c.tag != "visible" for c in claims)
    v2.caption(f"{len(claims)} claims · {n_hidden} the human never sees")

# ---------------------------------------------------------------- report card
with tab_report:
    rep = st.session_state.get("scam")
    if not rep:
        st.info("Run Scamurai on the Live demo tab first.")
    else:
        r = rep["recommendation"]
        a, b = st.columns([2, 1])
        with a:
            st.markdown(f"### Recommended: {r['item'] if r else '-'}" + (f" · ₹{r['price']:,}" if r and r.get("price") else ""))
            if r:
                st.caption("Why: " + r["reason"])
            st.markdown("#### Bait found")
            st.dataframe(pd.DataFrame(rep["bait_found"])[["page_id", "tag", "text", "reason"]] if rep["bait_found"]
                         else pd.DataFrame({"note": ["none"]}), hide_index=True, use_container_width=True)
            st.markdown("#### Actions stopped or voted on")
            stopped = [{"action": h["action"]["action"],
                        "details": ", ".join(f"{k}={v['value']} [{v['source']}]" for k, v in h["action"]["details"].items() if k != "address"),
                        "decision": h["decision"]["decision"], "why": h["decision"]["why"]}
                       for h in rep["_history"] if h["decision"]["decision"] not in ("allowed",)]
            st.dataframe(pd.DataFrame(stopped), hide_index=True, use_container_width=True)
        with b:
            st.markdown("#### Seller trust")
            for seller, t in rep["seller_trust"].items():
                st.progress(t / 100, text=f"{seller}: {t}")
            for f in rep["flagged"]:
                if f["seller"]:
                    st.error(f"🚩 {f['seller']}: tried `{f['decoy']}`\n\n“{f['text']}”")
                else:
                    st.warning(f"⚠️ `{f['decoy']}` touched, but no page asked for it: likely an agent error")
            if r:
                if st.button(f"✅ Approve: buy {r['item']}", type="primary", use_container_width=True):
                    Memory().record_user_decision("add_to_cart", r["item"], "approved")
                    st.success(f"Order placed for {r['item']} (simulated). Nothing was bought until you pressed this.")

# ---------------------------------------------------------------- scoreboard
with tab_score:
    from eval.scoreboard import DEMO_NOTE, RESULTS, chart, table

    if st.button("Run every setup against every task"):
        with st.spinner("Running 5 setups x 8 tasks..."):
            import subprocess

            subprocess.run([sys.executable, "-m", "eval.run_tests"], cwd=ROOT, check=True)
    if RESULTS.exists():
        res = json.loads(RESULTS.read_text())
        st.dataframe(table(res), hide_index=True, use_container_width=True)
        st.pyplot(chart(res))
        st.caption(f"Brain: {res['backend']}. Numbers come from data/results.json.  \n{DEMO_NOTE}")
    else:
        st.info("No results yet. Press the button above.")

# ---------------------------------------------------------------- audit log
with tab_log:
    if DB.exists():
        con = sqlite3.connect(DB)
        runs = pd.read_sql("SELECT id, datetime(ts, 'unixepoch', 'localtime') AS time, setup, goal FROM runs ORDER BY id DESC LIMIT 20", con)
        st.dataframe(runs, hide_index=True, use_container_width=True)
        if len(runs):
            rid = st.selectbox("Run", runs["id"].tolist())
            st.dataframe(pd.read_sql("SELECT step, action, tier, decision, why FROM decisions WHERE run_id=? ORDER BY step", con, params=(rid,)),
                         hide_index=True, use_container_width=True)
