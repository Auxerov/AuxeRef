"""Blender 5.0 Add-on: Web Image Search (Google & Pinterest) + 'Open in Blender' Bridge.

Press < / " (Turkish keyboard under ESC or next to Shift) inside Blender to search
Google Images or Pinterest in your default browser.
Right click any image on Google Images or Pinterest -> 'Open in Blender' to add it in one click.
Uses native OS messaging: NO network ports, NO webservers.
"""
bl_info = {
    "name": "Web Image Search & Bridge",
    "author": "Auxerov",
    "version": (2, 1, 0),
    "blender": (5, 0, 0),
    "location": "Shortcut: < / \" (or View3D > Header), Browser Right-Click",
    "description": "Search Google Images & Pinterest via shortcut, then right-click images in browser to Open in Blender in one click.",
    "category": "3D View",
}

import os
import json
import webbrowser
import urllib.parse
import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty
from bpy.types import Operator, AddonPreferences

from . import importer
from . import browser_installer

addon_keymaps = []
INBOX_DIR = "/tmp/blender_open_inbox"

class WebSearchPreferences(AddonPreferences):
    bl_idname = __package__ if __package__ else __name__

    default_mode: EnumProperty(
        name="Default Import Type",
        description="How images should be added to Blender",
        items=[
            ("REFERENCE", "Reference Image (Empty)", "Add as Empty Reference Image facing view"),
            ("PLANE", "Image Plane (Mesh)", "Create Mesh Plane with Principled BSDF material"),
            ("MATERIAL", "Active Material", "Apply as texture to active object's material")
        ],
        default="REFERENCE"
    )

    has_asked_browser_install: BoolProperty(
        name="Has Asked Browser Install",
        default=False
    )

    def draw(self, context):
        layout = self.layout
        detected = browser_installer.detect_default_browser()

        box = layout.box()
        box.label(text="Open in Blender Bridge", icon="WORLD")
        box.label(text=f"Default Browser: {detected['name']}")
        box.prop(self, "default_mode")

        col = box.column(align=True)
        col.operator("wm.auto_install_browser_extension", text=f"Auto-Install Extension to {detected['name']}", icon="IMPORT")

        box2 = layout.box()
        box2.label(text="How to use:", icon="INFO")
        box2.label(text="1. Press < / \" in Blender to search Google Images or Pinterest.")
        box2.label(text="2. In your browser, right-click any image and click 'Open in Blender'!")

        box3 = layout.box()
        box3.label(text="Shortcut Information", icon="KEYINGSET")
        box3.label(text="Default Shortcut: < / \" key (Turkish keyboard under ESC or next to Shift).")
        box3.label(text="Also accessible from 3D Viewport Header Search Icon or F3 -> 'Search Images'.")


class WM_OT_AutoInstallExtension(Operator):
    """Automatically install 'Open in Blender' extension into default browser without manual loading"""
    bl_idname = "wm.auto_install_browser_extension"
    bl_label = "Install Browser Extension"
    bl_description = "Configure 'Open in Blender' extension automatically in default browser"
    bl_options = {"REGISTER"}

    restart_browser: BoolProperty(
        name="Restart Browser Now",
        description="Restart browser to activate immediately (restores all open tabs)",
        default=True
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=480)

    def draw(self, context):
        layout = self.layout
        detected = browser_installer.detect_default_browser()

        box = layout.box()
        box.label(text=f"Detected Browser: {detected['name']}", icon="WORLD")
        box.label(text="Install 'Open in Blender' extension in one click.")

        layout.separator()
        layout.prop(self, "restart_browser")

        box2 = layout.box()
        box2.label(text="No manual steps needed:", icon="CHECKMARK")
        box2.label(text="• The extension is installed automatically into your browser.")
        box2.label(text="• If restarted, all your open tabs and windows will be restored.")

    def execute(self, context):
        pref = context.preferences.addons.get(__package__, None)
        if pref:
            pref.preferences.has_asked_browser_install = True

        success, msg = browser_installer.auto_install_all(restart_browser=self.restart_browser)
        if success:
            self.report({"INFO"}, msg)
        else:
            self.report({"WARNING"}, msg)
        return {"FINISHED"}


