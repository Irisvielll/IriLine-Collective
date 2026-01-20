# scripts/store.py
import json, os

def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_store(live_path, archive_path):
    live = load_json(live_path, {"generatedAt":"", "items":[]})
    archive = load_json(archive_path, {"items":[]})
    return live, archive

def save_store(live_path, archive_path, live, archive):
    save_json(live_path, live)
    save_json(archive_path, archive)

def merge_live_archive(live, archive, new_items):
    live_items = live.get("items", [])
    arch_items = archive.get("items", [])

    seen = {i["id"] for i in live_items} | {i["id"] for i in arch_items}
    for it in new_items:
        if it["id"] not in seen:
            live_items.append(it)
            seen.add(it["id"])

    live_items.sort(key=lambda x: x.get("publishedAt",""), reverse=True)

    LIVE_MAX = 40
    keep = live_items[:LIVE_MAX]
    overflow = live_items[LIVE_MAX:]

    arch_seen = {i["id"] for i in arch_items}
    for it in overflow:
        if it["id"] not in arch_seen:
            arch_items.append(it)
            arch_seen.add(it["id"])

    arch_items.sort(key=lambda x: x.get("publishedAt",""), reverse=True)
    archive = {"items": arch_items[:300]}
    live = {"generatedAt": live.get("generatedAt",""), "items": keep}
    return live, archive
