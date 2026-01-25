import html
import random

import json, os, re, time
from datetime import datetime, timezone, timedelta
...

import feedparser
import requests
from dateutil import parser as dtparser

GREEN = "#0B3D2E"

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
    s = html.unescape(s or "")          # Decodes HTML entities
    s = re.sub(r"<[^>]+>", "", s)       # Removes HTML tags
    s = re.sub(r"\s+", " ", s).strip()  # Cleans up spacing
    return s



def make_id(prefix, url):
    h = abs(hash(url)) % (10**10)
    return f"{prefix}_{h}"

def pick_image_stub(query: str) -> str:
    # Static-safe default. You can upgrade to Unsplash/Pexels API later.
    # For now, use a neutral newsroom image.
    return "https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1600&q=70"

def summarize_safe(title: str, description: str, section: str):
    """
    IMPORTANT:
    - We are NOT trying to 'evade plagiarism detection'.
    - We are generating an ORIGINAL SUMMARY of the linked source.
    - Keep it short, clear, factual.
    """
    base = clean_text(description) or clean_text(title)

    if section == "MEME":
        # Meme section with short captions
        caption = random.choice([
            "Reality glitches again",
            "Timeline officially cursed",
            "No context required",
            "Someone explain this",
        ])
        return {
            "title": clean_text(title)[:120],
            "dek": caption,
            "body": f"{clean_text(title)}\n\nContext: {base}"
        }

    # “Latest” and “Sports”: concise summary
    lead = clean_text(title)
    detail = base
    if len(detail) > 220:
        detail = detail[:220].rsplit(" ", 1)[0] + "…"

    dek = f"{detail}"
    body = f"{lead}\n\nSummary:\n{detail}\n\nRead the original source for full context."
    return {"title": lead[:140], "dek": dek, "body": body}

def fetch_rss(url):
    feed = feedparser.parse(url)
    return feed.entries if hasattr(feed, "entries") else []

def parse_time(entry):
    # Try multiple fields
    for key in ["published", "updated", "created"]:
        if key in entry:
            try:
                return dtparser.parse(entry[key]).astimezone(timezone.utc)
            except Exception:
                pass
    return None

