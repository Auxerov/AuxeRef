"""Automatic Native Messaging Host and Browser Extension setup for AuxeRef.
Author: Auxerov
"""
import os
import stat
import json
import time
import shutil
import subprocess
import bpy

EXTENSION_ID = "pplmekajjhbhhlhgpiplnghmmfoehmoi"
FIREFOX_EXT_ID = "auxeref@auxerov.local"
NATIVE_HOST_NAME = "com.auxerov.blender"
RECEIVER_SCRIPT_PATH = os.path.expanduser("~/.local/bin/blender_image_receiver.py")
INBOX_DIR = "/tmp/blender_open_inbox"

RECEIVER_SCRIPT_CONTENT = """#!/usr/bin/env python3
\"\"\"AuxeRef Native Messaging Host connecting Chrome/Firefox/LibreWolf to Blender without network ports.\"\"\"
import sys
import json
import struct
import os
import time

INBOX_DIR = "/tmp/blender_open_inbox"

def read_exact(n):
    data = bytearray()
    while len(data) < n:
        chunk = sys.stdin.buffer.read(n - len(data))
        if not chunk:
            break
        data.extend(chunk)
    return bytes(data)

def read_message():
    raw_length = read_exact(4)
    if len(raw_length) < 4:
        return None
    message_length = struct.unpack('@I', raw_length)[0]
    message_bytes = read_exact(message_length)
    if len(message_bytes) < message_length:
        return None
    return json.loads(message_bytes.decode('utf-8'))

def send_message(message_content):
    encoded_content = json.dumps(message_content).encode('utf-8')
    encoded_length = struct.pack('@I', len(encoded_content))
    sys.stdout.buffer.write(encoded_length)
    sys.stdout.buffer.write(encoded_content)
    sys.stdout.buffer.flush()

def main():
    os.makedirs(INBOX_DIR, exist_ok=True)
    try:
        msg = read_message()
        if msg:
            ts = int(time.time() * 1000)
            target_path = os.path.join(INBOX_DIR, f"item_{ts}.json")
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(msg, f)
            send_message({"status": "ok", "message": "Saved to Blender inbox"})
    except Exception as e:
        send_message({"status": "error", "message": str(e)})

if __name__ == "__main__":
    main()
"""

