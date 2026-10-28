"""Automatic Native Messaging Host and Browser Extension setup for AuxeRef.
Author: Auxerov
"""
import os
import stat
import json
import time
import subprocess
import bpy

EXTENSION_ID = "pplmekajjhbhhlhgpiplnghmmfoehmoi"
NATIVE_HOST_NAME = "com.auxerov.blender"
RECEIVER_SCRIPT_PATH = os.path.expanduser("~/.local/bin/blender_image_receiver.py")
INBOX_DIR = "/tmp/blender_open_inbox"

RECEIVER_SCRIPT_CONTENT = """#!/usr/bin/env python3
\"\"\"AuxeRef Native Messaging Host connecting Chrome/Firefox to Blender without any network ports.\"\"\"
import sys
import json
import struct
import os
import time

INBOX_DIR = "/tmp/blender_open_inbox"

def read_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    message_length = struct.unpack('@I', raw_length)[0]
    message_bytes = sys.stdin.buffer.read(message_length)
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

def ensure_native_host_installed():
    """Installs receiver script and native messaging manifests across all browser profiles."""
    os.makedirs(INBOX_DIR, exist_ok=True)

    bin_dir = os.path.dirname(RECEIVER_SCRIPT_PATH)
    os.makedirs(bin_dir, exist_ok=True)
    with open(RECEIVER_SCRIPT_PATH, "w", encoding="utf-8") as f:
        f.write(RECEIVER_SCRIPT_CONTENT)
    st = os.stat(RECEIVER_SCRIPT_PATH)
    os.chmod(RECEIVER_SCRIPT_PATH, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

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
        os.path.expanduser("~/.config/thorium"),
        os.path.expanduser("~/.config/chromium"),
        os.path.expanduser("~/.config/google-chrome"),
        os.path.expanduser("~/.config/BraveSoftware/Brave-Browser"),
        os.path.expanduser("~/.config/microsoft-edge")
    ]

    for cdir in chrome_dirs:
        nm_dir = os.path.join(cdir, "NativeMessagingHosts")
        os.makedirs(nm_dir, exist_ok=True)
        manifest_file = os.path.join(nm_dir, f"{NATIVE_HOST_NAME}.json")
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(chrome_manifest, f, indent=2)

    firefox_manifest = {
        "name": NATIVE_HOST_NAME,
        "description": "AuxeRef Image Bridge Native Host",
        "path": RECEIVER_SCRIPT_PATH,
        "type": "stdio",
        "allowed_extensions": [
            "auxeref@auxerov.local",
            "add-to-blender@auxerov.local"
        ]
    }
    ff_nm_dir = os.path.expanduser("~/.mozilla/native-messaging-hosts")
    os.makedirs(ff_nm_dir, exist_ok=True)
    with open(os.path.join(ff_nm_dir, f"{NATIVE_HOST_NAME}.json"), "w", encoding="utf-8") as f:
        json.dump(firefox_manifest, f, indent=2)

    return True

def detect_default_browser() -> dict:
    """Detects default browser name and family."""
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
    if any(k in raw_lower for k in ["firefox", "librewolf", "waterfox", "tor"]):
        return {"name": "Mozilla Firefox", "family": "firefox", "raw": raw}
    elif "thorium" in raw_lower:
        return {"name": "Thorium Browser", "family": "chromium", "raw": raw}
    elif "chrome" in raw_lower:
        return {"name": "Google Chrome", "family": "chromium", "raw": raw}
    elif "chromium" in raw_lower:
        return {"name": "Chromium", "family": "chromium", "raw": raw}
    elif "brave" in raw_lower:
        return {"name": "Brave Browser", "family": "chromium", "raw": raw}
    else:
        return {"name": "Chromium / Chrome", "family": "chromium", "raw": raw}

def auto_install_all(restart_browser: bool = False) -> tuple:
    """Configures browser flags and external extension registration so extension is loaded automatically."""
    ensure_native_host_installed()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ext_dir = os.path.join(base_dir, "extension_chrome")
    if not os.path.exists(ext_dir):
        ext_dir = "/home/auxerov/blender-image-search/extension"

    crx_path = os.path.join(base_dir, "extension.crx")
    if not os.path.exists(crx_path):
        crx_path = "/home/auxerov/blender-image-search/extension.crx"

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

    json_payload = {
        "external_crx": crx_path,
        "external_version": "2.4.0"
    }
    for browser_dir in [
        os.path.expanduser("~/.config/thorium"),
        os.path.expanduser("~/.config/chromium"),
        os.path.expanduser("~/.config/google-chrome"),
        os.path.expanduser("~/.config/BraveSoftware/Brave-Browser")
    ]:
        try:
            ext_folder = os.path.join(browser_dir, "External Extensions")
            os.makedirs(ext_folder, exist_ok=True)
            with open(os.path.join(ext_folder, f"{EXTENSION_ID}.json"), "w") as f:
                json.dump(json_payload, f, indent=2)
        except Exception:
            pass

    detected = detect_default_browser()

    if restart_browser:
        raw_cmd = detected.get("raw", "").replace(".desktop", "").strip()
        binary = raw_cmd if raw_cmd else "thorium-browser"
        try:
            subprocess.run(["pkill", "-TERM", "-f", "thorium|chrome|chromium"], check=False)
            time.sleep(1.0)
            subprocess.Popen([binary], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True, f"AuxeRef installed! {detected['name']} restarted."
        except Exception:
            return True, f"AuxeRef configured! Please restart {detected['name']}."

    return True, f"AuxeRef installed automatically for {detected['name']}!"
