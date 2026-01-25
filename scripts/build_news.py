import html
import random
import logging
import hashlib
import json, os, re
from datetime import datetime, timezone, timedelta

import feedparser
from dateutil import parser as dtparser

logging.basicConfig(level=logging.INFO)
GREEN = "#0B3D2E"


# -------------------------
# Helpers
# -------------------------

def now_utc():
    return datetime.now(timezone.utc)

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def clean_text(s: str) -> str:
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()

def make_id(prefix, url):
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{h}"

def pick_image_stub(section: str) -> str:
    return {
        "LATEST": "https://images.unsplash.com/photo-1504711434969-e33886168f5c",
        "SPORTS": "https://images.unsplash.com/photo-1502877338535-766e1452684a",
        "MEME": "https://images.unsplash.com/photo-1520975916090-3105956dac38",
    }.get(section, "")

def fetch_rss(url):
    feed = feedparser.parse(url)
    return feed.entries if hasattr(feed, "entries") else []

def parse_time(entry):
    for key in ("published", "updated", "created"):
        if key in entry:
            try:
                return dtparser.parse(entry[key]).astimezone(timezone.utc)
            except Exception:
                pass
    return None

def iso_to_dt(s):
    try:
        return dtparser.isoparse(s)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


# -------------------------
# Main builder
# -------------------------

def build_items():
    sources = load_json("data/sources.json", {})
    live = load_json("data/live.json", {"generatedAt": "", "items": []})
    archive = load_json("data/archive.json", {"items": []})

    existing_ids = {i["id"] for i in live["items"]} | {i["id"] for i in archive["items"]}
    items_new = []

    # -------- LATEST --------
    cutoff = now_utc() - timedelta(hours=24)

    for rss in sources.get("latest", {}).get("rss", []):
        entries = fetch_rss(rss)[:30]
        logging.info(f"[LATEST] {rss} -> {len(entries)} entries")

        for e in entries:
            url = e.get("link", "")
            if not url:
                continue

            pid = make_id("latest", url)
            if pid in existing_ids:
                continue

            t = parse_time(e) or now_utc()
            if t < cutoff:
                continue

            title = clean_text(e.get("title", ""))
            desc = clean_text(e.get("summary", ""))

            items_new.append({
                "id": pid,
                "section": "LATEST",
                "title": title,
                "body": desc,
                "publishedAt": t.isoformat(timespec="seconds"),
                "sourceUrl": url,
                "image": pick_image_stub("LATEST"),
            })

    # -------- MERGE --------
    all_live = live["items"] + items_new
    all_live.sort(key=lambda x: iso_to_dt(x.get("publishedAt", "")), reverse=True)

    LIVE_MAX = 40
    still_live = all_live[:LIVE_MAX]
    to_archive = all_live[LIVE_MAX:]

    arch_items = archive["items"]
    arch_ids = {i["id"] for i in arch_items}

    for it in to_archive:
        if it["id"] not in arch_ids:
            arch_items.append(it)

    arch_items.sort(key=lambda x: iso_to_dt(x.get("publishedAt", "")), reverse=True)
    arch_items[:] = arch_items[:300]

    save_json("data/live.json", {
        "generatedAt": now_utc().isoformat(timespec="seconds"),
        "items": still_live
    })
    save_json("data/archive.json", {"items": arch_items})

    logging.info(f"New items added: {len(items_new)}")
    logging.info(f"Live={len(still_live)} Archive={len(arch_items)}")


if __name__ == "__main__":
    build_items()
