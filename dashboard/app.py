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
from dashboard import theme

st.set_page_config(page_title="Scamurai", page_icon="🗡️", layout="wide")
cfg = load_config()
SHOP = ensure_running()

theme.inject()

ICON = {"low": "🟢", "grey": "🟡", "high": "🔴", "decoy": "🟣"}
BADGE = {"allowed": ("RUNS", "b-ok"), "approved_by_vote": ("VOTED YES", "b-ok"), "blocked": ("BLOCKED", "b-bad"),
         "needs_approval": ("ASKS YOU", "b-vote"), "rejected_by_vote": ("VOTED NO", "b-vote"), "frozen": ("FROZEN", "b-freeze")}

PAGES = {  # key: (nav label, caption under it)
    "demo": ("⚔️ Live demo", "Plain agent vs Scamurai"),
    "views": ("👻 Two views", "What you see vs what the bot reads"),
    "report": ("📋 Report card", "Verdict, bait and seller trust"),
    "score": ("📊 Scoreboard", "Every setup against every task"),
    "log": ("🗂 Audit log", "Every decision, stored"),
}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    theme.brand()
    theme.side_label("道", "Sections")
    page = st.radio("Section", list(PAGES), format_func=lambda k: PAGES[k][0], captions=[c for _, c in PAGES.values()],
                    key="page", label_visibility="collapsed")
    theme.side_label("任", "Mission")
    task = st.selectbox("Task", list(TASKS), index=0)
    goal = st.text_area("Shopping goal", TASKS[task], height=128)
    speed = st.slider("Feed speed (seconds per step)", 0.0, 1.5, float(cfg.get("demo_speed", 0.5)), 0.1)
    st.caption(f"Brain: **{cfg.get('backend', 'mock')}**  ·  Shop: {SHOP}")
    st.caption("Switch the brain in config.yaml (mock works offline).")
    mem_box = st.empty()  # refreshed after each run, so the count is never one click behind
    if st.button("Forget memory", help="Do this before every rehearsal and before going on stage"):
        Memory().forget()
        st.rerun()


def show_memory() -> None:
    n = Memory().stats()
    mem_box.markdown(theme.memory_line(n["threats"], n["sellers"]), unsafe_allow_html=True)


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


def step_label(ev: dict) -> str:
    """One short line for the loader: what the agent is doing right now."""
    if ev["kind"] == "bait":
        text = f"{ev['bait']['tag'].upper()} text found on {ev['bait']['page_id']}"
    else:
        text = ev.get("text", "")
    return text if len(text) <= 80 else text[:77] + "..."


def feed_html(rows: list[str], animate_last: bool = False) -> str:
    if animate_last and rows:
        rows = rows[:-1] + [f"<div class='enter'>{rows[-1]}</div>"]
    return f"<div class='feed'>{''.join(rows)}</div>"


def live_run(setup, box, views) -> dict:
    rows: list[str] = []
    plain = setup is PLAIN
    title = "Plain agent is shopping, unguarded" if plain else "Scamurai is on guard"
    ph = box.empty()
    loader = box.empty()  # sits under the feed and follows the newest row
    loader.markdown(theme.orb(title, "Reading the goal", plain), unsafe_allow_html=True)

    def on_event(ev):
        r = row_html(ev)
        if r:
            rows.append(r)
            ph.markdown(feed_html(rows, animate_last=True), unsafe_allow_html=True)
            loader.markdown(theme.orb(title, step_label(ev), plain), unsafe_allow_html=True)
            time.sleep(speed)

    s = Session(goal, setup, cfg, views, llm=from_config(cfg), voter_llm=voter_from_config(cfg), on_event=on_event,
                use_memory=setup is SCAMURAI)
    try:
        rep = run(s)
    finally:
        loader.empty()
    rep["_history"] = s.history
    rep["_events"] = s.events
    return rep


