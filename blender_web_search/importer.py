"""Universal Image Importer, Caching, and Conversion for AuxeRef.
Author: Auxerov
"""

import os
import re
import math
import base64
import hashlib
import urllib.request
import urllib.parse
import subprocess
import ssl
import bpy

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"


def get_cache_dir() -> str:
    """Returns persistent directory where reference images are preserved across reboots."""
    cache_dir = os.path.expanduser("~/.config/blender/auxeref_images")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def clean_name(title: str) -> str:
    if not title:
        return "WebImage"
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    return cleaned[:48] if len(cleaned) > 48 else (cleaned or "WebImage")


def is_valid_image_bytes(data: bytes) -> bool:
    if not data or len(data) < 64:
        return False
    prefix = data[:128].lower()
    if b"<!doctype" in prefix or b"<html" in prefix or b"<?xml" in prefix or b"<error" in prefix:
        return False
    return True


def detect_image_extension(content: bytes, url: str = "") -> str:
    if not content:
        return ".png"

    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if content.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if content.startswith(b"GIF87a") or content.startswith(b"GIF89a"):
        return ".gif"
    if content.startswith(b"RIFF") and b"WEBP" in content[:16]:
        return ".webp"
    if content.startswith(b"BM"):
        return ".bmp"
    if content.startswith(b"II*\x00") or content.startswith(b"MM\x00*"):
        return ".tiff"
    if b"ftyp" in content[:32]:
        prefix_32 = content[:32]
        if b"avif" in prefix_32 or b"avis" in prefix_32:
            return ".avif"
        if b"heic" in prefix_32 or b"heif" in prefix_32 or b"mif1" in prefix_32:
            return ".heic"
        return ".avif"
    prefix_lower = content[:512].lower().strip()
    if b"<svg" in prefix_lower or (b"<?xml" in prefix_lower and b"<svg" in prefix_lower):
        return ".svg"
    if content.startswith(b"\x00\x00\x01\x00"):
        return ".ico"
    if content.startswith(b"\xff\x0a") or content.startswith(b"\x00\x00\x00\x0cJXL \r\n\x87\n"):
        return ".jxl"

    clean_url = url.split("?")[0].lower()
    for ext_candidate in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".svg", ".bmp", ".tiff", ".heic", ".ico"]:
        if clean_url.endswith(ext_candidate):
            return ".jpg" if ext_candidate == ".jpeg" else ext_candidate

    return ".img"


def convert_to_png(input_path: str) -> str:
    png_path = os.path.splitext(input_path)[0] + "_converted.png"
    if os.path.exists(png_path) and os.path.getsize(png_path) > 100:
        return png_path

    try:
        res = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-frames:v", "1", "-update", "1", png_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        if res.returncode == 0 and os.path.exists(png_path) and os.path.getsize(png_path) > 100:
            return png_path
    except Exception as e:
        print(f"[AuxeRef] FFmpeg conversion error: {e}")

    try:
        res = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-frames:v", "1", png_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        if res.returncode == 0 and os.path.exists(png_path) and os.path.getsize(png_path) > 100:
            return png_path
    except Exception:
        pass

    try:
        from PIL import Image
        with Image.open(input_path) as im:
            im.convert("RGBA").save(png_path, "PNG")
            if os.path.exists(png_path) and os.path.getsize(png_path) > 100:
                return png_path
    except Exception:
        pass

    return input_path


def convert_if_needed(filepath: str) -> str:
    try:
        with open(filepath, "rb") as f:
            header = f.read(64)

        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return filepath

        if header.startswith(b"\xff\xd8\xff"):
            return filepath

        return convert_to_png(filepath)
    except Exception as e:
        print(f"[AuxeRef] Conversion check error: {e}")
        return filepath


def download_or_decode_image(url_or_data: str, title: str = "", fallback_url: str = "") -> str:
    cache_dir = get_cache_dir()
    name = clean_name(title)

    if url_or_data.startswith("data:image/"):
        match = re.match(r"data:image/([a-zA-Z0-9\-\+\.]+);base64,(.+)", url_or_data)
        if match:
            raw_ext = match.group(1).lower()
            if "png" in raw_ext:
                ext = ".png"
            elif "jpg" in raw_ext or "jpeg" in raw_ext:
                ext = ".jpg"
            elif "webp" in raw_ext:
                ext = ".webp"
            elif "gif" in raw_ext:
                ext = ".gif"
            elif "avif" in raw_ext:
                ext = ".avif"
            else:
                ext = f".{raw_ext}"

            b64_str = match.group(2)
            try:
                img_data = base64.b64decode(b64_str)
                data_hash = hashlib.sha1(img_data).hexdigest()[:12]
                filepath = os.path.join(cache_dir, f"{name}_{data_hash}{ext}")
                with open(filepath, "wb") as f:
                    f.write(img_data)
                return convert_if_needed(filepath)
            except Exception as e:
                print(f"[AuxeRef] Base64 decode failed: {e}")

    target_main_url = url_or_data
    if "pinimg.com" in target_main_url:
        target_main_url = re.sub(r'/(?:236x|474x|564x|736x)/', '/originals/', target_main_url)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    content = None
    urls_to_try = [target_main_url]
    if fallback_url and fallback_url != target_main_url:
        urls_to_try.append(fallback_url)

    for u in urls_to_try:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                data = resp.read()
                if is_valid_image_bytes(data):
                    content = data
                    break
        except Exception as e:
            print(f"[AuxeRef] Fetch attempt failed for {u[:60]}...: {e}")

    if not content:
        raise ValueError(f"Failed to fetch valid image bytes from {target_main_url}")

    ext = detect_image_extension(content, target_main_url)
    url_hash = hashlib.sha1(url_or_data.encode("utf-8")).hexdigest()[:12]
    filepath = os.path.join(cache_dir, f"{name}_{url_hash}{ext}")
    with open(filepath, "wb") as f:
        f.write(content)

    return convert_if_needed(filepath)


