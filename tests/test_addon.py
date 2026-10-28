"""Automated test for blender_image_search addon on Blender 5.0 and 5.2."""
import os
import sys
import tempfile
import bpy

def run_tests():
    print("=" * 60)
    print(f"RUNNING IMAGE SEARCH ADDON TESTS ON BLENDER {bpy.app.version_string}")
    print("=" * 60)

    # 1. Enable Add-on
    print("[1] Enabling addon 'blender_image_search'...")
    try:
        bpy.ops.preferences.addon_enable(module="blender_image_search")
        print("  -> Addon enabled successfully!")
    except Exception as e:
        print(f"FAILED to enable addon: {e}")
        sys.exit(1)

    assert hasattr(bpy.types.Scene, "img_search_props"), "Scene.img_search_props not registered!"
    scene = bpy.context.scene
    props = scene.img_search_props

    # 2. Test search engine queries
    from blender_image_search import search_engine
    print("[2] Testing search engine backend (Wikimedia & Bing)...")
    wiki_res = search_engine.search_wikimedia("cube", count=3)
    print(f"  -> Wikimedia returned {len(wiki_res)} items")
    assert len(wiki_res) > 0, "Wikimedia search returned 0 items!"

    bing_res = search_engine.search_bing_web("blender logo", count=3)
    print(f"  -> Bing returned {len(bing_res)} items")
    assert len(bing_res) > 0, "Bing search returned 0 items!"

    # 3. Create dummy image file for action testing
    print("[3] Creating test image file...")
    tmp_dir = tempfile.gettempdir()
    test_img_path = os.path.join(tmp_dir, "test_texture.png")
    
    # Create simple 64x32 image in Blender and save it
    dummy_bimg = bpy.data.images.new("TempTestImg", width=64, height=32, alpha=True)
    dummy_bimg.filepath_raw = test_img_path
    dummy_bimg.file_format = "PNG"
    dummy_bimg.save()
    assert os.path.exists(test_img_path), "Failed to save test image!"
    print(f"  -> Test image saved to {test_img_path} (64x32)")

    props.active_image_path = test_img_path
    props.active_image_title = "MyTestImage"

    # 4. Test Add Reference Image
    print("[4] Testing IMAGE_OT_AddReference operator...")
    res = bpy.ops.image_search.add_reference()
    assert "FINISHED" in res, f"add_reference failed: {res}"
    active = bpy.context.active_object
    assert active is not None and active.type == "EMPTY", f"Expected EMPTY, got {active}"
    assert active.empty_display_type == "IMAGE", f"Expected empty_display_type == 'IMAGE', got {active.empty_display_type}"
    assert active.data is not None, "Empty data (image) is None!"
    print(f"  -> Reference empty created: '{active.name}' with image '{active.data.name}'")

    # 5. Test Add Image Plane
    print("[5] Testing IMAGE_OT_AddPlane operator...")
    res = bpy.ops.image_search.add_plane()
    assert "FINISHED" in res, f"add_plane failed: {res}"
    plane = bpy.context.active_object
    assert plane is not None and plane.type == "MESH", f"Expected MESH, got {plane}"
    assert len(plane.data.materials) > 0, "Plane has no material!"
    mat = plane.data.materials[0]
    nodes = mat.node_tree.nodes
    tex_node = None
    for n in nodes:
        if n.type == "TEX_IMAGE":
            tex_node = n
            break
    assert tex_node is not None, "Plane material has no Image Texture node!"
    assert tex_node.image is not None, "Image Texture node has no image assigned!"
    print(f"  -> Image plane created: '{plane.name}', material: '{mat.name}', aspect ratio applied.")

    # 6. Test Apply To Material
    print("[6] Testing IMAGE_OT_ApplyToMaterial operator...")
    bpy.ops.mesh.primitive_cube_add(location=(5, 5, 0))
    cube = bpy.context.active_object
    res = bpy.ops.image_search.apply_to_material()
    assert "FINISHED" in res, f"apply_to_material failed: {res}"
    assert len(cube.data.materials) > 0, "Cube has no material after apply!"
    mat = cube.data.materials[0]
    tex_node = next((n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE"), None)
    assert tex_node is not None, "Cube material missing Image Texture node!"
    print(f"  -> Applied image texture to cube '{cube.name}' material '{mat.name}' successfully.")

    # 7. Test Open in Image Editor
    print("[7] Testing IMAGE_OT_OpenInEditor operator...")
    res = bpy.ops.image_search.open_in_editor()
    assert "FINISHED" in res, f"open_in_editor failed: {res}"
    print("  -> open_in_editor executed successfully.")

    # 8. Unregister and re-enable check
    print("[8] Testing addon disable & enable cycle...")
    bpy.ops.preferences.addon_disable(module="blender_image_search")
    assert not hasattr(bpy.types.Scene, "img_search_props"), "Scene.img_search_props was not cleaned up on disable!"
    bpy.ops.preferences.addon_enable(module="blender_image_search")
    assert hasattr(bpy.types.Scene, "img_search_props"), "Scene.img_search_props not restored on re-enable!"
    print("  -> Addon disable/enable cycle clean!")

    print("=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
