"""Image downloading, caching, universal format conversion, and Blender data-block creation."""
import os
import re
import math
import base64
import hashlib
import tempfile
import urllib.request
import urllib.parse
import subprocess
import ssl
import bpy

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def get_cache_dir() -> str:
    cache_dir = os.path.join(tempfile.gettempdir(), "auxeref_image_cache")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir

def clean_name(title: str) -> str:
    if not title:
        return "WebImage"
    cleaned = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    return cleaned[:48] if len(cleaned) > 48 else (cleaned or "WebImage")

def is_valid_image_bytes(data: bytes) -> bool:
    """Verifies that bytes are genuine image data and not an HTML 403/404 error page."""
    if not data or len(data) < 64:
        return False
    prefix = data[:128].lower()
    if b"<!doctype" in prefix or b"<html" in prefix or b"<?xml" in prefix or b"<error" in prefix:
        return False
    return True

def convert_to_png(input_path: str) -> str:
    """Converts any unsupported image format (AVIF, WebP, HEIC, SVG, etc.) to standard PNG via ffmpeg."""
    png_path = os.path.splitext(input_path)[0] + "_converted.png"
    if os.path.exists(png_path) and os.path.getsize(png_path) > 100:
        return png_path

    try:
        res = subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-frames:v", "1", png_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
        if res.returncode == 0 and os.path.exists(png_path) and os.path.getsize(png_path) > 100:
            return png_path
    except Exception as e:
        print(f"[AuxeRef] ffmpeg conversion error: {e}")

    return input_path

