"""
IriLine Collective
Motto: Context, not copies.

We do NOT plagiarize.
All summaries are original, human-readable context
from public sources.
"""
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
# IMAGE KEYWORD LOGIC
# -------------------------

def extract_keywords(title: str, limit=3):
    """
    Pulls meaningful keywords from a title.
    Keeps it simple and safe.
    """
    stopwords = {
        "the", "a", "an", "and", "or", "to", "of", "in",
        "on", "for", "with", "as", "is", "are", "was"
    }

    words = re.findall(r"[a-zA-Z]{4,}", title.lower())
    keywords = [w for w in words if w not in stopwords]

    return keywords[:limit] if keywords else ["news"]

def pick_unsplash_image(section: str, seed: str, title: str):
    title_l = title.lower()
    section_map = INTENT_IMAGE_QUERIES.get(section, {})

    # Topic override (NBA, election, war, etc.)
    for keyword, queries in section_map.items():
        if keyword != "default" and keyword in title_l:
            query = random.choice(queries)
            break
    else:
        query = random.choice(section_map.get("default", ["news"]))

    return {
        "url": f"https://source.unsplash.com/1600x900/?{query.replace(' ', ',')}&sig={seed}",
        "credit": "Photo via Unsplash (free to use)"
    }


def extract_rss_image(entry):
    if "media_content" in entry and entry["media_content"]:
        return entry["media_content"][0].get("url")
    if "media_thumbnail" in entry and entry["media_thumbnail"]:
        return entry["media_thumbnail"][0].get("url")
    if "enclosures" in entry and entry["enclosures"]:
        return entry["enclosures"][0].get("href")
    return None

# -------------------------
# HELPERS
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

    # -------- LATEST --------
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
            summary = clean_text(e.get("summary", ""))

            rss_img = extract_rss_image(e)
            if rss_img:
                image = {
                    "url": rss_img,
                    "credit": "Image via original publisher"
                }
            else:
                image = pick_unsplash_image("LATEST", pid, title)

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

    # -------- MERGE / ARCHIVE --------
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
