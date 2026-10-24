# Scamurai: pre-hackathon prototype

A working reference build of the Scamurai design doc. **It is for learning and testing only.** If the
rules say no code built before the event, don't bring this code. Bring what you learned and the
`context/` files. The spec in those files is what you rebuild from on the day.

## Run it

```bash
pip install -r requirements.txt
playwright install chromium            # once

python -m pytest -q                    # 10 firewall tests
python -m demo.run_demo                # terminal demo: plain agent vs Scamurai on the phone task
python -m demo.run_demo --task earbuds --all-setups
python -m eval.run_tests --fresh       # scoreboard: 5 setups x 8 tasks + memory second pass -> data/results.json
streamlit run dashboard/app.py         # the dashboard used for the live demo
```

The shop starts on its own (http://127.0.0.1:5050) when any of these run. To browse it by hand, run
`python -m shop.app`.

## Brains

`config.yaml` → `backend:`

| backend | What it is | When to use |
|---|---|---|
| `mock` | Deterministic, deliberately gullible agent (`agent/mock_brain.py`) | Building, testing, the demo backup. No key, no Wi-Fi |
| `anthropic` | Claude via the HTTP API, needs `ANTHROPIC_API_KEY` | Real-agent runs |
| `openai` | Any OpenAI-compatible endpoint: OpenAI, Groq, local Ollama (`openai_base_url`) | Real-agent runs, offline with Ollama |

LLM answers are cached in `data/llm_cache/`, so a demo run replays identically. The real-LLM loop is
in `agent/shopper.py::run_llm`; every real run saves its full message list to `data/transcripts/`.
We ran it with `openai/gpt-oss-20b` on Groq: on the phone task the plain agent sent the address to
partner-deals in 2 of 3 runs but never picked Nova X5, so the live demo uses `mock` (see `config.yaml`).

## What the prototype shows (brain: `mock`, 8 tasks, 19 pages)

From `python -m eval.run_tests --fresh`:

| Setup | Fooled (of 5) | Hijacked (of 8) | Legit actions wrongly stopped | Caught only by voters |
|---|---|---|---|---|
| Plain agent | 5 | 8 | 0 of 50 | 0 |
| + Two views | 2 | 5 | 0 of 50 | 0 |
| + Source labels | 1 | 2 | 0 of 50 | 0 |
| + Firewall and voters | 0 | 0 | 0 of 52 | 1 |
| + Decoys (full Scamurai) | 0 | 0 | 0 of 52 | 1 |
| + Memory (second pass) | 0 | 0 | 0 of 52 | 1 |

- **Caught only by voters:** bait the voters rejected where every key detail came from you or a tool, so
  source labels could never catch it. The one case: LiteCell 10K charges at 10 W, the goal asks for at
  least 20 W. Seller upsells the voters also reject aren't counted (source labels stop those anyway).
- **+ Memory (second pass):** full Scamurai, each task twice with a throwaway memory DB, scoring the
  second pass. 11 known threats are dropped on read, and 0 of 8 sessions freeze (2 without memory).
- Real model, for comparison: gpt-oss-20b (Groq) sent the address in 2 of 3 plain runs, 0 of 3 with Scamurai.

These are numbers for a mock agent on a test shop we wrote ourselves. They prove the plumbing works,
not that Scamurai beats real attackers.

## Where each md section lives

| md section | Code |
|---|---|
| 3.1 Shopper agent | `agent/shopper.py`, `agent/mock_brain.py`, `agent/llm.py` |
| 3.2 Two views | `views/capture.py` (Playwright + bot fetch), `views/claims.py` |
| 3.3 Source labels | `agent/labels.py` (deterministic, never asks the LLM) |
| 3.4 Firewall | `firewall/severity.py`, `rules.py`, `voters.py`, `gate.py` |
| 3.5 Decoys | `firewall/decoys.py` |
| 3.6 Report card | `agent/session.py::report`, dashboard Report card tab |
| 5 Shared action format | `core/schema.py` |
| 8 Test shop | `shop/` (`pages.yaml` holds every page and its bait) |
| 9 Measuring success | `eval/run_tests.py`, `eval/scoreboard.py` |

## Changes from the md (and why)

1. **Source labels are computed, not asked.** A detail is `user` only if it matches the goal or the
   profile. It is `tool` if it appears in search or cart output. Everything else is `seller`, which
   fails closed.
2. **Links on a site you named are low risk.** "Never follow a link from seller text" would block
   every "next page" and review link. Links that leave your sites are still high risk and blocked.
3. **Pages reached through a seller's link are marked as the seller's.** This is how fake backup is
   beaten: a "TechTruth" review linked from Hush Audio's page doesn't count as independent.
4. **Decoy hits are attributed to the text, not blindly to the seller.** The Nova X5 decoy command sits
   in a customer review, and the report says so.
5. **After a decoy freeze the agent can still recommend**, because a recommendation buys nothing.
   Cart and pay stay frozen until you approve.
6. **Honest caveat on voters:** every attack the voters rejected would also have been blocked by
   source labels alone. They add explanation, not extra catches. Either add grey-zone pages where only
   judgment helps (an add-on found through search, a cheaper option that drops a required feature) or
   say this openly in the pitch.
