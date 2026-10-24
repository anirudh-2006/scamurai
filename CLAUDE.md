# Scamurai: notes for Claude Code

Scamurai is a hackathon project: an AI shopping agent with a built-in
firewall against hidden text, bot-only pages, hidden commands, persuasion aimed at AI, and fake backup
reviews. We are building it during the hackathon on one laptop.

Read `context/00_SHARED.md` for the architecture and the contract (`core/schema.py`). The current task
file is in `context/` (start with `P1_REAL_LLM_AND_MEMORY.md`).

## Commands (run from the repo root, with the venv active: `source .venv/bin/activate`)

```bash
python -m pytest -q                      # must stay green
python -m demo.run_demo                  # phone task: plain agent vs Scamurai (the demo scenario)
python -m demo.run_demo --task earbuds --all-setups
python -m eval.run_tests --fresh         # scoreboard -> data/results.json
streamlit run dashboard/app.py           # the live demo UI
```

The test shop starts on its own on http://127.0.0.1:5050.

## Rules that never bend

1. **The phone scenario must keep working.** After every change, run `python -m pytest -q` and
   `python -m demo.run_demo`. Full Scamurai on phones must show: two HIDDEN rows on nova-x5, the
   Nova Shield Case voted down 1 to 2, send_address blocked, export_order_history FROZEN, Orion 8
   recommended. The plain agent must pick Nova X5 and leak 3 things.
2. **`backend: mock` must keep working.** It is the offline fallback and the demo backup.
3. **Source labels are computed, never asked of the LLM.** Never use `reason_given` or page text to
   decide whether an action is allowed.
4. **Never commit API keys.** Keys go in environment variables or `config.local.yaml` (gitignored).
5. Don't change `core/schema.py` unless it's unavoidable; say so if you do.
6. Small, reviewable changes. Explain what changed after each step.
