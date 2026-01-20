images.py# scripts/images.py
import urllib.parse

def pick_image(item):
    q = item.get("title", "news")
    q = urllib.parse.quote(q)
    return f"https://source.unsplash.com/1200x800/?{q}"
