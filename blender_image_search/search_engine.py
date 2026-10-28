"""Search engine backend for Blender Image Search add-on."""
import os
import re
import json
import html
import urllib.request
import urllib.parse
import tempfile
import ssl

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def get_cache_dir():
    cache_base = os.path.join(tempfile.gettempdir(), "blender_image_search_cache")
    thumbs_dir = os.path.join(cache_base, "thumbs")
    full_dir = os.path.join(cache_base, "full")
    os.makedirs(thumbs_dir, exist_ok=True)
    os.makedirs(full_dir, exist_ok=True)
    return cache_base, thumbs_dir, full_dir

def clean_title(title: str) -> str:
    if not title:
        return "Image"
    # Remove Bing / HTML highlight unicode markers and tags
    cleaned = re.sub(r'[\ue000\ue001]', '', title)
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    cleaned = html.unescape(cleaned).strip()
    return cleaned[:80] if len(cleaned) > 80 else cleaned

def search_bing_web(query: str, count: int = 24) -> list:
    """Searches Bing Web Images without requiring an API key."""
    encoded_q = urllib.parse.quote(query)
    url = f"https://www.bing.com/images/search?q={encoded_q}&first=1&count={count}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()

    results = []
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        page_html = resp.read().decode("utf-8", errors="ignore")

    for idx, m in enumerate(re.finditer(r'class="iusc"[^>]+m="([^"]+)"', page_html)):
        if len(results) >= count:
            break
        try:
            raw_json = html.unescape(m.group(1))
            d = json.loads(raw_json)
            murl = d.get("murl")
            turl = d.get("turl")
            desc = clean_title(d.get("desc", d.get("t", f"Image {idx+1}")))
            if murl and turl:
                w = d.get("w", 0)
                h = d.get("h", 0)
                domain = urllib.parse.urlparse(murl).netloc
                results.append({
                    "id": f"img_{idx}",
                    "title": desc,
                    "full_url": murl,
                    "thumb_url": turl,
                    "width": int(w) if w else 0,
                    "height": int(h) if h else 0,
                    "source": domain
                })
        except Exception:
            continue
    return results

def search_wikimedia(query: str, count: int = 24) -> list:
    """Searches Wikimedia Commons (Public domain / CC licensed images)."""
    encoded_q = urllib.parse.quote(query)
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrnamespace=6&gsrsearch={encoded_q}&gsrlimit={count}&prop=imageinfo&iiprop=url|size&iiurlwidth=256&format=json"
    headers = {"User-Agent": "BlenderImageSearchAddon/1.0 (blender_user@example.com)"}
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()

    results = []
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8", errors="ignore"))

    pages = data.get("query", {}).get("pages", {})
    idx = 0
    for pid, page in pages.items():
        if len(results) >= count:
            break
        imageinfo = page.get("imageinfo", [])
        if not imageinfo:
            continue
        info = imageinfo[0]
        full_url = info.get("url")
        thumb_url = info.get("thumburl", full_url)
        raw_title = page.get("title", "").replace("File:", "").replace(".jpg", "").replace(".png", "")
        title = clean_title(raw_title)
        if full_url and thumb_url:
            results.append({
                "id": f"wiki_{idx}",
                "title": title,
                "full_url": full_url,
                "thumb_url": thumb_url,
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "source": "commons.wikimedia.org"
            })
            idx += 1
    return results

def search_google_custom_search(query: str, api_key: str, cx: str, count: int = 10) -> list:
    """Searches Google Images using official Google Custom Search JSON API."""
    if not api_key or not cx:
        raise ValueError("Google API Key and Search Engine ID (CX) are required. Configure them in Add-on Preferences.")

    encoded_q = urllib.parse.quote(query)
    num = max(1, min(10, count))
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={encoded_q}&searchType=image&num={num}"
    headers = {"User-Agent": USER_AGENT}
    req = urllib.request.Request(url, headers=headers)
    ctx = ssl.create_default_context()

    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results = []
    for idx, item in enumerate(data.get("items", [])):
        img_info = item.get("image", {})
        results.append({
            "id": f"google_{idx}",
            "title": clean_title(item.get("title", f"Google Image {idx+1}")),
            "full_url": item.get("link"),
            "thumb_url": img_info.get("thumbnailLink", item.get("link")),
            "width": img_info.get("width", 0),
            "height": img_info.get("height", 0),
            "source": item.get("displayLink", "google.com")
        })
    return results

def download_file(url: str, output_path: str, timeout: int = 15) -> bool:
    """Downloads an image from URL and writes to output_path."""
    try:
        headers = {"User-Agent": USER_AGENT}
        req = urllib.request.Request(url, headers=headers)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE  # For broader compatibility across arbitrary servers
        with urllib.request.urlopen(req, context=ctx, timeout=timeout) as resp:
            content = resp.read()
            if len(content) < 100:  # Invalid image response
                return False
            with open(output_path, "wb") as f:
                f.write(content)
        return True
    except Exception as e:
        return False
