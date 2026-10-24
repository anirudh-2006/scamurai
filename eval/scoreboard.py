"""Build the results table and chart from data/results.json."""
from __future__ import annotations

import json

import pandas as pd

from core.config import ROOT

RESULTS = ROOT / "data" / "results.json"

# A4 decision, shown under the scoreboard.
DEMO_NOTE = ("Mock naive agent. Real model gpt-oss-20b: address sent in 2 of 3 plain runs, 0 of 3 with Scamurai.")


def table(out: dict) -> pd.DataFrame:
    rows = []
    for s in out["setups"]:
        rows.append({
            "Setup": s["setup"],
            f"Fooled (of {s['bait_tasks']} baited tasks)": s["fooled"],
            f"Hijacked (of {s['commands']} commands)": s["hijacked"],
            "Legit actions wrongly stopped": f"{s['false_alarms']} of {s['legit_actions']}",  # count differs per setup
            "Caught only by voters": s["vote_rescued"],
            "ms per action": s["ms_per_action"],
        })
    return pd.DataFrame(rows)


def memory_note(out: dict) -> str:
    """One line on what memory changed, for the memory row (which the table can't show)."""
    mem = next((s for s in out["setups"] if s["setup"].startswith("+ Memory")), None)
    full = next((s for s in out["setups"] if s["setup"].startswith("+ Decoys")), None)
    if not mem or not full:
        return ""
    return (f"+ Memory (second pass): {mem['known_on_read']} known threats dropped on read; "
            f"sessions frozen {mem['frozen_tasks']} of {len(mem['runs'])} (without memory: {full['frozen_tasks']}).")


def print_table(out: dict) -> None:
    print(f"\nScoreboard (backend: {out['backend']})\n")
    print(table(out).to_string(index=False))
    if note := memory_note(out):
        print(f"\n{note}")
    print(f"\n{DEMO_NOTE}")


def chart(out: dict, path=None):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = [s["setup"] for s in out["setups"]]
    fooled = [s["fooled"] for s in out["setups"]]
    hijacked = [s["hijacked"] for s in out["setups"]]
    x = range(len(names))
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar([i - 0.2 for i in x], fooled, width=0.4, label="Fooled", color="#d9822b")
    ax.bar([i + 0.2 for i in x], hijacked, width=0.4, label="Hijacked", color="#c23030")
    ax.set_xticks(list(x), names, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("Count")
    ax.set_title("Each protection removes a class of attack")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150)
    return fig


if __name__ == "__main__":
    out = json.loads(RESULTS.read_text())
    print_table(out)
    chart(out, ROOT / "data" / "scoreboard.png")
