"""
IriLine Collective
Motto: Context, not copies.

We do NOT plagiarize.
All summaries are original, human-readable context
from public sources.
"""

import html
import random
import logging
import hashlib
import json, os, re
from datetime import datetime, timezone, timedelta

import feedparser
from dateutil import parser as dtparser

logging.basicConfig(level=logging.INFO)

# -------------------------
# IMAGE INTENT MAP
# -------------------------

INTENT_IMAGE_QUERIES = {
    "SPORTS": {
        "nba": ["nba basketball game", "basketball arena crowd", "nba players action"],
        "trade": ["basketball press conference", "sports interview"],
        "default": ["basketball game action", "sports stadium crowd"]
    },
    "LATEST": {
        "election": ["election polling station", "ballot voting"],
        "war": ["military briefing room", "international news press"],
        "default": ["world news press", "journalism newsroom"]
    },
    "MEME": {
        "default": ["funny street sign", "unexpected moment", "public sign humor"]
    }
}

# -------------------------
# IMAGE HELPERS
# -------------------------

def pick_unsplash_image(section: str, seed: str, title: str):
    title_l = title.lower()
    section_map = INTENT_IMAGE_QUERIES.get(section, {})

    for key, queries in section_map.items():
        if key != "default" and key in title_l:
            query = random.choice(queries)
            break
    else:
        query = random.choice(section_map.get("default", ["news"]))

    return {
        "url": f"https://source.unsplash.com/1600x900/?{query.replace(' ', ',')}&sig={seed}",
        "credit": "Photo via Unsplash (free to use)"
    }

def extract_rss_image(entry):
    if entry.get("media_content"):
        return entry["media_content"][0].get("url")
    if entry.get("media_thumbnail"):
        return entry["media_thumbnail"][0].get("url")
    if entry.get("enclosures"):
        return entry["enclosures"][0].get("href")
    return None

# -------------------------
# GENERAL HELPERS
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
    return f"{prefix}_{hashlib.sha1(url.encode()).hexdigest()[:12]}"

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
# MAIN BUILDER
# -------------------------

def build_items():
    sources = load_json("data/sources.json", {})
    live = load_json("data/live.json", {"generatedAt": "", "items": []})
    archive = load_json("data/archive.json", {"items": []})

    existing_ids = {i["id"] for i in live["items"]} | {i["id"] for i in archive["items"]}
    items_new = []

    cutoff = now_utc() - timedelta(hours=24)

    for rss in sources.get("latest", {}).get("rss", []):
        entries = fetch_rss(rss)[:30]
        logging.info(f"[LATEST] {rss} -> {len(entries)} entries")

        for e in entries:
            url = e.get("link")
            if not url:
                continue

            pid = make_id("latest", url)
            if pid in existing_ids:
                continue

            t = parse_time(e) or now_utc()
            if t < cutoff:
                continue

            title = clean_text(e.get("title", ""))
            summary = clean_text(e.get("summary", ""))

            rss_img = extract_rss_image(e)
            image = (
                {"url": rss_img, "credit": "Image via original publisher"}
                if rss_img
                else pick_unsplash_image("LATEST", pid, title)
            )

            items_new.append({
                "id": pid,
                "section": "LATEST",
                "sectionLabel": "Latest",
                "type": "REAL",
                "category": "WORLD",
                "title": title,
                "dek": summary[:160],
                "body": summary,
                "author": "IriLine Desk",
                "publishedAt": t.isoformat(timespec="seconds"),
                "sourceUrl": url,
                "image": image["url"],
                "imageCredit": image["credit"],
            })
            # -------- SPORTS --------
