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

    def process_rss_feed(section, rss_feed, category, section_label, type_label):
        """
        Process a section's RSS feed and append new articles to `items_new`.
        """
        entries = fetch_rss(rss_feed)[:30]
        logging.debug(f"[{section}] {rss_feed} -> {len(entries)} entries")

        for e in entries:
            url = e.get("link")
            if not url:
                logging.debug(f"Skipping article with no URL: {e.get('title')}")
                continue

            pid = make_id(section, url)
            if pid in existing_ids:
                logging.debug(f"Article already exists: {url}")
                continue

            t = parse_time(e) or now_utc()
            if t < cutoff:
                logging.debug(f"Article is older than cutoff: {url}")
                continue

            title = clean_text(e.get("title", ""))
            summary = clean_text(e.get("summary", ""))

            rss_img = extract_rss_image(e)
            image = (
                {"url": rss_img, "credit": "Image via original publisher"}
                if rss_img
                else pick_unsplash_image(section, pid, title)
            )

            items_new.append({
                "id": pid,
                "section": section,
                "sectionLabel": section_label,
                "type": type_label,
                "category": category,
                "title": title,
                "dek": summary[:160],
                "body": summary,
                "author": "IriLine Desk",
                "publishedAt": t.isoformat(timespec="seconds"),
                "sourceUrl": url,
                "image": image["url"],
                "imageCredit": image["credit"],
            })
            logging.debug(f"Processed article: {title} (ID: {pid})")

    # -------- LATEST --------
    for rss in sources.get("latest", {}).get("rss", []):
        process_rss_feed("latest", rss, "WORLD", "Latest", "REAL")

    # -------- SPORTS --------
    for rss in sources.get("sports", {}).get("rss", []):
        process_rss_feed("sports", rss, "SPORTS", "Sports", "REAL")

    # -------- MEME / NOT-SO-SERIOUS --------
    for rss in sources.get("meme", {}).get("rss", []):
        process_rss_feed("meme", rss, "WEIRD", "Not-So-Serious", "MEME")

    # -------- MERGE / ARCHIVE --------
    all_live = live["items"] + items_new
    all_live.sort(key=lambda x: iso_to_dt(x["publishedAt"]), reverse=True)

    live_out = all_live[:3]  # Display only the 3 most recent live articles
    archive_out = archive["items"] + all_live[3:]
    archive_out = list({i["id"]: i for i in archive_out}.values())
    
    # Remove articles older than 1 month from the archive
    one_month_ago = now_utc() - timedelta(days=30)
    archive_out = [article for article in archive_out if iso_to_dt(article["publishedAt"]) >= one_month_ago]

    archive_out.sort(key=lambda x: iso_to_dt(x["publishedAt"]), reverse=True)
    archive_out = archive_out[:300]  # Limit to 300 archive items

    save_json("data/live.json", {
        "generatedAt": now_utc().isoformat(timespec="seconds"),
        "items": live_out
    })
    save_json("data/archive.json", {"items": archive_out})

    logging.info(f"New items: {len(items_new)} | Live: {len(live_out)} | Archive: {len(archive_out)}")

if __name__ == "__main__":
    build_items()
