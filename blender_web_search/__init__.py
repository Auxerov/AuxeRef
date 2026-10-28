"""Blender 5.0 Add-on: Web Image Search & Browser Bridge.

Allows pressing the Turkish keyboard shortcut (< / ") inside Blender to pop up
a search bar that opens Google Images in your default browser, and adds images
directly into Blender via Right-Click -> Add to Blender in Chrome/Firefox.
"""
bl_info = {
    "name": "Web Image Search & Bridge",
    "author": "Auxerov",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "Shortcut: < / \" (or View3D > Header), Browser Right-Click",
    "description": "Popup Google Images search from Blender via shortcut, then right-click images in browser to add directly to Blender.",
    "category": "3D View",
}

import os
import sys
import webbrowser
import urllib.parse
import bpy
from bpy.props import StringProperty, IntProperty, EnumProperty
from bpy.types import Operator, Panel, AddonPreferences, Header

from . import bridge_server
from . import importer

addon_keymaps = []

class WebSearchPreferences(AddonPreferences):
    bl_idname = __package__ if __package__ else __name__

    server_port: IntProperty(
        name="Bridge Server Port",
        description="Local HTTP server port for browser communication",
        default=9981,
        min=1024,
        max=65535
    )

    default_mode: EnumProperty(
        name="Default Import Mode",
        description="Default way to import images into Blender",
        items=[
            ("REFERENCE", "Reference Image (Empty)", "Add as 3D Viewport Reference Image Empty facing view"),
            ("PLANE", "Image Plane (Mesh)", "Create Mesh Plane with Principled BSDF material"),
            ("MATERIAL", "Active Material", "Apply as texture to active object's material")
        ],
        default="REFERENCE"
    )

    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="Local Bridge Server Configuration", icon="WORLD")
        row = box.row()
        row.prop(self, "server_port")
        row.prop(self, "default_mode")
        
        status_text = f"Server listening on http://127.0.0.1:{self.server_port}" if bridge_server.server_instance else "Server is stopped"
        status_icon = "CHECKMARK" if bridge_server.server_instance else "ERROR"
        box.label(text=status_text, icon=status_icon)

        box2 = layout.box()
        box2.label(text="Browser Extension (Chrome / Thorium / Firefox)", icon="PREFERENCES")
        box2.label(text="To enable 'Right Click -> Add to Blender' in your browser:")
        
        col = box2.column(align=True)
        col.label(text="1. Chrome / Thorium / Brave: Go to chrome://extensions -> Enable Developer Mode -> Load unpacked")
        col.label(text="   Select folder: /home/auxerov/blender-image-search/extension")
        col.separator()
        col.label(text="2. Firefox: Go to about:debugging#/runtime/this-firefox -> Load Temporary Add-on")
        col.label(text="   Select file: /home/auxerov/blender-image-search/extension_firefox/manifest.json")
        
        box3 = layout.box()
        box3.label(text="Shortcut Information", icon="KEYINGSET")
        box3.label(text="Default Shortcut: < / \" key (Turkish keyboard under ESC or next to Shift).")
        box3.label(text="You can also use: 3D Viewport Header Search Icon or F3 -> 'Search Google Images'.")