for rss in sources.get("sports", {}).get("rss", []):
    entries = fetch_rss(rss)[:30]
    logging.info(f"[SPORTS] {rss} -> {len(entries)} entries")

    for e in entries:
        url = e.get("link", "")
        if not url:
            continue

        pid = make_id("sports", url)
        if pid in existing_ids:
            continue

        t = parse_time(e) or now_utc()
        if t < cutoff:
            continue

        title = clean_text(e.get("title", ""))
        summary = clean_text(e.get("summary", ""))

        rss_img = extract_rss_image(e)
        if rss_img:
            image = {
                "url": rss_img,
                "credit": "Image via original publisher"
            }
        else:
            image = pick_unsplash_image("SPORTS", pid, title)

        items_new.append({
            "id": pid,
            "section": "SPORTS",
            "sectionLabel": "Sports",
            "type": "REAL",
            "category": "SPORTS",
            "title": title,
            "dek": summary[:160],
            "body": summary,
            "author": "IriLine Sports Desk",
            "publishedAt": t.isoformat(timespec="seconds"),
            "sourceUrl": url,
            "image": image["url"],
            "imageCredit": image["credit"],
        })
# -------- SPORTS --------
for rss in sources.get("sports", {}).get("rss", []):
    entries = fetch_rss(rss)[:30]
    logging.info(f"[SPORTS] {rss} -> {len(entries)} entries")

    for e in entries:
        url = e.get("link", "")
        if not url:
            continue

        pid = make_id("sports", url)
        if pid in existing_ids:
            continue

        t = parse_time(e) or now_utc()
        if t < cutoff:
            continue

        title = clean_text(e.get("title", ""))
        summary = clean_text(e.get("summary", ""))

        rss_img = extract_rss_image(e)
        if rss_img:
            image = {
                "url": rss_img,
                "credit": "Image via original publisher"
            }
        else:
            image = pick_unsplash_image("SPORTS", pid, title)

        items_new.append({
            "id": pid,
            "section": "SPORTS",
            "sectionLabel": "Sports",
            "type": "REAL",
            "category": "SPORTS",
            "title": title,
            "dek": summary[:160],
            "body": summary,
            "author": "IriLine Sports Desk",
            "publishedAt": t.isoformat(timespec="seconds"),
            "sourceUrl": url,
            "image": image["url"],
            "imageCredit": image["credit"],
        })
# -------- MEME / NOT-SO-SERIOUS --------
for rss in sources.get("meme", {}).get("rss", []):
    entries = fetch_rss(rss)[:20]
    logging.info(f"[MEME] {rss} -> {len(entries)} entries")

    for e in entries:
        url = e.get("link", "")
        if not url:
            continue

        pid = make_id("meme", url)
        if pid in existing_ids:
            continue

        t = parse_time(e) or now_utc()

        title = clean_text(e.get("title", ""))
        summary = clean_text(e.get("summary", ""))

        rss_img = extract_rss_image(e)
        if rss_img:
            image = {
                "url": rss_img,
                "credit": "Image via original publisher"
            }
        else:
            image = pick_unsplash_image("MEME", pid, title)

        items_new.append({
            "id": pid,
            "section": "MEME",
            "sectionLabel": "Not-So-Serious",
            "type": "MEME",
            "category": "WEIRD",
            "title": title,
            "dek": summary[:120],
            "body": summary,
            "author": "Meme Bureau",
            "publishedAt": t.isoformat(timespec="seconds"),
            "sourceUrl": url,
            "image": image["url"],
            "imageCredit": image["credit"],
        })


    all_live = live["items"] + items_new
    all_live.sort(key=lambda x: iso_to_dt(x["publishedAt"]), reverse=True)

    live_out = all_live[:40]
    archive_out = archive["items"] + all_live[40:]
    archive_out = list({i["id"]: i for i in archive_out}.values())
    archive_out.sort(key=lambda x: iso_to_dt(x["publishedAt"]), reverse=True)
    archive_out = archive_out[:300]

    save_json("data/live.json", {
        "generatedAt": now_utc().isoformat(timespec="seconds"),
        "items": live_out
    })
    save_json("data/archive.json", {"items": archive_out})

    logging.info(f"New items: {len(items_new)} | Live: {len(live_out)} | Archive: {len(archive_out)}")

if __name__ == "__main__":
    build_items()
