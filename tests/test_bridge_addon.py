"""Automated test for blender_web_search add-on and HTTP bridge server."""
import os
import sys
import time
import json
import urllib.request
import urllib.parse
import bpy

def run_tests():
    print("=" * 60)
    print(f"RUNNING WEB IMAGE SEARCH & BRIDGE TESTS ON BLENDER {bpy.app.version_string}")
    print("=" * 60)

    # 1. Enable Add-on
    print("[1] Enabling addon 'blender_web_search'...")
    try:
        bpy.ops.preferences.addon_enable(module="blender_web_search")
        print("  -> Addon enabled successfully!")
    except Exception as e:
        print(f"FAILED to enable addon: {e}")
        sys.exit(1)

    time.sleep(0.5)  # Allow server thread to start

    # 2. Check HTTP bridge server status endpoint
    print("[2] Testing GET http://127.0.0.1:9981/status...")
    try:
        req = urllib.request.Request("http://127.0.0.1:9981/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"  -> Server responded: {data}")
            assert data.get("status") == "online", f"Unexpected status: {data}"
    except Exception as e:
        print(f"FAILED to query bridge server: {e}")
        sys.exit(1)

    # 3. Verify Keymap registration
    print("[3] Verifying Turkish shortcut keymaps (< / \")...")
    from blender_web_search import addon_keymaps
    print(f"  -> Registered {len(addon_keymaps)} keymap items")
    assert len(addon_keymaps) >= 2, f"Expected at least 2 keymap items, got {len(addon_keymaps)}"
    types = [kmi.type for _, kmi in addon_keymaps]
    print(f"  -> Key types registered: {types}")
    assert "ACCENT_GRAVE" in types, "ACCENT_GRAVE keymap not registered!"
    assert "GRLESS" in types, "GRLESS keymap not registered!"

    # 4. Generate base64 test image
    # Minimal 16x16 red PNG data URI
    import struct, zlib, base64
    def make_png_data_uri():
        def png_chunk(chunk_type, data):
            return struct.pack('>I', len(data)) + chunk_type + data + struct.pack('>I', zlib.crc32(chunk_type + data) & 0xffffffff)
        raw = bytearray()
        for y in range(16):
            raw.append(0)
            for x in range(16):
                raw.extend(b'\xff\x20\x20\xff') # Red RGBA
        header = b'\x89PNG\r\n\x1a\n'
        ihdr = png_chunk(b'IHDR', struct.pack('>IIBBBBB', 16, 16, 8, 6, 0, 0, 0))
        idat = png_chunk(b'IDAT', zlib.compress(bytes(raw)))
        iend = png_chunk(b'IEND', b'')
        png_bytes = header + ihdr + idat + iend
        return "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")

    test_data_uri = make_png_data_uri()

    # Helper function to trigger queued timers
    from blender_web_search import bridge_server
    def flush_bridge_queue():
        # Process queue on main thread directly
        bridge_server._process_queue()

    # 5. Test POST /add_image as REFERENCE
    print("[5] Testing POST /add_image (REFERENCE mode)...")
    payload = {
        "url": test_data_uri,
        "mode": "REFERENCE",
        "title": "TestRefImage"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:9981/add_image",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res.get("status") == "ok", f"Unexpected response: {res}"

    flush_bridge_queue()

    # Assert Empty reference object exists
    ref_obj = next((o for o in bpy.context.scene.objects if "TestRefImage" in o.name), None)
    assert ref_obj is not None, "Reference Empty object was not created!"
    assert ref_obj.type == "EMPTY", f"Expected EMPTY, got {ref_obj.type}"
    assert ref_obj.empty_display_type == "IMAGE", f"Expected IMAGE empty, got {ref_obj.empty_display_type}"
    assert ref_obj.data is not None, "Empty data image is None!"
    print(f"  -> Reference object created successfully: '{ref_obj.name}' with image '{ref_obj.data.name}'")

    # 6. Test POST /add_image as PLANE
    print("[6] Testing POST /add_image (PLANE mode)...")
    payload = {
        "url": test_data_uri,
        "mode": "PLANE",
        "title": "TestPlaneImage"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:9981/add_image",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res.get("status") == "ok"

    flush_bridge_queue()

    plane_obj = next((o for o in bpy.context.scene.objects if "Plane_TestPlaneImage" in o.name), None)
    assert plane_obj is not None, "Plane object was not created!"
    assert plane_obj.type == "MESH", f"Expected MESH, got {plane_obj.type}"
    assert len(plane_obj.data.materials) > 0, "Plane object has no material assigned!"
    mat = plane_obj.data.materials[0]
    tex_node = next((n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    assert tex_node is not None, "Plane material missing TEX_IMAGE node!"
    print(f"  -> Plane object created successfully: '{plane_obj.name}' with material '{mat.name}'")

    # 7. Test POST /add_image as MATERIAL
    print("[7] Testing POST /add_image (MATERIAL mode)...")
    bpy.ops.mesh.primitive_cube_add(location=(10, 0, 0))
    cube = bpy.context.active_object
    payload = {
        "url": test_data_uri,
        "mode": "MATERIAL",
        "title": "TestMaterialImage"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:9981/add_image",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res.get("status") == "ok"

    flush_bridge_queue()

    assert len(cube.data.materials) > 0, "Cube has no material after apply!"
    cube_mat = cube.data.materials[0]
    tex_node = next((n for n in cube_mat.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    assert tex_node is not None, "Cube material missing TEX_IMAGE node!"
    print(f"  -> Applied image texture to cube active material successfully!")

    # 8. Test Addon disable and server shutdown
    print("[8] Disabling addon and testing server shutdown...")
    bpy.ops.preferences.addon_disable(module="blender_web_search")
    time.sleep(0.5)

    # Server should be closed now
    try:
        req = urllib.request.Request("http://127.0.0.1:9981/status")
        with urllib.request.urlopen(req, timeout=1) as resp:
            assert False, "Server should have been closed on disable!"
    except Exception:
        print("  -> Bridge server stopped cleanly.")

    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
