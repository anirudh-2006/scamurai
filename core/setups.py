"""The five setups from section 9 of the md. Protections are switched on one at a time."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Setup:
    name: str
    two_views: bool = False
    source_labels: bool = False
    firewall: bool = False
    voters: bool = False
    decoys: bool = False


SETUPS = [
    Setup("Plain agent"),
    Setup("+ Two views", two_views=True),
    Setup("+ Source labels", two_views=True, source_labels=True),
    Setup("+ Firewall and voters", two_views=True, source_labels=True, firewall=True, voters=True),
    Setup("+ Decoys (full Scamurai)", two_views=True, source_labels=True, firewall=True, voters=True, decoys=True),
]
PLAIN = SETUPS[0]
SCAMURAI = SETUPS[-1]
