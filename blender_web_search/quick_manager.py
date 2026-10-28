"""Persistent Quick References storage and manager for AuxeRef.
Author: Auxerov
"""
import os
import json

QUICK_FILE = os.path.expanduser("~/.config/blender/auxeref_quick_references.json")

def load_quick_references() -> list:
    """Loads saved quick reference items from disk."""
    if os.path.exists(QUICK_FILE):
        try:
            with open(QUICK_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)
                return [it for it in items if os.path.exists(it.get("filepath", ""))]
        except Exception:
            return []
    return []

def save_quick_references(items: list):
    """Saves quick reference items to disk."""
    try:
        os.makedirs(os.path.dirname(QUICK_FILE), exist_ok=True)
        with open(QUICK_FILE, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
    except Exception as e:
        print(f"[AuxeRef] Error saving quick references: {e}")

def add_quick_reference(title: str, url: str, filepath: str) -> list:
    """Adds a new reference to the quick list and persists it."""
    items = load_quick_references()
    items = [it for it in items if it.get("url") != url and it.get("filepath") != filepath]
    
    clean_title = (title.strip() if title else "Reference")[:32]
    items.insert(0, {
        "title": clean_title or "Reference",
        "url": url,
        "filepath": filepath
    })
    items = items[:30]
    save_quick_references(items)
    return items

def update_quick_reference(index: int, title: str = "", url: str = "") -> list:
    """Updates title and/or web URL of a quick reference item."""
    items = load_quick_references()
    if 0 <= index < len(items):
        if title:
            items[index]["title"] = title.strip()[:48]
        if url:
            items[index]["url"] = url.strip()
        save_quick_references(items)
    return items

def remove_quick_reference(index: int) -> list:
    """Removes an item by index."""
    items = load_quick_references()
    if 0 <= index < len(items):
        items.pop(index)
        save_quick_references(items)
    return items

def clear_quick_references() -> list:
    """Clears all saved quick references."""
    save_quick_references([])
    return []
