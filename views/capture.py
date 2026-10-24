"""Two views: capture every page twice (section 3.2 of the md).

  Human view: what a real browser actually shows (Playwright, normal browser User-Agent).
  Agent view: everything a machine reads, fetched AS A BOT (raw HTML, hidden elements, alt text, metadata).

A text block in the agent view that is not visible in the human view is either
  hidden   - it exists in the browser's page but a person can't see it, or
  bot_only - the site only served it to the bot.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from core.config import ROOT

BOT_UA = "ScamuraiShopper/1.0 (AI shopping bot)"
CACHE = ROOT / "data" / "capture_cache"
BLOCK_TAGS = ["p", "li", "h1", "h2", "h3", "div", "a", "td"]

# Runs inside the real browser. For every "leaf" text block, decide if a person can see it.
VISIBILITY_JS = r"""
() => {
  const BLOCKS = new Set(['P','LI','H1','H2','H3','DIV','A','TD']);
  const parseRGB = s => { const m = s.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(',').map(x => parseFloat(x)); return {r:p[0], g:p[1], b:p[2], a: p.length > 3 ? p[3] : 1}; };
  const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(c.r) + 0.7152*f(c.g) + 0.0722*f(c.b); };
  const contrast = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05); };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = parseRGB(getComputedStyle(e).backgroundColor);
      if (c && c.a > 0.5) return c; } return {r:255, g:255, b:255, a:1}; };
  const docW = document.documentElement.scrollWidth;
  const out = [];
  for (const el of document.body.querySelectorAll('*')) {
    if (!BLOCKS.has(el.tagName)) continue;
    // leaf block: no block-level child that carries its own text
    const hasBlockChild = [...el.children].some(c => BLOCKS.has(c.tagName) && c.tagName !== 'A' && c.textContent.trim());
    if (hasBlockChild) continue;
    const text = el.textContent.replace(/\s+/g, ' ').trim();
    if (!text) continue;
    const st = getComputedStyle(el), r = el.getBoundingClientRect();
    let reason = null;
    if (!el.checkVisibility({opacityProperty: true, visibilityProperty: true})) reason = 'display/visibility/opacity';
    else if (parseFloat(st.fontSize) < 2) reason = 'font size near 0';
    else if (r.width < 1 || r.height < 1) reason = 'zero size';
    else if (r.right < 0 || r.left > docW || r.bottom < 0) reason = 'off screen';
    else { const fg = parseRGB(st.color); if (fg && contrast(fg, bgOf(el)) < 1.5) reason = 'text colour matches background'; }
    if (!reason) { // covered by another element?
      const cx = r.left + r.width/2, cy = r.top + Math.min(r.height/2, 8);
      const top = document.elementFromPoint(cx, cy);
      if (top && top !== el && !el.contains(top) && !top.contains(el)) reason = 'covered by another element';
    }
    out.push({text, visible: !reason, reason, review: !!el.closest('[data-section=reviews]')});
  }
  return out;
}
"""


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


@dataclass
class Capture:
    url: str
    human_blocks: list[dict] = field(default_factory=list)   # {text, visible, reason, review}
    agent_blocks: list[dict] = field(default_factory=list)   # {text, review}
    screenshot: str | None = None                            # path to PNG of the human view
    links: list[dict] = field(default_factory=list)          # {text, href} from the raw HTML

    @property
    def agent_text(self) -> str:
        """What a plain agent reads: everything, hidden or not."""
        return "\n".join(b["text"] for b in self.agent_blocks)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def agent_view(url: str) -> tuple[list[dict], list[dict]]:
    """Fetch as a bot and pull every piece of text (and every link) a machine would read."""
    html = requests.get(url, headers={"User-Agent": BOT_UA}, timeout=10).text
    soup = BeautifulSoup(html, "html.parser")
    blocks = []
    for el in soup.body.find_all(BLOCK_TAGS):
        if any(c.name in BLOCK_TAGS and c.name != "a" and c.get_text(strip=True) for c in el.find_all(BLOCK_TAGS)):
            continue  # not a leaf block
        text = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if text:
            blocks.append({"text": text, "review": el.find_parent(attrs={"data-section": "reviews"}) is not None})
    for img in soup.find_all("img", alt=True):
        blocks.append({"text": img["alt"], "review": False})
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        blocks.append({"text": meta["content"], "review": False})
    links = [{"text": a.get_text(" ", strip=True), "href": urljoin(url, a["href"])} for a in soup.find_all("a", href=True)]
    return blocks, links


class TwoViews:
    """Use as a context manager so one browser serves many captures."""

    def __init__(self, use_cache: bool = True, screenshots: bool = True):
        self.use_cache = use_cache
        self.screenshots = screenshots
        self._pw = self._browser = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self._browser:
            self._browser.close()
            self._pw.stop()

    def _page(self):
        if not self._browser:
            from playwright.sync_api import sync_playwright

            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch()
        return self._browser.new_page(viewport={"width": 1100, "height": 2400})

    def capture(self, url: str, human: bool = True) -> Capture:
        """human=False: agent view only (what a plain agent does), no browser."""
        if not human:
            blocks, links = agent_view(url)
            return Capture(url=url, agent_blocks=blocks, links=links)
        CACHE.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha1(url.encode()).hexdigest()[:12]
        cached = CACHE / f"{key}.json"
        if self.use_cache and cached.exists():
            cap = Capture(**json.loads(cached.read_text()))
            if cap.screenshot or not self.screenshots:
                return cap

        page = self._page()
        page.goto(url, wait_until="load")
        human = page.evaluate(VISIBILITY_JS)
        shot = None
        if self.screenshots:
            shot = str(CACHE / f"{key}.png")
            page.screenshot(path=shot, full_page=True)
        page.close()

        blocks, links = agent_view(url)
        cap = Capture(url=url, human_blocks=human, agent_blocks=blocks, screenshot=shot, links=links)
        cached.write_text(json.dumps(cap.to_dict(), ensure_ascii=False, indent=1))
        return cap