class WM_OT_WebImageSearch(Operator):
    """Open Google Images search prompt and bridge images into Blender"""
    bl_idname = "wm.web_image_search"
    bl_label = "Search Google Images"
    bl_description = "Popup search bar for Google Images and open in default browser"
    bl_options = {"REGISTER"}

    query: StringProperty(
        name="Search",
        description="Keyword to search on Google Images",
        default=""
    )

    mode: EnumProperty(
        name="Import Mode",
        description="How to add image to Blender when selected in browser",
        items=[
            ("REFERENCE", "Reference Image (Empty)", "Add as 3D Viewport Reference Image Empty facing view"),
            ("PLANE", "Image Plane (Mesh)", "Create Mesh Plane with Principled BSDF material"),
            ("MATERIAL", "Active Material", "Apply as texture to active object's material")
        ],
        default="REFERENCE"
    )

    def invoke(self, context, event):
        pref = context.preferences.addons.get(__package__, None)
        if pref:
            self.mode = pref.preferences.default_mode
        elif hasattr(context.scene, "web_search_default_mode"):
            self.mode = context.scene.web_search_default_mode
        return context.window_manager.invoke_props_dialog(self, width=440)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Search Google Images:", icon="VIEWZOOM")
        col.prop(self, "query", text="")
        
        layout.separator()
        row = layout.row()
        row.prop(self, "mode", text="Import As")

        box = layout.box()
        box.label(text="In browser: Right-click image -> 'Add to Blender'!", icon="INFO")
        if not bridge_server.server_instance:
            box.label(text="Warning: Local bridge server is not running!", icon="ERROR")

    def execute(self, context):
        q = self.query.strip()
        if not q:
            self.report({"WARNING"}, "Please enter a search term.")
            return {"CANCELLED"}

        # Store mode preference
        context.scene.web_search_default_mode = self.mode

        # Ensure server is running
        if not bridge_server.server_instance:
            pref = context.preferences.addons.get(__package__, None)
            port = pref.preferences.server_port if pref else 9981
            bridge_server.start_server(port)

        # Open Google Images in default browser
        # udm=2 is modern Google Images, tbm=isch is legacy fallback
        encoded_query = urllib.parse.quote_plus(q)
        search_url = f"https://www.google.com/search?q={encoded_query}&udm=2&tbm=isch"

        try:
            webbrowser.open_new_tab(search_url)
            self.report({"INFO"}, f"Opened Google Images for '{q}'. Right click any image -> Add to Blender!")
        except Exception as e:
            self.report({"ERROR"}, f"Could not launch browser: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


def draw_header_button(self, context):
    """Draws a quick search button in the 3D Viewport header."""
    layout = self.layout
    layout.separator()
    layout.operator("wm.web_image_search", text="", icon="VIEWZOOM")


def draw_add_menu(self, context):
    """Adds operator to Add > Image menu."""
    layout = self.layout
    layout.separator()
    layout.operator("wm.web_image_search", text="Google Images (< / \")", icon="IMAGE_DATA")


__REG_CLASSES = (
    WebSearchPreferences,
    WM_OT_WebImageSearch,
)

def register():
    for cls in __REG_CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.web_search_default_mode = EnumProperty(
        name="Default Import Mode",
        items=[
            ("REFERENCE", "Reference Image", ""),
            ("PLANE", "Image Plane", ""),
            ("MATERIAL", "Active Material", "")
        ],
        default="REFERENCE"
    )

    # Add UI elements
    bpy.types.VIEW3D_HT_header.append(draw_header_button)
    bpy.types.VIEW3D_MT_image_add.append(draw_add_menu)

    # Start local bridge HTTP server
    bridge_server.start_server(port=9981)

    # Register Keymaps for Turkish keyboard shortcut (< / ")
    # On Turkish keyboards:
    # - Key below ESC (labeled é, ", <) produces ACCENT_GRAVE
    # - Key between Left Shift and Z (labeled <, >) produces GRLESS
    # We bind both in Window and 3D View so either key immediately opens search!
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # 1. Window keymap (works across all areas in Blender)
        km_win = kc.keymaps.new(name="Window", space_type="EMPTY")
        
        # Primary: ACCENT_GRAVE (the " / < key under ESC)
        kmi1 = km_win.keymap_items.new("wm.web_image_search", type="ACCENT_GRAVE", value="PRESS")
        addon_keymaps.append((km_win, kmi1))
        
        # Secondary: GRLESS (the < / > key next to Left Shift)
        kmi2 = km_win.keymap_items.new("wm.web_image_search", type="GRLESS", value="PRESS")
        addon_keymaps.append((km_win, kmi2))

        # 2. 3D View keymap
        km_v3d = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi3 = km_v3d.keymap_items.new("wm.web_image_search", type="ACCENT_GRAVE", value="PRESS")
        addon_keymaps.append((km_v3d, kmi3))
        
        kmi4 = km_v3d.keymap_items.new("wm.web_image_search", type="GRLESS", value="PRESS")
        addon_keymaps.append((km_v3d, kmi4))


def unregister():
    # Remove keymaps
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    addon_keymaps.clear()

    # Remove UI hooks
    bpy.types.VIEW3D_HT_header.remove(draw_header_button)
    bpy.types.VIEW3D_MT_image_add.remove(draw_add_menu)

    # Stop local HTTP server
    bridge_server.stop_server()

    if hasattr(bpy.types.Scene, "web_search_default_mode"):
        del bpy.types.Scene.web_search_default_mode

    for cls in reversed(__REG_CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
