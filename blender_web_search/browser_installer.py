"""Automatic browser detection and extension installation for Blender Image Search."""
import os
import sys
import shutil
import subprocess
import webbrowser
import bpy

EXTENSION_ID = "pplmekajjhbhhlhgpiplnghmmfoehmoi"

def detect_default_browser() -> dict:
    """Detects the operating system's default web browser."""
    raw = ""
    # 1. Try xdg-settings on Linux
    try:
        raw = subprocess.check_output(
            ["xdg-settings", "get", "default-web-browser"],
            stderr=subprocess.DEVNULL
        ).decode("utf-8").strip()
    except Exception:
        pass

    # 2. Try xdg-mime query
    if not raw:
        try:
            raw = subprocess.check_output(
                ["xdg-mime", "query", "default", "x-scheme-handler/http"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
        except Exception:
            pass

    # 3. Environment variable $BROWSER
    if not raw:
        raw = os.environ.get("BROWSER", "")

    # 4. Fallback search installed binaries
    if not raw:
        for candidate in ["thorium-browser", "google-chrome", "chromium", "firefox", "brave-browser"]:
            if shutil.which(candidate):
                raw = candidate
                break

    raw_lower = raw.lower()
    
    # Classification
    if any(k in raw_lower for k in ["firefox", "librewolf", "waterfox", "tor"]):
        return {
            "id": "firefox",
            "name": "Mozilla Firefox",
            "family": "firefox",
            "target": "FIREFOX",
            "raw": raw
        }
    elif "thorium" in raw_lower:
        return {
            "id": "thorium",
            "name": "Thorium Browser",
            "family": "chromium",
            "target": "CHROME",
            "raw": raw,
            "config_dirs": [os.path.expanduser("~/.config/thorium")]
        }
    elif "google-chrome" in raw_lower or "chrome" in raw_lower:
        return {
            "id": "chrome",
            "name": "Google Chrome",
            "family": "chromium",
            "target": "CHROME",
            "raw": raw,
            "config_dirs": [os.path.expanduser("~/.config/google-chrome")]
        }
    elif "chromium" in raw_lower:
        return {
            "id": "chromium",
            "name": "Chromium",
            "family": "chromium",
            "target": "CHROME",
            "raw": raw,
            "config_dirs": [os.path.expanduser("~/.config/chromium")]
        }
    elif "brave" in raw_lower:
        return {
            "id": "brave",
            "name": "Brave Browser",
            "family": "chromium",
            "target": "CHROME",
            "raw": raw,
            "config_dirs": [os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")]
        }
    else:
        # Default Chromium family
        return {
            "id": "chromium_generic",
            "name": "Chromium / Chrome",
            "family": "chromium",
            "target": "CHROME",
            "raw": raw or "unknown",
            "config_dirs": [
                os.path.expanduser("~/.config/thorium"),
                os.path.expanduser("~/.config/chromium"),
                os.path.expanduser("~/.config/google-chrome")
            ]
        }

def install_extension(target: str = "AUTO") -> tuple:
    """Installs or configures the extension for the requested or default browser."""
    detected = detect_default_browser()
    actual_target = detected["target"] if target == "AUTO" else target

    base_dir = os.path.dirname(os.path.abspath(__file__))
    chrome_ext_dir = os.path.join(base_dir, "extension_chrome")
    firefox_ext_dir = os.path.join(base_dir, "extension_firefox")
    firefox_manifest = os.path.join(firefox_ext_dir, "manifest.json")
    crx_path = os.path.join(base_dir, "extension.crx")

    # If directories aren't in addon dir, check parent repo dir
    if not os.path.exists(chrome_ext_dir):
        parent_dir = os.path.dirname(base_dir)
        chrome_ext_dir = os.path.join(parent_dir, "extension")
        firefox_ext_dir = os.path.join(parent_dir, "extension_firefox")
        firefox_manifest = os.path.join(firefox_ext_dir, "manifest.json")
        crx_path = os.path.join(parent_dir, "extension.crx")

    if actual_target == "CHROME":
        # 1. Setup External Extensions JSON for all Chromium profiles found
        candidates = [
            os.path.expanduser("~/.config/thorium"),
            os.path.expanduser("~/.config/chromium"),
            os.path.expanduser("~/.config/google-chrome"),
            os.path.expanduser("~/.config/BraveSoftware/Brave-Browser"),
            os.path.expanduser("~/.config/microsoft-edge")
        ]
        
        json_content = f'{{\n  "external_crx": "{crx_path}",\n  "external_version": "1.0.0"\n}}\n'
        configured_paths = []
        for cdir in candidates:
            if os.path.exists(cdir):
                ext_dir = os.path.join(cdir, "External Extensions")
                os.makedirs(ext_dir, exist_ok=True)
                json_file = os.path.join(ext_dir, f"{EXTENSION_ID}.json")
                try:
                    with open(json_file, "w") as f:
                        f.write(json_content)
                    configured_paths.append(cdir)
                except Exception:
                    pass

        # 2. Copy the unpacked extension folder path to clipboard
        try:
            bpy.context.window_manager.clipboard = chrome_ext_dir
        except Exception:
            pass

        # 3. Open interactive setup page in default browser
        from . import bridge_server
        port = bridge_server.get_active_port()
        setup_url = f"http://127.0.0.1:{port}/setup?browser=chrome&name={detected['name']}"
        try:
            webbrowser.open_new_tab(setup_url)
        except Exception:
            pass

        browser_name = detected["name"]
        msg = f"Configured for {browser_name}. Setup page opened in browser!"
        return True, msg

    else:  # FIREFOX
        # 1. Copy manifest path to clipboard for about:debugging
        try:
            bpy.context.window_manager.clipboard = firefox_manifest
        except Exception:
            pass

        # 2. Open interactive setup page in browser
        from . import bridge_server
        port = bridge_server.get_active_port()
        setup_url = f"http://127.0.0.1:{port}/setup?browser=firefox"
        try:
            webbrowser.open_new_tab(setup_url)
        except Exception:
            pass

        return True, "Configured for Mozilla Firefox. Setup page opened in browser!"