def get_or_load_image(filepath: str, name: str = "") -> bpy.types.Image:
    filepath = convert_if_needed(filepath)
    abs_path = os.path.abspath(filepath)

    for img in bpy.data.images:
        if img.filepath and os.path.abspath(bpy.path.abspath(img.filepath)) == abs_path:
            if img.has_data and img.size[0] > 0:
                try:
                    img.pack()
                except Exception:
                    pass
                return img

    bimg = bpy.data.images.load(filepath, check_existing=False)

    if bimg.size[0] == 0 or not bimg.has_data:
        try:
            bpy.data.images.remove(bimg)
        except Exception:
            pass
        png_path = convert_to_png(filepath)
        if png_path != filepath and os.path.exists(png_path):
            bimg = bpy.data.images.load(png_path, check_existing=False)

    if bimg.size[0] == 0 or not bimg.has_data:
        raise ValueError(f"Could not decode valid image texture from {filepath}")

    if name:
        bimg.name = clean_name(name)

    # Pack image into Blender file so it is saved and preserved
    try:
        bimg.pack()
    except Exception:
        pass

    return bimg


def create_reference_empty(bimg: bpy.types.Image, name: str, context):
    empty = bpy.data.objects.new(name=name, object_data=None)
    empty.empty_display_type = "IMAGE"
    empty.data = bimg
    empty.location = context.scene.cursor.location
    empty.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    w, h = bimg.size[0], bimg.size[1]
    if w > 0 and h > 0:
        scale_factor = 3.0
        empty.empty_display_size = scale_factor if w >= h else (scale_factor * (h / w))

    context.collection.objects.link(empty)

    for o in context.selected_objects:
        o.select_set(False)
    empty.select_set(True)
    context.view_layer.objects.active = empty
    return empty


def create_image_plane(bimg: bpy.types.Image, name: str, context):
    w, h = bimg.size[0], bimg.size[1]
    aspect = (w / h) if (w > 0 and h > 0) else 1.0

    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    hw = aspect
    hh = 1.0
    verts = [(-hw, -hh, 0.0), (hw, -hh, 0.0), (hw, hh, 0.0), (-hw, hh, 0.0)]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    uv_layer = mesh.uv_layers.new(name="UVMap")
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for i, loop in enumerate(mesh.loops):
        uv_layer.data[i].uv = uvs[i]

    obj = bpy.data.objects.new(f"Plane_{name}", mesh)
    obj.location = context.scene.cursor.location
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    context.collection.objects.link(obj)

    mat = bpy.data.materials.new(name=f"Mat_{name}")
    if hasattr(mat, "use_nodes"):
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bimg
    tex.location = (-320, 0)

    if bsdf:
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        if "Alpha" in tex.outputs and "Alpha" in bsdf.inputs:
            links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
            if hasattr(mat, "blend_method"):
                mat.blend_method = "BLEND"

    obj.data.materials.append(mat)

    for o in context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj


def apply_to_active_material(bimg: bpy.types.Image, name: str, context):
    obj = context.active_object
    if not obj or obj.type != "MESH":
        return create_image_plane(bimg, name, context)

    mat = obj.active_material
    if not mat:
        mat = bpy.data.materials.new(name=f"Mat_{name}")
        obj.active_material = mat

    if hasattr(mat, "use_nodes"):
        mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bimg
    tex.location = (-320, 0)

    if bsdf:
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])

    return obj


def import_image_into_scene(filepath_or_url: str, mode: str = "REFERENCE", title: str = "Reference", context = None):
    if context is None:
        context = bpy.context

    bimg = get_or_load_image(filepath_or_url, name=title)

    if mode == "PLANE":
        obj = create_image_plane(bimg, title, context)
        desc = "Image Plane"
    elif mode == "MATERIAL":
        obj = apply_to_active_material(bimg, title, context)
        desc = "Active Material Texture"
    else:
        obj = create_reference_empty(bimg, title, context)
        desc = "Reference Image"

    return obj, desc
