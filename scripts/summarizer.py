# scripts/summarizer.py
def summarize_item(item):
    # Simple: compress raw text to ~140 chars
    raw = (item.get("raw") or item.get("title")).strip()
    dek = raw[:140].rsplit(" ", 1)[0] + "…" if len(raw) > 140 else raw
    body = f"{item['title']}\n\n{raw}\n\nSource: {item.get('sourceUrl','')}"
    return dek, body
