"""Blender 5.0 Add-on: Google & Web Image Search directly inside Blender's UI."""
bl_info = {
    "name": "Image Search (Google & Web)",
    "author": "Auxerov",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > Image Search",
    "description": "Search Google and Web images directly inside Blender and add as Reference Image, Image Plane, or Material Texture.",
    "category": "3D View",
    "doc_url": "https://github.com/Auxerov/blender-image-search",
}

import os
import sys
import threading
import concurrent.futures
import bpy
import bpy.utils.previews
from bpy.props import StringProperty, IntProperty, EnumProperty, BoolProperty, PointerProperty
from bpy.types import Operator, Panel, AddonPreferences, PropertyGroup

from . import search_engine
from . import image_actions

# Global dynamic preview collection
preview_collection = None
current_results = []

class ImageSearchPreferences(AddonPreferences):
    bl_idname = __package__ if __package__ else __name__

    google_api_key: StringProperty(
        name="Google API Key",
        description="Google Cloud Custom Search JSON API Key (Optional)",
        default="",
        subtype="PASSWORD"
    )

    google_cx: StringProperty(
        name="Search Engine ID (CX)",
        description="Programmable Search Engine ID (Optional)",
        default=""
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="Google Custom Search API Configuration (Optional)", icon="URL")
        box.label(text="Note: Web (Bing) and Wikimedia searches work for free without any API key!")
        
        col = box.column(align=True)
        col.prop(self, "google_api_key")
        col.prop(self, "google_cx")
        
        box.separator()
        box.label(text="How to get free Google API credentials (100 free searches/day):", icon="INFO")
        box.label(text="1. Create an API Key in Google Cloud Console -> APIs -> Custom Search API.")
        box.label(text="2. Create a Search Engine at programmablesearchengine.google.com with 'Image search' ON.")


class ImageSearchItem(PropertyGroup):
    item_id: StringProperty()
    title: StringProperty()
    full_url: StringProperty()
    thumb_url: StringProperty()
    width: IntProperty(default=0)
    height: IntProperty(default=0)
    source: StringProperty()
    thumb_path: StringProperty()
    full_path: StringProperty()


class ImageSearchProperties(PropertyGroup):
    query: StringProperty(
        name="Search",
        description="Type image search query",
        default="concept art"
    )

    engine: EnumProperty(
        name="Source",
        description="Choose image search engine",
        items=[
            ("BING", "Web / Bing (Free)", "Fast web image search, no API key required"),
            ("WIKIMEDIA", "Wikimedia Commons", "Open public domain & CC library"),
            ("GOOGLE", "Google Images (API)", "Google Custom Search JSON API (requires key in Preferences)")
        ],
        default="BING"
    )

    count: IntProperty(
        name="Results",
        description="Number of images to fetch",
        default=18,
        min=4,
        max=40
    )

    status_message: StringProperty(
        name="Status",
        default="Ready"
    )

    is_searching: BoolProperty(
        name="Is Searching",
        default=False
    )

    selected_index: IntProperty(
        name="Selected Index",
        default=-1
    )

    active_image_title: StringProperty(default="")
    active_image_url: StringProperty(default="")
    active_image_path: StringProperty(default="")
    active_image_res: StringProperty(default="")
    active_image_source: StringProperty(default="")


class IMAGE_OT_Search(Operator):
    """Search images online and download previews in background"""
    bl_idname = "image_search.search"
    bl_label = "Search Images"
    bl_description = "Execute image search in background"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = context.scene.img_search_props
        query = props.query.strip()
        if not query:
            self.report({"WARNING"}, "Please enter a search query.")
            return {"CANCELLED"}

        if props.is_searching:
            self.report({"INFO"}, "Search is already running...")
            return {"CANCELLED"}

        props.is_searching = True
        props.status_message = f"Searching for '{query}'..."
        props.selected_index = -1
        props.active_image_path = ""

        # Read preferences
        pref = context.preferences.addons.get(__package__, None)
        api_key = pref.preferences.google_api_key if pref else ""
        cx = pref.preferences.google_cx if pref else ""
        engine = props.engine
        count = props.count

        def _worker():
            global current_results
            _, thumbs_dir, _ = search_engine.get_cache_dir()
            try:
                # 1. Fetch search result metadata
                if engine == "GOOGLE":
                    if not api_key or not cx:
                        props.status_message = "Error: Google API Key or CX missing in Preferences."
                        props.is_searching = False
                        return
                    items = search_engine.search_google_custom_search(query, api_key, cx, count)
                elif engine == "WIKIMEDIA":
                    items = search_engine.search_wikimedia(query, count)
                else:  # BING
                    items = search_engine.search_bing_web(query, count)

                if not items:
                    props.status_message = "No images found. Try a different query."
                    props.is_searching = False
                    return

                props.status_message = f"Found {len(items)} images. Loading previews..."

                # 2. Concurrently download thumbnails
                def download_thumb(item):
                    idx = item["id"]
                    ext = ".jpg"
                    clean_name = f"thumb_{idx}{ext}"
                    local_path = os.path.join(thumbs_dir, clean_name)
                    if not os.path.exists(local_path):
                        ok = search_engine.download_file(item["thumb_url"], local_path, timeout=8)
                        if ok:
                            item["thumb_path"] = local_path
                    else:
                        item["thumb_path"] = local_path
                    return item

                with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                    updated_items = list(executor.map(download_thumb, items))

                current_results = [it for it in updated_items if it.get("thumb_path") and os.path.exists(it["thumb_path"])]

                # Update preview collection on main thread
                def _update_ui():
                    global preview_collection
                    if preview_collection:
                        preview_collection.clear()
                        for it in current_results:
                            if it.get("thumb_path"):
                                try:
                                    preview_collection.load(it["id"], it["thumb_path"], "IMAGE")
                                except Exception:
                                    pass
                    props.status_message = f"Found {len(current_results)} images"
                    props.is_searching = False
                    # Auto select first
                    if current_results:
                        bpy.ops.image_search.select_item(index=0)
                    return None

                bpy.app.timers.register(_update_ui, first_interval=0.01)

            except Exception as e:
                props.status_message = f"Search failed: {str(e)[:50]}"
                props.is_searching = False

        threading.Thread(target=_worker, daemon=True).start()
        return {"FINISHED"}