def convert_if_needed(filepath: str) -> str:
    """Checks image format and converts unsupported or problematic formats (AVIF, WebP, SVG, HEIC, etc.) to PNG."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(64)
        
        # Standard PNG is always good in Blender
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return filepath

        # Standard JPEG is always good in Blender
        if header.startswith(b"\xff\xd8\xff"):
            return filepath

        # Any other format (WebP, AVIF, HEIC, SVG, TIFF, BMP, etc.) -> Convert to PNG!
        return convert_to_png(filepath)
    except Exception as e:
        print(f"[AuxeRef] convert_if_needed error: {e}")
        return filepath

def download_or_decode_image(url_or_data: str, title: str = "", fallback_url: str = "") -> str:
    """Saves image to disk from either a data URI or HTTP/HTTPS URL, auto-converting to standard PNG."""
    cache_dir = get_cache_dir()
    name = clean_name(title)

    # 1. Base64 data URI
    if url_or_data.startswith("data:image/"):
        match = re.match(r"data:image/(\w+);base64,(.+)", url_or_data)
        if match:
            raw_ext = match.group(1).lower()
            ext = ".png" if "png" in raw_ext else (".jpg" if ("jpg" in raw_ext or "jpeg" in raw_ext) else f".{raw_ext}")
            img_data = base64.b64decode(match.group(2))
            h = hashlib.sha1(img_data).hexdigest()[:12]
            filepath = os.path.join(cache_dir, f"{name}_{h}{ext}")
            with open(filepath, "wb") as f:
                f.write(img_data)
            return convert_if_needed(filepath)

    # 2. HTTP / HTTPS URL
    def fetch_url(target_url: str):
        target_url = target_url.strip()
        parsed = urllib.parse.urlparse(target_url)

        # Referer selection
        if "pinimg.com" in target_url or "pinterest.com" in target_url:
            referer = "https://www.pinterest.com/"
        elif "gstatic.com" in target_url or "google.com" in target_url:
            referer = "https://www.google.com/"
        else:
            referer = f"{parsed.scheme}://{parsed.netloc}/"

        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Referer": referer
        }
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(target_url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=12) as resp:
            data = resp.read()
            if not is_valid_image_bytes(data):
                raise ValueError("Response was not a valid image (likely HTML 403/404)")
            return data

    content = None
    last_err = None
    for attempt_url in [url_or_data, fallback_url]:
        if not attempt_url:
            continue
        try:
            content = fetch_url(attempt_url)
            break
        except Exception as e:
            last_err = e
            # Try without referer if hotlink protected
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                req = urllib.request.Request(attempt_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
                    data = resp.read()
                    if is_valid_image_bytes(data):
                        content = data
                        break
            except Exception:
                pass

    if not content:
        raise ValueError(f"Failed to download image from {url_or_data}: {last_err}")

    # Determine extension from magic bytes
    if content.startswith(b"\x89PNG\r\n\x1a\n"):
        ext = ".png"
    elif content.startswith(b"\xff\xd8\xff"):
        ext = ".jpg"
    elif content.startswith(b"RIFF") and b"WEBP" in content[:16]:
        ext = ".webp"
    elif b"ftyp" in content[:32]:
        ext = ".avif"
    else:
        ext = ".img"

    url_hash = hashlib.sha1(url_or_data.encode("utf-8")).hexdigest()[:12]
    filepath = os.path.join(cache_dir, f"{name}_{url_hash}{ext}")
    with open(filepath, "wb") as f:
        f.write(content)

    return convert_if_needed(filepath)

def get_or_load_image(filepath: str, name: str = "") -> bpy.types.Image:
    """Loads image into Blender, ensuring non-pink valid texture data via automatic format conversion."""
    filepath = convert_if_needed(filepath)
    abs_path = os.path.abspath(filepath)
    
    # Check already loaded
    for img in bpy.data.images:
        if img.filepath and os.path.abspath(bpy.path.abspath(img.filepath)) == abs_path:
            if img.has_data and img.size[0] > 0:
                return img

    bimg = bpy.data.images.load(filepath, check_existing=False)
    
    # If Blender failed to decode (e.g. format unsupported or corrupt), auto-convert via ffmpeg
    if bimg.size[0] == 0 or not bimg.has_data:
        print(f"[AuxeRef] Blender could not decode {filepath} directly. Converting to PNG via ffmpeg...")
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
    return bimg

def create_reference_empty(bimg: bpy.types.Image, name: str, context):
    """Creates an Empty image at the 3D Cursor rotated 90 degrees on the X-axis (standing upright)."""
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
    """Creates a Mesh Plane textured with the image without requiring viewport operators."""
    w, h = bimg.size[0], bimg.size[1]
    aspect = (w / h) if (w > 0 and h > 0) else 1.0

    mesh = bpy.data.meshes.new(f"Mesh_{name}")
    hw = aspect
    hh = 1.0
    verts = [(-hw, -hh, 0.0), (hw, -hh, 0.0), (hw, hh, 0.0), (-hw, hh, 0.0)]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # UV Unwrapping
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for i, loop in enumerate(mesh.loops):
        uv_layer.data[i].uv = uvs[i]

    obj = bpy.data.objects.new(f"Plane_{name}", mesh)
    obj.location = context.scene.cursor.location
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    context.collection.objects.link(obj)

    # Material
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

    # Set active
    for o in context.selected_objects:
        o.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    return obj

def apply_to_active_material(bimg: bpy.types.Image, name: str, context):
    """Applies image texture to active object's material."""
    obj = context.active_object
    if not obj or obj.type != "MESH":
        return create_image_plane(bimg, name, context)

    mat = obj.active_material
    if not mat:
        mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
        if hasattr(mat, "use_nodes"):
            mat.use_nodes = True
        obj.data.materials.append(mat)

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    tex = next((n for n in nodes if n.type == "TEX_IMAGE"), None)
    if not tex:
        tex = nodes.new("ShaderNodeTexImage")
        tex.location = (-320, 0)
    
    tex.image = bimg
    if bsdf:
        links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return obj

def import_image_into_scene(filepath: str, mode: str = "REFERENCE", title: str = "", context = None):
    """Dispatches image import into Blender scene."""
    if context is None:
        context = bpy.context

    name = clean_name(title)
    bimg = get_or_load_image(filepath, name)

    mode_upper = mode.upper() if mode else "REFERENCE"
    if mode_upper == "PLANE":
        created = create_image_plane(bimg, name, context)
        action_desc = "Image Plane (Mesh)"
    elif mode_upper == "MATERIAL":
        created = apply_to_active_material(bimg, name, context)
        action_desc = "Active Material Texture"
    else:  # REFERENCE
        created = create_reference_empty(bimg, name, context)
        action_desc = "Reference Image (Empty)"

    return created, action_desc
