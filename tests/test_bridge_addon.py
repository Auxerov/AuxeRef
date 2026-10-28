"""Automated test for native 'Open in Blender' bridge, Pinterest & Google search, and zero-port architecture."""
import os
import sys
import time
import json
import struct
import subprocess
import bpy

def run_tests():
    print("=" * 60)
    print(f"RUNNING NATIVE 'OPEN IN BLENDER' TESTS ON BLENDER {bpy.app.version_string}")
    print("=" * 60)

    # 1. Enable Add-on
    print("[1] Enabling addon 'blender_web_search'...")
    try:
        bpy.ops.preferences.addon_enable(module="blender_web_search")
        print("  -> Addon enabled successfully!")
    except Exception as e:
        print(f"FAILED to enable addon: {e}")
        sys.exit(1)

    # 2. Check Native Host setup
    print("[2] Verifying Native Messaging Host installation...")
    receiver_path = os.path.expanduser("~/.local/bin/blender_image_receiver.py")
    assert os.path.exists(receiver_path), f"Receiver script missing at {receiver_path}"
    assert os.access(receiver_path, os.X_OK), "Receiver script is not executable!"
    print("  -> Receiver script installed and executable.")

    chrome_manifest = os.path.expanduser("~/.config/thorium/NativeMessagingHosts/com.auxerov.blender.json")
    assert os.path.exists(chrome_manifest), "Chrome native host manifest missing"
    firefox_manifest = os.path.expanduser("~/.mozilla/native-messaging-hosts/com.auxerov.blender.json")
    assert os.path.exists(firefox_manifest), "Firefox native host manifest missing"
    print("  -> Native messaging manifests verified for both Chrome/Thorium and Firefox.")

    # 3. Verify Keymap registration
    print("[3] Verifying Turkish shortcut keymaps (< / \")...")
    from blender_web_search import addon_keymaps
    print(f"  -> Registered {len(addon_keymaps)} keymap items")
    assert len(addon_keymaps) >= 2, f"Expected at least 2 keymap items, got {len(addon_keymaps)}"
    types = [kmi.type for _, kmi in addon_keymaps]
    print(f"  -> Key types registered: {types}")
    assert "ACCENT_GRAVE" in types, "ACCENT_GRAVE keymap not registered!"
    assert "GRLESS" in types, "GRLESS keymap not registered!"

    # 4. Test Search operator with Pinterest & Google
    print("[4] Testing Search operator with Pinterest & Google...")
    wm = bpy.context.window_manager
    # Google Images search
    res = bpy.ops.wm.web_image_search(query="blender logo", engine="GOOGLE")
    assert "FINISHED" in res
    # Pinterest search
    res = bpy.ops.wm.web_image_search(query="game art concept", engine="PINTEREST")
    assert "FINISHED" in res
    print("  -> Both Google Images and Pinterest search operators executed successfully.")

    # 5. Generate base64 test image
    import zlib, base64
    def make_png_data_uri():
        def png_chunk(chunk_type, data):
            return struct.pack('>I', len(data)) + chunk_type + data + struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
        raw = bytearray()
        for y in range(16):
            raw.append(0)
            for x in range(16):
                raw.extend(b'\x30\x80\xe0\xff') # Blue RGBA
        header = b'\x89PNG\r\n\x1a\n'
        ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', 16, 16, 8, 6, 0, 0, 0))
        idat = png_chunk(b'IDAT', zlib.compress(bytes(raw)))
        iend = png_chunk(b'IEND', b'')
        png_bytes = header + ihdr + idat + iend
        return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")

    test_data_uri = make_png_data_uri()

    # 6. Simulate Browser Native Messaging invocation
    print("[6] Testing Browser -> Native Host invocation (stdin pipe)...")
    payload = {
        "url": test_data_uri,
        "title": "OneClickTestImage"
    }
    encoded = json.dumps(payload).encode("utf-8")
    native_input = struct.pack("@I", len(encoded)) + encoded

    proc = subprocess.Popen(
        [sys.executable, receiver_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate(input=native_input)
    assert proc.returncode == 0, f"Receiver script failed: {stderr}"
    
    # Check response from receiver
    resp_len = struct.unpack("@I", stdout[:4])[0]
    resp_data = json.loads(stdout[4:4+resp_len].decode("utf-8"))
    assert resp_data.get("status") == "ok"
    print(f"  -> Native host responded: {resp_data}")

    # 7. Check that item was placed in Blender inbox and process it
    print("[7] Checking Blender inbox processing...")
    inbox_dir = "/tmp/blender_open_inbox"
    inbox_files = [f for f in os.listdir(inbox_dir) if f.endswith(".json")]
    print(f"  -> Inbox contains {len(inbox_files)} files: {inbox_files}")
    assert len(inbox_files) > 0, "No item found in inbox!"

    # Trigger Blender inbox timer loop
    from blender_web_search import _check_inbox_timer
    _check_inbox_timer()

    # Verify inbox is cleaned
    remaining = [f for f in os.listdir(inbox_dir) if f.endswith(".json")]
    assert len(remaining) == 0, f"Inbox should be empty after processing, found {remaining}"

    # Verify Blender scene object was created
    created_obj = next((o for o in bpy.context.scene.objects if "OneClickTestImage" in o.name), None)
    assert created_obj is not None, "Image was not created in Blender scene!"
    print(f"  -> Verified scene object created in Blender: '{created_obj.name}' (type={created_obj.type})")

    # 8. Test Pinterest URL resolution logic
    print("[8] Testing Pinterest image download handling...")
    from blender_web_search import importer
    # Test clean real Pinterest image URL
    pin_test_url = "https://i.pinimg.com/originals/d5/3b/01/d53b014d86a6b6761bf649a0ed813c2b.png"
    downloaded_path = importer.download_or_decode_image(pin_test_url, "PinterestPin")
    assert os.path.exists(downloaded_path) and os.path.getsize(downloaded_path) > 1000
    print(f"  -> Pinterest image downloaded successfully to: {downloaded_path} ({os.path.getsize(downloaded_path)} bytes)")

    # 9. Clean unregister
    print("[9] Testing clean unregister...")
    bpy.ops.preferences.addon_disable(module="blender_web_search")
    print("  -> Addon unregistered cleanly.")

    print("=" * 60)
    print("ALL NATIVE 'OPEN IN BLENDER' TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