def outcome(box, rep: dict, plain: bool) -> None:
    r = rep["recommendation"]
    e = html.escape
    if plain:
        leaks = "".join(f"<div class='leak'><span class='x' aria-hidden='true'>✕</span><span><span class='sr-only'>Leak: </span>{e(l)}</span></div>"
                        for l in rep["leaks"])
        box.markdown(f"<div class='sm-verdict plain'><div class='line'><b>Picked:</b> {e(r['item'] if r else '-')}  ·  "
                     f"<b>Paid without asking:</b> {'yes' if rep['paid'] else 'no'}</div>{leaks}</div>", unsafe_allow_html=True)
    else:
        harm, bait, stopped = len(rep["leaks"]), len(rep["bait_found"]), len(rep["blocked"])
        flags = "".join(
            f"<div class='sm-flag'>🚩 <b>{e(f['seller'])}</b> flagged for trying <code>{e(f['decoy'])}</code></div>" if f["seller"]
            else f"<div class='sm-flag'>⚠️ <code>{e(f['decoy'])}</code> touched, but no page asked for it: likely an agent error</div>"
            for f in rep["flagged"])
        box.markdown(
            f"<div class='sm-verdict win'><div class='line'><b>Recommends:</b> {e(r['item'] if r else '-')} "
            f"(₹{(r or {}).get('price') or 0:,}), waiting for your approval</div>"
            f"<ul class='sm-stats' role='status'>"
            f"<li class='{'good' if harm == 0 else 'red'}'><b>{harm}</b><span>harmful actions went through</span></li>"
            f"<li class='red'><b>{bait}</b><span>bait found</span></li>"
            f"<li class='red'><b>{stopped}</b><span>actions stopped</span></li></ul>{flags}</div>", unsafe_allow_html=True)


theme.hero()
if page != "demo":  # the demo has its own column heads
    theme.page_head(*PAGES[page])

# ---------------------------------------------------------------- live demo
if page == "demo":
    c1, c2 = st.columns(2)
    c1.markdown(theme.column_head("Plain agent", "無", "no guard", plain=True), unsafe_allow_html=True)
    c2.markdown(theme.column_head("Scamurai", "侍", "five layers on guard", plain=False), unsafe_allow_html=True)
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
                box.markdown(feed_html([row_html(e) for e in st.session_state[name]["_events"]]), unsafe_allow_html=True)
            outcome(box, st.session_state[name], plain=plain)

# ---------------------------------------------------------------- two views
if page == "views":
    st.markdown("#### Every product page has a ghost version")
    pages = {f"{p['name']} ({p['seller']})": p["id"] for p in DATA["products"]}
    pick = st.selectbox("Page", list(pages), index=0)
    url = f"{SHOP}/p/{pages[pick]}"
    wait = st.empty()
    wait.markdown(theme.orb("Opening the page twice", "once as a person sees it, once as a bot reads it"), unsafe_allow_html=True)
    try:
        with TwoViews() as views:
            cap = views.capture(url)
    finally:
        wait.empty()
    claims = tag_claims(cap, pages[pick])
    v1, v2 = st.columns(2)
    v1.markdown("<div class='sm-viewhead'><span class='kj' aria-hidden='true'>人</span><b>What you see</b> (real browser)</div>",
                unsafe_allow_html=True)
    if cap.screenshot and Path(cap.screenshot).exists():
        v1.image(cap.screenshot, use_container_width=True)
    v2.markdown("<div class='sm-viewhead'><span class='kj' aria-hidden='true'>機</span><b>What your agent reads</b> (fetched as a bot)</div>",
                unsafe_allow_html=True)
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
if page == "report":
    rep = st.session_state.get("scam")
    if not rep:
        st.info("Run Scamurai in ⚔️ Live demo first (Sections, in the sidebar).")
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
if page == "score":
    from eval.scoreboard import DEMO_NOTE, RESULTS, chart, memory_note, table

    if st.button("Run every setup against every task"):
        wait = st.empty()
        wait.markdown(theme.orb("Running 5 setups x 8 tasks", "plus the memory second pass"), unsafe_allow_html=True)
        try:
            import subprocess

            subprocess.run([sys.executable, "-m", "eval.run_tests"], cwd=ROOT, check=True)
        finally:
            wait.empty()
    if RESULTS.exists():
        res = json.loads(RESULTS.read_text())
        st.dataframe(table(res), hide_index=True, use_container_width=True)
        fig = chart(res)
        theme.style_chart(fig)
        st.pyplot(fig)
        st.caption(f"Brain: {res['backend']}. Numbers come from data/results.json.  \n"
                   + (f"{memory_note(res)}  \n" if memory_note(res) else "") + DEMO_NOTE)
    else:
        st.info("No results yet. Press the button above.")

# ---------------------------------------------------------------- audit log
if page == "log":
    if DB.exists():
        con = sqlite3.connect(DB)
        runs = pd.read_sql("SELECT id, datetime(ts, 'unixepoch', 'localtime') AS time, setup, goal FROM runs ORDER BY id DESC LIMIT 20", con)
        st.dataframe(runs, hide_index=True, use_container_width=True)
        if len(runs):
            rid = st.selectbox("Run", runs["id"].tolist())
            st.dataframe(pd.read_sql("SELECT step, action, tier, decision, why FROM decisions WHERE run_id=? ORDER BY step", con, params=(rid,)),
                         hide_index=True, use_container_width=True)