class IMAGE_OT_SelectItem(Operator):
    """Select an image from the search results and download full resolution version"""
    bl_idname = "image_search.select_item"
    bl_label = "Select Image"
    bl_description = "Select and prepare image for importing"
    bl_options = {"REGISTER"}

    index: IntProperty(default=0)

    def execute(self, context):
        global current_results
        props = context.scene.img_search_props
        if self.index < 0 or self.index >= len(current_results):
            return {"CANCELLED"}

        item = current_results[self.index]
        props.selected_index = self.index
        props.active_image_title = item.get("title", "Image")
        props.active_image_url = item.get("full_url", "")
        props.active_image_source = item.get("source", "")
        w = item.get("width", 0)
        h = item.get("height", 0)
        props.active_image_res = f"{w} × {h}" if (w and h) else "Original Res"

        # Check if full image is already downloaded
        _, _, full_dir = search_engine.get_cache_dir()
        filename = f"full_{item['id']}.png"
        full_path = os.path.join(full_dir, filename)

        if os.path.exists(full_path) and os.path.getsize(full_path) > 1000:
            props.active_image_path = full_path
        else:
            # Fallback to thumbnail path immediately, download full in background
            props.active_image_path = item.get("thumb_path", "")
            def _download_full():
                ok = search_engine.download_file(item["full_url"], full_path, timeout=15)
                if ok and os.path.exists(full_path):
                    props.active_image_path = full_path

            threading.Thread(target=_download_full, daemon=True).start()

        return {"FINISHED"}


class IMAGE_PT_SearchPanel(Panel):
    """3D Viewport Sidebar Panel for Image Search"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Image Search"
    bl_label = "Image Search"

    def draw(self, context):
        layout = self.layout
        props = context.scene.img_search_props

        # Search bar
        col = layout.column(align=True)
        col.prop(props, "query", text="", icon="VIEWZOOM")
        
        row = col.row(align=True)
        row.prop(props, "engine", text="")
        row.prop(props, "count", text="Max")

        # Search button
        if props.is_searching:
            col.label(text=props.status_message, icon="TIME")
        else:
            btn = col.operator("image_search.search", text="Search", icon="FILE_REFRESH")

        # Status
        layout.label(text=props.status_message, icon="INFO")

        layout.separator()

        # Results Grid / Buttons
        global current_results, preview_collection
        if current_results and preview_collection:
            box = layout.box()
            box.label(text=f"Results ({len(current_results)}):", icon="IMAGE_DATA")
            
            # Draw thumbnails in rows of 3 columns
            grid = box.grid_flow(row_major=True, columns=3, even_columns=True, even_rows=True, align=True)
            for idx, item in enumerate(current_results):
                icon_id = 0
                if item["id"] in preview_collection:
                    icon_id = preview_collection[item["id"]].icon_id
                
                is_selected = (idx == props.selected_index)
                op = grid.operator(
                    "image_search.select_item",
                    text=f"#{idx+1}",
                    icon_value=icon_id,
                    depress=is_selected
                )
                op.index = idx

        # Selected Image Details and Actions
        if props.selected_index >= 0 and props.active_image_path:
            box = layout.box()
            box.label(text="Selected Image Actions:", icon="CHECKMARK")
            
            col = box.column(align=True)
            col.label(text=props.active_image_title[:38])
            col.label(text=f"Resolution: {props.active_image_res} | {props.active_image_source}")
            
            box.separator()
            # Action Buttons
            col = box.column(align=True)
            col.operator("image_search.add_reference", text="Add as Reference (Empty)", icon="IMAGE_REFERENCE")
            col.operator("image_search.add_plane", text="Add as Image Plane (Mesh)", icon="MESH_PLANE")
            col.operator("image_search.apply_to_material", text="Apply to Active Material", icon="MATERIAL")
            col.operator("image_search.open_in_editor", text="Open in Image Editor", icon="IMAGE")


__REG_CLASSES = (
    ImageSearchPreferences,
    ImageSearchItem,
    ImageSearchProperties,
    IMAGE_OT_Search,
    IMAGE_OT_SelectItem,
    IMAGE_PT_SearchPanel,
)

def register():
    global preview_collection
    preview_collection = bpy.utils.previews.new()

    for cls in __REG_CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.img_search_props = PointerProperty(type=ImageSearchProperties)
    image_actions.register()

def unregister():
    global preview_collection
    image_actions.unregister()

    if hasattr(bpy.types.Scene, "img_search_props"):
        del bpy.types.Scene.img_search_props

    for cls in reversed(__REG_CLASSES):
        bpy.utils.unregister_class(cls)

    if preview_collection is not None:
        bpy.utils.previews.remove(preview_collection)
        preview_collection = None

if __name__ == "__main__":
    register()
