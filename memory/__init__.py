"""Scamurai's memory: it learns only from its own verdicts, never from page text or the LLM's opinion."""
from memory.store import Memory, fingerprint

__all__ = ["Memory", "fingerprint"]
