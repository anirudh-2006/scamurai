"""Scamurai test shop (Flask).

A small fake marketplace whose product pages carry the five kinds of bait.
Run it on its own with:  python -m shop.app
"""
from __future__ import annotations

import socket
import threading
from pathlib import Path

import yaml
from flask import Flask, abort, jsonify, render_template, request

HERE = Path(__file__).parent
DATA = yaml.safe_load((HERE / "pages.yaml").read_text(encoding="utf-8"))
PRODUCTS = {p["id"]: p for p in DATA["products"]}
REVIEWS = {r["id"]: r for r in DATA.get("review_pages", [])}
TASKS = DATA["tasks"]

# Words in a search query that map to a category.
CATEGORY_WORDS = {
    "phones": ["phone", "smartphone", "mobile"],
    "earbuds": ["earbud", "earbuds", "tws"],
    "laptops": ["laptop", "notebook"],
    "watches": ["smartwatch", "watch"],
    "headphones": ["headphone", "headphones"],
    "powerbanks": ["power bank", "powerbank"],
    "kettles": ["kettle"],
    "backpacks": ["backpack", "bag"],
}

app = Flask(__name__, template_folder=str(HERE / "templates"))


def is_bot(req) -> bool:
    """The trick a bot-only page uses: look at the User-Agent."""
    ua = req.headers.get("User-Agent", "").lower()
    return "bot" in ua or "scamurai" in ua


def match_category(query: str) -> str | None:
    q = query.lower()
    # Check "backpack" before "bag"-like collisions and "laptop backpack" before "laptop".
    for cat in ["backpacks", "powerbanks", "headphones", "earbuds", "watches", "kettles", "laptops", "phones"]:
        if any(w in q for w in CATEGORY_WORDS[cat]):
            return cat
    return None


@app.route("/")
def index():
    cats = {}
    for p in PRODUCTS.values():
        cats.setdefault(p["category"], []).append(p)
    return render_template("index.html", cats=cats)


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    cat = match_category(q)
    results = [
        {
            "id": p["id"],
            "name": p["name"],
            "seller": p["seller"],
            "price": p["price"],
            "specs": p.get("specs", []),
            "url": f"{request.host_url}p/{p['id']}",
        }
        for p in PRODUCTS.values()
        if p["category"] == cat
    ]
    return jsonify({"query": q, "category": cat, "results": results})


@app.route("/p/<pid>")
def product(pid):
    p = PRODUCTS.get(pid) or abort(404)
    bait = p.get("bait", [])
    bot = is_bot(request)
    return render_template(
        "product.html",
        p=p,
        bot=bot,
        hidden=[b for b in bait if b["type"] == "hidden" or (b["type"] == "command" and b.get("visibility") == "hidden")],
        bot_only=[b for b in bait if b["type"] == "bot_only" or (b["type"] == "command" and b.get("visibility") == "bot_only")],
        visible_cmds=[b for b in bait if b["type"] == "command" and b.get("visibility") == "visible"],
        persuasion=[b for b in bait if b["type"] == "persuasion"],
    )


@app.route("/reviews/<rid>")
def review_page(rid):
    r = REVIEWS.get(rid) or abort(404)
    return render_template("review.html", r=r, product=PRODUCTS[r["about"]])


# ---------------------------------------------------------------- server helper
def port_open(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) == 0


def ensure_running(host: str = "127.0.0.1", port: int = 5050) -> str:
    """Start the shop in a background thread if nothing is listening yet."""
    if not port_open(host, port):
        import logging

        from werkzeug.serving import make_server

        logging.getLogger("werkzeug").setLevel(logging.ERROR)

        server = make_server(host, port, app, threaded=True)
        threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://{host}:{port}"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
