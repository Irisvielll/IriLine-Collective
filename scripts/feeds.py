# scripts/feeds.py
import feedparser
from dateutil import parser as dtparser
from datetime import datetime, timezone, timedelta
import re

def clean(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", s).strip()

def parse_time(entry):
    for key in ("published", "updated"):
        if key in entry:
            try:
                return dtparser.parse(entry[key]).astimezone(timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)

def make_item(section, type_, category, entry):
    url = entry.get("link", "")
    title = clean(entry.get("title", ""))
    summary = clean(entry.get("summary", ""))

    t = parse_time(entry)
    return {
        "id": f"{section.lower()}_{abs(hash(url))%10**10}",
        "section": section,               # LATEST / SPORTS / MEME
        "type": type_,                    # REAL / MEME
        "category": category,             # WORLD / INJURY / WEIRD...
        "title": title[:140],
        "raw": summary,                   # raw text before summarization
        "publishedAt": t.isoformat(timespec="seconds"),
        "sourceUrl": url,
        "author": "IriLine Desk"
    }

def fetch_rss(url, limit=25):
    f = feedparser.parse(url)
    return (f.entries or [])[:limit]

def fetch_latest_items(cfg):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=90)  # “freshest available”
    items = []
    for rss in cfg.get("rss", []):
        for e in fetch_rss(rss, 30):
            t = parse_time(e)
            if t < cutoff:
                continue
            items.append(make_item("LATEST", "REAL", "WORLD", e))
    return items[:12]

def fetch_sports_items(cfg):
    entries = []
    for rss in cfg.get("rss", []):
        entries += fetch_rss(rss, 50)

    injury_kw = [k.lower() for k in cfg.get("keywords_injury", [])]
    def is_injury(e):
        text = (clean(e.get("title","")) + " " + clean(e.get("summary",""))).lower()
        return any(k in text for k in injury_kw)

    injuries = [e for e in entries if is_injury(e)]
    chosen = injuries[:8]

    if not chosen:
        # fallback basketball
        for e in entries:
            text = (clean(e.get("title","")) + " " + clean(e.get("summary",""))).lower()
            if "nba" in text or "basketball" in text:
                chosen.append(e)
            if len(chosen) >= 8:
                break

    return [make_item("SPORTS", "REAL", "INJURY" if is_injury(e) else "BASKETBALL", e) for e in chosen]

def fetch_meme_items(cfg):
    items = []
    for rss in cfg.get("rss", []):
        for e in fetch_rss(rss, 20):
            items.append(make_item("MEME", "MEME", "WEIRD", e))
    return items[:10]