def build_items():
    repo_root = os.getcwd()
    sources = load_json("data/sources.json", {})

    live = load_json("data/live.json", {"generatedAt": "", "items": []})
    archive = load_json("data/archive.json", {"items": []})

    existing_ids = {i["id"] for i in live.get("items", [])} | {i["id"] for i in archive.get("items", [])}

    items_new = []

    # -------------------------
    # LATEST: world news
    # NOTE: “15 minutes prior” is often unrealistic for RSS.
    # We will FILTER to last 60 minutes by default (adjustable),
    # and you can tighten later depending on feed freshness.
    # -------------------------
    latest_cutoff = now_utc() - timedelta(hours=24)


    for rss in sources.get("latest", {}).get("rss", []):
        for e in fetch_rss(rss)[:30]:
            url = e.get("link", "")
            if not url:
                continue
            pid = make_id("latest", url)
            if pid in existing_ids:
                continue

            t = parse_time(e) or now_utc()
            if t < latest_cutoff:
                continue

            title = clean_text(e.get("title", ""))
            desc = clean_text(e.get("summary", ""))

            s = summarize_safe(title, desc, "LATEST")
            items_new.append({
                "id": pid,
                "section": "LATEST",
                "sectionLabel": "Latest",
                "type": "REAL",
                "category": "WORLD",
                "title": s["title"],
                "dek": s["dek"],
                "body": s["body"],
                "author": "IriLine Desk",
                "publishedAt": t.isoformat(timespec="seconds"),
                "sourceUrl": url,
                "image": pick_image_stub(title),
            })

    # -------------------------
    # SPORTS: prioritize injuries
    # -------------------------
    injury_keywords = [k.lower() for k in sources.get("sports", {}).get("keywords_injury", [])]
    sports_entries = []
    for rss in sources.get("sports", {}).get("rss", []):
        sports_entries.extend(fetch_rss(rss)[:40])

    def is_injury(title, summary):
        text = (title + " " + summary).lower()
        return any(k in text for k in injury_keywords)

    picked_sports = []
    # first pass: injuries
    for e in sports_entries:
        title = clean_text(e.get("title", ""))
        desc = clean_text(e.get("summary", ""))
        if is_injury(title, desc):
            picked_sports.append((e, "INJURY"))
    # fallback: basketball
    if not picked_sports:
        for e in sports_entries:
            title = clean_text(e.get("title", ""))
            desc = clean_text(e.get("summary", ""))
            if "nba" in (title + " " + desc).lower() or "basketball" in (title + " " + desc).lower():
                picked_sports.append((e, "BASKETBALL"))

    for e, cat in picked_sports[:6]:
        url = e.get("link", "")
        if not url:
            continue
        pid = make_id("sports", url)
        if pid in existing_ids:
            continue

        t = parse_time(e) or now_utc()
        title = clean_text(e.get("title", ""))
        desc = clean_text(e.get("summary", ""))

        s = summarize_safe(title, desc, "SPORTS")
        items_new.append({
            "id": pid,
            "section": "SPORTS",
            "sectionLabel": "Sports",
            "type": "REAL",
            "category": cat,
            "title": s["title"],
            "dek": s["dek"],
            "body": s["body"],
            "author": "IriLine Sports",
            "publishedAt": t.isoformat(timespec="seconds"),
            "sourceUrl": url,
            "image": pick_image_stub(title),
        })

    # -------------------------
    # MEME: weird headlines (public RSS)
    # every run is fine; your workflow schedule handles timing
    # -------------------------
    meme_entries = []
    for rss in sources.get("meme", {}).get("rss", []):
        meme_entries.extend(fetch_rss(rss)[:30])

    for e in meme_entries[:6]:
        url = e.get("link", "")
        if not url:
            continue
        pid = make_id("meme", url)
        if pid in existing_ids:
            continue

        t = parse_time(e) or now_utc()
        title = clean_text(e.get("title", ""))
        desc = clean_text(e.get("summary", ""))

        s = summarize_safe(title, desc, "MEME")
        items_new.append({
            "id": pid,
            "section": "MEME",
            "sectionLabel": "Not-So-Serious",
            "type": "MEME",
            "category": "WEIRD",
            "title": s["title"],
            "dek": s["dek"],
            "body": s["body"],
            "author": "Meme Bureau",
            "publishedAt": t.isoformat(timespec="seconds"),
            "sourceUrl": url,
            "image": pick_image_stub(title),
        })

    # -------------------------
    # Merge: newest first
    # Auto-archive old live items
    # -------------------------
    all_live = live.get("items", [])
    all_live.extend(items_new)

    # Sort by time desc
    all_live.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)

    # Keep live small (e.g., 40)
    LIVE_MAX = 40
    still_live = all_live[:LIVE_MAX]
    to_archive = all_live[LIVE_MAX:]

    # Add to archive (dedupe)
    arch_items = archive.get("items", [])
    arch_ids = {i["id"] for i in arch_items}
    for it in to_archive:
        if it["id"] not in arch_ids:
            arch_items.append(it)

    # Archive newest first, cap it
    arch_items.sort(key=lambda x: x.get("publishedAt", ""), reverse=True)
    ARCHIVE_MAX = 300
    arch_items = arch_items[:ARCHIVE_MAX]

    live_out = {"generatedAt": now_utc().isoformat(timespec="seconds"), "items": still_live}
    arch_out = {"items": arch_items}

    save_json("data/live.json", live_out)
    save_json("data/archive.json", arch_out)

    print(f"Generated: {len(items_new)} new items. Live={len(still_live)} Archive={len(arch_items)}")

if __name__ == "__main__":
    build_items()

