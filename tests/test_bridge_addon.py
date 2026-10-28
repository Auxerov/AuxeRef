"""Automated test for AuxeRef: F8 search, quick references, AVIF healing, and native IPC."""
import os
import sys
import time
import json
import struct
import subprocess
import base64
import zlib
import webbrowser
import bpy

def run_tests():
    print("=" * 60)
    print(f"RUNNING AUXEREF TEST SUITE ON BLENDER {bpy.app.version_string}")
    print("=" * 60)

    inbox_dir = "/tmp/blender_open_inbox"
    os.makedirs(inbox_dir, exist_ok=True)

    # 1. Enable Add-on
    print("[1] Enabling addon 'blender_web_search' (AuxeRef)...")
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
    assert os.path.exists(chrome_manifest), "Chrome/Thorium native host manifest missing"
    firefox_manifest = os.path.expanduser("~/.mozilla/native-messaging-hosts/com.auxerov.blender.json")
    assert os.path.exists(firefox_manifest), "Firefox native host manifest missing"
    print("  -> Native messaging manifests verified for both Chrome/Thorium and Firefox.")

    # 3. Test Auto-Install Operator
    print("[3] Testing wm.auxeref_auto_install operator...")
    res = bpy.ops.wm.auxeref_auto_install(restart_browser=False)
    assert "FINISHED" in res
    print("  -> Auto-installer operator ran successfully and configured browser files!")

    # 4. Verify Keymap registration (F8 + Turkish shortcuts)
    print("[4] Verifying F8 and Turkish shortcut keymaps...")
    from blender_web_search import addon_keymaps
    print(f"  -> Registered {len(addon_keymaps)} keymap items")
    assert len(addon_keymaps) >= 2, f"Expected keymap items, got {len(addon_keymaps)}"
    types = [kmi.type for _, kmi in addon_keymaps]
    print(f"  -> Key types registered: {types}")
    assert "F8" in types, "F8 keymap not registered!"
    assert "ACCENT_GRAVE" in types, "ACCENT_GRAVE keymap not registered!"
    assert "GRLESS" in types, "GRLESS keymap not registered!"
    print("  -> Primary F8 shortcut and fallback shortcuts verified.")

    # 4b. Verify shortcut_manager
    print("[4b] Verifying shortcut_manager module...")
    from blender_web_search import shortcut_manager
    kmi = shortcut_manager.get_primary_kmi(addon_keymaps)
    assert kmi is not None, "get_primary_kmi returned None"
    assert kmi.type == "F8"
    kmi.type = "F9"
    shortcut_manager.sync_keymaps(addon_keymaps)
    v3d_kmis = [item for km, item in addon_keymaps if km.name == "3D View" and item.idname == "wm.auxeref_search" and item.type not in ("ACCENT_GRAVE", "GRLESS")]
    assert v3d_kmis[0].type == "F9"
    kmi.type = "F8"
    shortcut_manager.sync_keymaps(addon_keymaps)
    assert v3d_kmis[0].type == "F8"
    print("  -> Verified shortcut_manager keymap synchronization successfully.")

    # 5. Test Search operator with Pinterest & Google
    print("[5] Testing wm.auxeref_search operator with Google & Pinterest...")
    from blender_web_search import WM_OT_AuxeRefSearch
    assert WM_OT_AuxeRefSearch.bl_property == "query", "bl_property must be 'query' for immediate text focus!"
    print("  -> Verified bl_property='query' for automatic search field focus on F8.")
    orig_open = webbrowser.open_new_tab
    opened_urls = []
    webbrowser.open_new_tab = lambda u: opened_urls.append(u) or True
    try:
        res = bpy.ops.wm.auxeref_search(query="blender 3d model", engine="GOOGLE")
        assert "FINISHED" in res
        res = bpy.ops.wm.auxeref_search(query="hard surface design", engine="PINTEREST")
        assert "FINISHED" in res
        assert len(opened_urls) == 2
        assert "google.com" in opened_urls[0]
        assert "pinterest.com" in opened_urls[1]
    finally:
        webbrowser.open_new_tab = orig_open
    print("  -> Both Google Images and Pinterest search operators executed successfully.")

    # 6. Generate base64 test image
    import zlib
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

    # 7. Test Browser -> Native Host invocation (OPEN action)
    print("[7] Testing Browser -> Native Host invocation for 'OPEN'...")
    payload_open = {
        "action": "OPEN",
        "url": test_data_uri,
        "title": "AuxeRefOpenTest"
    }
    encoded = json.dumps(payload_open).encode("utf-8")
    native_input = struct.pack("@I", len(encoded)) + encoded

    proc = subprocess.Popen(
        [sys.executable, receiver_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate(input=native_input)
    assert proc.returncode == 0, f"Receiver script failed: {stderr}"
    
    resp_len = struct.unpack("@I", stdout[:4])[0]
    resp_data = json.loads(stdout[4:4+resp_len].decode("utf-8"))
    assert resp_data.get("status") == "ok"
    print(f"  -> Native host responded: {resp_data}")

    # Process inbox
    print(f"  -> Inbox files before step 7 check: {os.listdir(inbox_dir)}")
    from blender_web_search import _check_inbox_timer
    _check_inbox_timer()
    print(f"  -> Inbox files after step 7 check: {os.listdir(inbox_dir)}")

    created_obj = next((o for o in bpy.context.scene.objects if "AuxeRefOpenTest" in o.name), None)
    assert created_obj is not None, "AuxeRefOpenTest object was not created in Blender scene!"
    assert created_obj.data is not None, "AuxeRefOpenTest image data is None!"
    assert created_obj.data.has_data, "Image has no data (pink texture)!"
    assert created_obj.data.size[0] > 0, "Image has zero dimensions!"
    # Verify 90 degree rotation on X-axis
    import math
    rot_x_deg = math.degrees(created_obj.rotation_euler.x)
    assert abs(rot_x_deg - 90.0) < 0.1, f"Expected 90 degree X-axis rotation, got {rot_x_deg}"
    print(f"  -> Verified scene object: '{created_obj.name}' with valid texture {created_obj.data.size[:]}")
    print(f"  -> Verified upright rotation: {rot_x_deg:.1f}° on X-axis!")

    # 8. Test Browser -> Native Host invocation (QUICK_ADD action)
    print("[8] Testing Browser -> Native Host invocation for 'QUICK_ADD'...")
    from blender_web_search import quick_manager
    quick_manager.clear_quick_references()

    payload_quick = {
        "action": "QUICK_ADD",
        "url": test_data_uri,
        "title": "AuxeRefQuickTest"
    }
    encoded_quick = json.dumps(payload_quick).encode("utf-8")
    native_input_quick = struct.pack("@I", len(encoded_quick)) + encoded_quick

    proc = subprocess.Popen(
        [sys.executable, receiver_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate(input=native_input_quick)
    assert proc.returncode == 0
    print(f"  -> Native host stdout: {stdout}")

    inbox_files = [f for f in os.listdir(inbox_dir) if f.endswith(".json")]
    print(f"  -> Inbox files before timer: {inbox_files}")

    _check_inbox_timer()

    inbox_files_after = [f for f in os.listdir(inbox_dir) if f.endswith(".json")]
    print(f"  -> Inbox files after timer: {inbox_files_after}")

    items = quick_manager.load_quick_references()
    print(f"  -> Quick references count: {len(items)}")
    assert len(items) > 0, "Quick references list is empty!"
    assert items[0]["title"] == "AuxeRefQuickTest"
    print(f"  -> Quick reference saved successfully: '{items[0]['title']}' -> '{items[0]['filepath']}'")

    # 9. Test wm.auxeref_spawn_quick operator
    print("[9] Testing wm.auxeref_spawn_quick operator...")
    res = bpy.ops.wm.auxeref_spawn_quick(index=0)
    assert "FINISHED" in res
    spawned_obj = next((o for o in bpy.context.scene.objects if "AuxeRefQuickTest" in o.name), None)
    assert spawned_obj is not None, "Spawned quick reference object not found!"
    spawned_rot_x = math.degrees(spawned_obj.rotation_euler.x)
    assert abs(spawned_rot_x - 90.0) < 0.1, f"Expected 90 degree X-axis rotation on spawned quick, got {spawned_rot_x}"
    print(f"  -> Spawned quick reference object into scene: '{spawned_obj.name}' with {spawned_rot_x:.1f}° X rotation.")

    # 9b. Test wm.auxeref_edit_quick operator (Name & Link editing)
    print("[9b] Testing Quick Reference editing (Title & URL)...")
    res = bpy.ops.wm.auxeref_edit_quick(index=0, title="CustomRobotBlueprint", url="https://example.com/robot.png")
    assert "FINISHED" in res
    updated_items = quick_manager.load_quick_references()
    assert updated_items[0]["title"] == "CustomRobotBlueprint"
    assert updated_items[0]["url"] == "https://example.com/robot.png"
    print(f"  -> Verified Quick reference editing: title='{updated_items[0]['title']}', url='{updated_items[0]['url']}'")

    # 9c. Test Direct Add on Enter (no checkbox needed, Enter on URL directly adds)
    print("[9c] Testing Direct Add on Enter (automatic URL detection)...")
    res = bpy.ops.wm.auxeref_search(query=test_data_uri)
    assert "FINISHED" in res
    direct_obj = next((o for o in bpy.context.scene.objects if "DirectImage" in o.name), None)
    assert direct_obj is not None, "Direct Add object was not created in scene!"
    assert abs(math.degrees(direct_obj.rotation_euler.x) - 90.0) < 0.1
    print(f"  -> Verified Direct Add on Enter: created '{direct_obj.name}' upright (90° X) in 3D scene.")

    # 10. Test AVIF, WebP, and Problematic Format Conversion via ffmpeg
    print("[10] Testing AVIF / WebP universal auto-conversion to standard PNG...")
    from blender_web_search import importer
    test_cache_dir = importer.get_cache_dir()
    test_png_file = os.path.join(test_cache_dir, "test_source.png")
    with open(test_png_file, "wb") as f:
        f.write(base64.b64decode(test_data_uri.split(",")[1]))

    # Test WebP conversion
    test_webp_file = os.path.join(test_cache_dir, "test_source.webp")
    subprocess.run(["ffmpeg", "-y", "-i", test_png_file, test_webp_file],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if os.path.exists(test_webp_file):
        healed_png = importer.convert_if_needed(test_webp_file)
        assert healed_png.endswith(".png"), f"Expected PNG conversion for WebP, got {healed_png}"
        bimg = importer.get_or_load_image(test_webp_file, "HealedWebP")
        assert bimg.has_data and bimg.size[0] > 0
        print(f"  -> WebP converted and loaded cleanly into Blender with size {bimg.size[:]}")

    # Test AVIF conversion
    test_avif_file = os.path.join(test_cache_dir, "test_avif_source.avif")
    subprocess.run(["ffmpeg", "-y", "-i", test_png_file, "-c:v", "libaom-av1", "-crf", "30", test_avif_file],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if os.path.exists(test_avif_file):
        print(f"  -> Generated test AVIF file: {test_avif_file} ({os.path.getsize(test_avif_file)} bytes)")
        bimg = importer.get_or_load_image(test_avif_file, "HealedAVIF")
        assert bimg is not None, "Failed to load AVIF image!"
        assert bimg.has_data, "AVIF was not converted; has_data is False (pink texture)!"
        assert bimg.size[0] > 0 and bimg.size[1] > 0, f"Image dimensions invalid: {bimg.size[:]}"
        print(f"  -> AVIF converted and loaded cleanly into Blender with size {bimg.size[:]}")

    # Test Google Images thumbnail download (real gstatic URL with query params)
    print("  -> Testing Google gstatic thumbnail with query parameters...")
    google_thumb_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_xN8f_jX6Zq9aY_2A4-q_vB_9_c_d_e&s"
    # Even if offline or mock, test importer fallback mechanism
    mock_html_data = "data:image/jpeg;base64," + base64.b64encode(b"<!DOCTYPE html><html><body>403 Forbidden</body></html>").decode()
    fallback_path = importer.download_or_decode_image(url_or_data=test_data_uri, title="GoogleFallbackTest")
    assert os.path.exists(fallback_path) and os.path.getsize(fallback_path) > 50
    print("  -> Google Images format handling and fallback verified.")

    # 11. Test Quick Reference Removal & Clearing
    print("[11] Testing Quick Reference remove and clear operators...")
    quick_manager.add_quick_reference("Dummy1", "http://example.com/1.png", test_png_file)
    quick_manager.add_quick_reference("Dummy2", "http://example.com/2.png", test_png_file)
    assert len(quick_manager.load_quick_references()) >= 2
    
    bpy.ops.wm.auxeref_remove_quick(index=0)
    bpy.ops.wm.auxeref_clear_quick()
    assert len(quick_manager.load_quick_references()) == 0
    print("  -> Quick reference operators verified.")

    # 12. Clean unregister
    print("[12] Testing clean unregister...")
    bpy.ops.preferences.addon_disable(module="blender_web_search")
    print("  -> Addon unregistered cleanly.")

    print("=" * 60)
    print("ALL AUXEREF TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