def get_bundle_dir() -> str:
    """Returns the directory where extension files and packages reside."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return current_dir

def find_xpi_file() -> str:
    """Finds the Firefox/LibreWolf XPI package."""
    base = get_bundle_dir()
    candidates = [
        os.path.join(base, f"{FIREFOX_EXT_ID}.xpi"),
        os.path.join(base, "add_to_blender_firefox.xpi"),
        os.path.join(base, "..", f"{FIREFOX_EXT_ID}.xpi"),
        os.path.join(base, "..", "add_to_blender_firefox.xpi"),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.path.getsize(c) > 100:
            return os.path.abspath(c)
    return ""

def find_crx_file() -> str:
    """Finds the Chrome/Chromium CRX package."""
    base = get_bundle_dir()
    candidates = [
        os.path.join(base, "extension.crx"),
        os.path.join(base, "..", "extension.crx"),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.path.getsize(c) > 100:
            return os.path.abspath(c)
    return ""

def find_chrome_ext_dir() -> str:
    """Finds the unpacked Chrome extension directory."""
    base = get_bundle_dir()
    candidates = [
        os.path.join(base, "extension_chrome"),
        os.path.join(base, "extension"),
        os.path.join(base, "..", "extension_chrome"),
        os.path.join(base, "..", "extension"),
    ]
    for c in candidates:
        if os.path.isdir(c) and os.path.isfile(os.path.join(c, "manifest.json")):
            return os.path.abspath(c)
    return ""

def ensure_native_host_installed():
    """Installs receiver script and native messaging manifests across all browser profiles."""
    os.makedirs(INBOX_DIR, exist_ok=True)

    bin_dir = os.path.dirname(RECEIVER_SCRIPT_PATH)
    os.makedirs(bin_dir, exist_ok=True)
    with open(RECEIVER_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(RECEIVER_SCRIPT_CONTENT)
    st = os.stat(RECEIVER_SCRIPT_PATH)
    os.chmod(RECEIVER_SCRIPT_PATH, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # 1. Manifest for Chromium-based browsers
    chrome_manifest = {
        "name": NATIVE_HOST_NAME,
        "description": "AuxeRef Image Bridge Native Host",
        "path": RECEIVER_SCRIPT_PATH,
        "type": "stdio",
        "allowed_origins": [
            f"chrome-extension://{EXTENSION_ID}/"
        ]
    }

    chrome_dirs = [
        os.path.expanduser("~/.config/google-chrome"),
        os.path.expanduser("~/.config/google-chrome-beta"),
        os.path.expanduser("~/.config/chromium"),
        os.path.expanduser("~/.config/thorium"),
        os.path.expanduser("~/.config/BraveSoftware/Brave-Browser"),
        os.path.expanduser("~/.config/microsoft-edge"),
        os.path.expanduser("~/.config/vivaldi"),
        os.path.expanduser("~/.config/opera"),
    ]

    for cdir in chrome_dirs:
        try:
            nm_dir = os.path.join(cdir, "NativeMessagingHosts")
            os.makedirs(nm_dir, exist_ok=True)
            manifest_file = os.path.join(nm_dir, f"{NATIVE_HOST_NAME}.json")
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(chrome_manifest, f, indent=2)
        except Exception:
            pass

    # 2. Manifest for Firefox / LibreWolf based browsers
    firefox_manifest = {
        "name": NATIVE_HOST_NAME,
        "description": "AuxeRef Image Bridge Native Host",
        "path": RECEIVER_SCRIPT_PATH,
        "type": "stdio",
        "allowed_extensions": [
            FIREFOX_EXT_ID,
            "add-to-blender@auxerov.local"
        ]
    }

    ff_dirs = [
        os.path.expanduser("~/.librewolf/native-messaging-hosts"),
        os.path.expanduser("~/.config/librewolf/native-messaging-hosts"),
        os.path.expanduser("~/.mozilla/native-messaging-hosts"),
        os.path.expanduser("~/.waterfox/native-messaging-hosts"),
        os.path.expanduser("~/.floorp/native-messaging-hosts"),
    ]

    for fdir in ff_dirs:
        try:
            os.makedirs(fdir, exist_ok=True)
            with open(os.path.join(fdir, f"{NATIVE_HOST_NAME}.json"), "w", encoding="utf-8") as f:
                json.dump(firefox_manifest, f, indent=2)
        except Exception:
            pass

    return True

def install_firefox_extension() -> int:
    """Installs the .xpi extension directly into LibreWolf and Firefox profiles and disables signature enforcement."""
    # 1. Ensure LibreWolf overrides enable unsigned extensions
    lw_overrides_path = os.path.expanduser("~/.config/librewolf/librewolf.overrides.cfg")
    pref_block = (
        "\n// ==============================================================================\n"
        "// AuxeRef & Unsigned Extensions Support\n"
        "// ==============================================================================\n"
        'defaultPref("xpinstall.signatures.required", false);\n'
        'pref("xpinstall.signatures.required", false);\n'
        'defaultPref("extensions.langpacks.signatures.required", false);\n'
        'defaultPref("extensions.autoDisableScopes", 0);\n'
        'defaultPref("extensions.startupScanScopes", 15);\n'
        'defaultPref("extensions.enabledScopes", 15);\n'
    )
    user_js_block = (
        "\n// AuxeRef & Unsigned Extensions Support\n"
        'user_pref("xpinstall.signatures.required", false);\n'
        'user_pref("extensions.langpacks.signatures.required", false);\n'
        'user_pref("extensions.autoDisableScopes", 0);\n'
        'user_pref("extensions.startupScanScopes", 15);\n'
        'user_pref("extensions.enabledScopes", 15);\n'
    )

    try:
        if os.path.exists(lw_overrides_path):
            with open(lw_overrides_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "xpinstall.signatures.required" not in content:
                with open(lw_overrides_path, "a", encoding="utf-8") as f:
                    f.write(pref_block)
        else:
            os.makedirs(os.path.dirname(lw_overrides_path), exist_ok=True)
            with open(lw_overrides_path, "w", encoding="utf-8") as f:
                f.write(pref_block)
    except Exception as e:
        print(f"[AuxeRef] Error updating librewolf.overrides.cfg: {e}")

    xpi_src = find_xpi_file()
    if not xpi_src or not os.path.exists(xpi_src):
        return 0

    roots = [
        os.path.expanduser("~/.config/librewolf/librewolf"),
        os.path.expanduser("~/.librewolf"),
        os.path.expanduser("~/.mozilla/firefox"),
        os.path.expanduser("~/.waterfox"),
        os.path.expanduser("~/.floorp"),
    ]

    installed_count = 0
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            for entry in os.scandir(root):
                if entry.is_dir():
                    profile_indicators = ["extensions", "prefs.js", "user.js", "times.json", "compatibility.ini"]
                    is_profile = any(os.path.exists(os.path.join(entry.path, ind)) for ind in profile_indicators)
                    if is_profile or "default" in entry.name:
                        # Append unsigned preference block to user.js
                        ujs_path = os.path.join(entry.path, "user.js")
                        try:
                            ujs_content = ""
                            if os.path.exists(ujs_path):
                                with open(ujs_path, "r", encoding="utf-8") as f:
                                    ujs_content = f.read()
                            if "xpinstall.signatures.required" not in ujs_content:
                                with open(ujs_path, "a", encoding="utf-8") as f:
                                    f.write(user_js_block)
                        except Exception:
                            pass

                        ext_dir = os.path.join(entry.path, "extensions")
                        os.makedirs(ext_dir, exist_ok=True)
                        dest_file = os.path.join(ext_dir, f"{FIREFOX_EXT_ID}.xpi")
                        shutil.copy2(xpi_src, dest_file)
                        installed_count += 1
        except Exception as e:
            print(f"[AuxeRef] Firefox profile scan error: {e}")

    return installed_count

def install_chromium_extension() -> bool:
    """Configures browser flags and external extensions for Chromium-based browsers."""
    ext_dir = find_chrome_ext_dir()
    crx_path = find_crx_file()

    if ext_dir:
        flags_line = f"--load-extension={ext_dir}"
        for flags_file in [
            os.path.expanduser("~/.config/thorium-flags.conf"),
            os.path.expanduser("~/.config/chromium-flags.conf"),
            os.path.expanduser("~/.config/chrome-flags.conf"),
        ]:
            try:
                lines = []
                if os.path.exists(flags_file):
                    with open(flags_file, "r") as f:
                        for line in f.read().splitlines():
                            if not line.startswith("--load-extension"):
                                lines.append(line)
                lines.append(flags_line)
                with open(flags_file, "w") as f:
                    f.write("\n".join(lines).strip() + "\n")
            except Exception:
                pass

    if crx_path:
        json_payload = {
            "external_crx": crx_path,
            "external_version": "1.0.0"
        }
        for browser_dir in [
            os.path.expanduser("~/.config/thorium"),
            os.path.expanduser("~/.config/chromium"),
            os.path.expanduser("~/.config/google-chrome"),
            os.path.expanduser("~/.config/BraveSoftware/Brave-Browser"),
            os.path.expanduser("~/.config/microsoft-edge"),
        ]:
            try:
                ext_folder = os.path.join(browser_dir, "External Extensions")
                os.makedirs(ext_folder, exist_ok=True)
                with open(os.path.join(ext_folder, f"{EXTENSION_ID}.json"), "w") as f:
                    json.dump(json_payload, f, indent=2)
            except Exception:
                pass

    return True

def detect_default_browser() -> dict:
    """Detects default browser name, family, and binary executable."""
    raw = ""
    try:
        raw = subprocess.check_output(["xdg-settings", "get", "default-web-browser"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        pass

    if not raw:
        try:
            raw = subprocess.check_output(["xdg-mime", "query", "default", "x-scheme-handler/http"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            pass

    if not raw:
        raw = os.environ.get("BROWSER", "")

    raw_lower = raw.lower()
    if "librewolf" in raw_lower:
        return {"name": "LibreWolf", "family": "firefox", "raw": raw, "binary": "librewolf"}
    elif "floorp" in raw_lower:
        return {"name": "Floorp", "family": "firefox", "raw": raw, "binary": "floorp"}
    elif "waterfox" in raw_lower:
        return {"name": "Waterfox", "family": "firefox", "raw": raw, "binary": "waterfox"}
    elif "firefox" in raw_lower or "tor" in raw_lower:
        return {"name": "Mozilla Firefox", "family": "firefox", "raw": raw, "binary": "firefox"}
    elif "thorium" in raw_lower:
        return {"name": "Thorium Browser", "family": "chromium", "raw": raw, "binary": "thorium-browser"}
    elif "chrome" in raw_lower:
        return {"name": "Google Chrome", "family": "chromium", "raw": raw, "binary": "google-chrome"}
    elif "chromium" in raw_lower:
        return {"name": "Chromium", "family": "chromium", "raw": raw, "binary": "chromium"}
    elif "brave" in raw_lower:
        return {"name": "Brave Browser", "family": "chromium", "raw": raw, "binary": "brave-browser"}
    else:
        return {"name": "Web Browser", "family": "unknown", "raw": raw, "binary": "xdg-open"}

def auto_install_all(restart_browser: bool = False) -> tuple:
    """Configures browser flags, profiles, and native host across all browsers."""
    ensure_native_host_installed()
    ff_installed = install_firefox_extension()
    install_chromium_extension()

    detected = detect_default_browser()

    if restart_browser:
        binary = detected.get("binary", "xdg-open")
        try:
            kill_targets = "librewolf|firefox|thorium|chrome|chromium|brave"
            subprocess.run(["pkill", "-TERM", "-f", kill_targets], check=False)
            time.sleep(0.8)
            subprocess.Popen([binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"AuxeRef installed! {detected['name']} restarted with unsigned extension support."
        except Exception:
            pass

    if detected["family"] == "firefox":
        return True, f"AuxeRef configured for {detected['name']}! Please restart {detected['name']} to activate."

    return True, f"AuxeRef configured successfully for {detected['name']}!"
