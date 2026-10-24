# Phase 4: the proof (hours 8 to 10)

**Checkpoint at hour 10:** two clean timed rehearsals of `DEMO.md`, a backup video, real numbers on the
scoreboard.

## Hour 8 to 9

**P4: dashboard polish**
- Report card tab: recommendation with price and reasons; bait found table (page, tag, text, reason); actions stopped table (action, details with `[source]`, decision, why); seller trust as progress bars; red flag box with the decoy's trigger text; **Approve** button → "Order placed for Orion 8 (simulated). Nothing was bought until you pressed this."
- Scoreboard tab: button that runs `eval.run_tests`, then the table and chart from `data/results.json`.
- Audit log tab: last 20 runs, and each run's decisions.
- Feed speed slider so the live feed is readable (0.5 s per step works on a projector).

**P3: run the numbers**
- `python -m eval.run_tests --fresh` with the mock brain, then with the real LLM if time allows.
- Put the real numbers into the pitch slides. Never show "?" cells.

**P1 + P2: break it**
- Try to make the demo fail: second run, cleared cache, slow Wi-Fi (turn it off), wrong task picked. Fix only what breaks the demo path.
- Check `ollama` fallback works with Wi-Fi off.

## Hour 9 to 10

- [ ] **Backup video** of a clean "Run both" plus the Two views tab (screen recording, about 2 minutes). Save it locally and to a USB stick.
- [ ] Rehearsal 1, timed. Fix the slowest part.
- [ ] Rehearsal 2, timed. Stop changing code after this.
- [ ] Demo laptop: dashboard open on the Two views tab with Nova X5 selected, phone task selected, previous runs cleared (restart Streamlit), screen zoom 125 %, notifications off.

## Slides (P4, at most 5)

1. Hook: the same page, seen by you vs read by your agent (screenshot from the Two views tab)
2. The trap: plain agent result in one line, with the three red leaks
3. How Scamurai works: reading → deciding → acting (the architecture picture)
4. The proof: the scoreboard
5. What's next: Scamurai Shield (Python package), Scamurai for Chrome, real-world scan