class WM_OT_WebImageSearch(Operator):
    """Open search prompt for Google Images or Pinterest and bridge back to Blender"""
    bl_idname = "wm.web_image_search"
    bl_label = "Search Images"
    bl_description = "Search Google Images or Pinterest in browser and open in Blender via right click"
    bl_options = {"REGISTER"}

    query: StringProperty(
        name="Search",
        description="Keyword to search",
        default=""
    )

    engine: EnumProperty(
        name="Source",
        description="Choose search engine",
        items=[
            ("GOOGLE", "Google Images", "Search Google Images in browser"),
            ("PINTEREST", "Pinterest", "Search Pinterest in browser")
        ],
        default="GOOGLE"
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Search Online Images:", icon="VIEWZOOM")
        col.prop(self, "query", text="")
        
        layout.separator()
        row = layout.row(align=True)
        row.prop(self, "engine", expand=True)

        box = layout.box()
        box.label(text="In browser: Right-click image -> 'Open in Blender'!", icon="INFO")

    def execute(self, context):
        q = self.query.strip()
        if not q:
            self.report({"WARNING"}, "Please enter a search term.")
            return {"CANCELLED"}

        encoded = urllib.parse.quote_plus(q)
        if self.engine == "PINTEREST":
            search_url = f"https://www.pinterest.com/search/pins/?q={encoded}"
            engine_name = "Pinterest"
        else:
            search_url = f"https://www.google.com/search?q={encoded}&udm=2"
            engine_name = "Google Images"

        try:
            webbrowser.open_new_tab(search_url)
            self.report({"INFO"}, f"Opened {engine_name} for '{q}'. Right click any image -> Open in Blender!")
        except Exception as e:
            self.report({"ERROR"}, f"Could not launch browser: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


def draw_header_button(self, context):
    """Quick search button in the 3D Viewport header."""
    layout = self.layout
    layout.separator()
    layout.operator("wm.web_image_search", text="", icon="VIEWZOOM")


def draw_add_menu(self, context):
    """Add > Image menu item."""
    layout = self.layout
    layout.separator()
    layout.operator("wm.web_image_search", text="Search Images (< / \")", icon="IMAGE_DATA")


def _check_inbox_timer():
    """Checks /tmp/blender_open_inbox/ on Blender's main loop and opens images immediately."""
    if not os.path.exists(INBOX_DIR):
        try:
            os.makedirs(INBOX_DIR, exist_ok=True)
        except Exception:
            pass
        return 0.15

    for filename in os.listdir(INBOX_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(INBOX_DIR, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                
                try:
                    os.remove(filepath)
                except Exception:
                    pass

                url = payload.get("url")
                title = payload.get("title", "WebImage")

                pref = bpy.context.preferences.addons.get(__package__, None)
                mode = pref.preferences.default_mode if pref else "REFERENCE"

                if url:
                    local_img = importer.download_or_decode_image(url, title)
                    obj, desc = importer.import_image_into_scene(local_img, mode=mode, title=title)
                    print(f"[Open in Blender] Loaded '{obj.name}' as {desc} into scene.")

                    for window in bpy.context.window_manager.windows:
                        for area in window.screen.areas:
                            if area.type == "VIEW_3D":
                                area.tag_redraw()

            except Exception as e:
                print(f"[Open in Blender Error] {e}")
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    return 0.15


__REG_CLASSES = (
    WebSearchPreferences,
    WM_OT_AutoInstallExtension,
    WM_OT_WebImageSearch,
)

def register():
    for cls in __REG_CLASSES:
        bpy.utils.register_class(cls)

    # Ensure native host setup
    browser_installer.ensure_native_host_installed()

    # Add UI elements
    bpy.types.VIEW3D_HT_header.append(draw_header_button)
    bpy.types.VIEW3D_MT_image_add.append(draw_add_menu)

    # Start inbox timer
    bpy.app.timers.register(_check_inbox_timer, first_interval=0.15)

    # Register Keymaps for Turkish keyboard shortcut (< / ")
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km_win = kc.keymaps.new(name="Window", space_type="EMPTY")
        kmi1 = km_win.keymap_items.new("wm.web_image_search", type="ACCENT_GRAVE", value="PRESS")
        addon_keymaps.append((km_win, kmi1))
        kmi2 = km_win.keymap_items.new("wm.web_image_search", type="GRLESS", value="PRESS")
        addon_keymaps.append((km_win, kmi2))

        km_v3d = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi3 = km_v3d.keymap_items.new("wm.web_image_search", type="ACCENT_GRAVE", value="PRESS")
        addon_keymaps.append((km_v3d, kmi3))
        kmi4 = km_v3d.keymap_items.new("wm.web_image_search", type="GRLESS", value="PRESS")
        addon_keymaps.append((km_v3d, kmi4))

    # Automatic prompt on first run (non-headless only)
    def _prompt_auto_install():
        if bpy.app.background:
            return None
        pref = bpy.context.preferences.addons.get(__package__, None)
        if pref and not pref.preferences.has_asked_browser_install:
            try:
                bpy.ops.wm.auto_install_browser_extension("INVOKE_DEFAULT")
            except Exception:
                pass
        return None

    bpy.app.timers.register(_prompt_auto_install, first_interval=1.2)


def unregister():
    if bpy.app.timers.is_registered(_check_inbox_timer):
        bpy.app.timers.unregister(_check_inbox_timer)

    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()

    bpy.types.VIEW3D_HT_header.remove(draw_header_button)
    bpy.types.VIEW3D_MT_image_add.remove(draw_add_menu)

    for cls in reversed(__REG_CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
