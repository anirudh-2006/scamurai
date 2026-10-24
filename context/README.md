# How to use these context files during the hackathon

Each person gives their AI coding assistant two files at a time:

1. `00_SHARED.md`, always. It holds the contract every module must follow.
2. The file for the current phase, plus a pointer to your own section in it ("I am Person 2").

| File | Hours | Ends with (checkpoint) |
|---|---|---|
| `PHASE_0_before_event.md` | before the day | Accounts, keys and bait text ready. No code |
| `PHASE_1_trap.md` | 0 to 3 | The plain agent reliably falls for the phone page |
| `PHASE_2_defence.md` | 3 to 6 | **Demo works:** plain fails, Scamurai blocks, side by side |
| `PHASE_3_extras.md` | 6 to 8 | Decoys, voters, all pages, scoreboard numbers. **Feature freeze at hour 8** |
| `PHASE_4_demo.md` | 8 to 10 | Polished dashboard, real numbers, backup video, two rehearsals |
| `DEMO.md` | read it now | The 3-minute script. Everything else serves this |

## The one rule

**The phone scenario (Nova X5 / Orion 8 / Pixel Lite) is built first and never broken.** Every phase
ends with something you could show a judge. If you are behind, cut in this order: voters, extra
pages, dashboard polish. Never cut the plain vs Scamurai comparison.

## Team

| Person | Owns |
|---|---|
| P1 | Shopper agent + source labels (`agent/`) |
| P2 | Two views (`views/`) |
| P3 | Test shop, bait, decoys, scoring (`shop/`, `firewall/decoys.py`, `eval/`) |
| P4 | Firewall, dashboard, pitch (`firewall/`, `log/`, `dashboard/`) |

Integration happens at three fixed times: **hour 3, hour 6, hour 8**. Everyone merges to `main` and
runs `python -m demo.run_demo` together.
