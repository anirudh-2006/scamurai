"""Minimal LLM client: Anthropic or any OpenAI-compatible endpoint (OpenAI, Groq, Ollama).

Responses are cached on disk by prompt, so a demo run can be replayed exactly with no network.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time

import requests

from core.config import ROOT

CACHE = ROOT / "data" / "llm_cache"


class LLM:
    def __init__(self, backend: str, model: str, base_url: str = "", temperature: float = 0, use_cache: bool = True,
                 api_key: str = ""):
        self.backend, self.model, self.base_url, self.temperature, self.use_cache = backend, model, base_url, temperature, use_cache
        self.api_key = api_key

    def complete(self, prompt: str) -> str:
        return self.chat("Answer briefly.", [{"role": "user", "content": prompt}])

    def chat(self, system: str, messages: list[dict]) -> str:
        CACHE.mkdir(parents=True, exist_ok=True)
        h = hashlib.sha1(json.dumps([self.backend, self.model, system, messages], ensure_ascii=False).encode()).hexdigest()
        f = CACHE / f"{h}.txt"
        if self.use_cache and f.exists():
            return f.read_text(encoding="utf-8")
        out = self._anthropic(system, messages) if self.backend == "anthropic" else self._openai(system, messages)
        f.write_text(out, encoding="utf-8")
        return out

    def _anthropic(self, system: str, messages: list[dict]) -> str:
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=60, headers={
            "x-api-key": self.api_key or os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": self.model, "max_tokens": 600, "temperature": self.temperature, "system": system, "messages": messages})
        r.raise_for_status()
        return r.json()["content"][0]["text"]

    def _openai(self, system: str, messages: list[dict]) -> str:
        for attempt in range(6):
            try:
                r = requests.post(f"{self.base_url.rstrip('/')}/chat/completions", timeout=(10, 90),
                                  headers={"Authorization": f"Bearer {self.api_key or self._env_key()}"},
                                  json={"model": self.model, "temperature": self.temperature,
                                        "messages": [{"role": "system", "content": system}, *messages]})
            except (requests.ConnectionError, requests.Timeout):
                if attempt == 5:
                    raise
                time.sleep(2 ** attempt)  # flaky network: back off and retry
                continue
            if r.status_code != 429:
                break
            # Rate limited (Groq free tier: tokens per minute). Wait as long as the server asks, then retry.
            m = re.search(r"try again in ([\d.]+)s", r.text)
            time.sleep(min(60.0, float(m.group(1)) + 0.5 if m else float(r.headers.get("retry-after", 2 ** attempt))))
        if r.status_code == 400 and '"failed_generation"' in r.text:
            # Groq rejected the reply (tool_use_failed: the model tried a native tool call; output_parse_failed:
            # prose). Keep what the model wrote; shopper._parse handles {"name": ..., "arguments": ...} and
            # asks again for JSON if there is none.
            return r.json()["error"].get("failed_generation", "")
        if not r.ok:
            raise RuntimeError(f"{self.backend} {self.model}: HTTP {r.status_code}: {r.text[:500]}")
        return r.json()["choices"][0]["message"].get("content") or ""

    def _env_key(self) -> str:
        if "groq.com" in self.base_url:
            return os.environ.get("GROQ_API_KEY", "")
        return os.environ.get("OPENAI_API_KEY", "ollama")


def from_config(cfg: dict):
    """The shopper's LLM, or None for the mock backend."""
    if cfg.get("backend", "mock") == "mock":
        return None
    return LLM(cfg["backend"], cfg["model"], cfg.get("openai_base_url", ""), cfg.get("temperature", 0),
               use_cache=cfg.get("llm_cache", True), api_key=cfg.get("api_key", ""))


def voter_from_config(cfg: dict):
    """The voters' LLM: voter_backend / voter_model if set, else the same as the shopper."""
    if not (cfg.get("voter_backend") or cfg.get("voter_model")):
        return from_config(cfg)
    return from_config({**cfg, "backend": cfg.get("voter_backend", cfg.get("backend")),
                        "model": cfg.get("voter_model", cfg.get("model")),
                        "openai_base_url": cfg.get("voter_base_url", cfg.get("openai_base_url", "")),
                        "api_key": cfg.get("voter_api_key", cfg.get("api_key", ""))})
