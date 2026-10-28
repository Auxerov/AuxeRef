"""AuxeRef: Fast Image Search (Google & Pinterest) via F8 + Browser Context Bridge.

Press F8 in Blender to open the search bar (tab through engine, enter to search).
In your browser, right-click any image -> AuxeRef -> 'Open in Blender' or 'Add to Quick'.
Saved quick images appear at the bottom of the F8 search dialog and in the AuxeRef N-Panel.
Uses native OS messaging: ZERO network ports, ZERO webservers.
"""
bl_info = {
    "name": "AuxeRef",
    "author": "Auxerov",
    "version": (2, 2, 0),
    "blender": (5, 0, 0),
    "location": "Shortcut: F8 (or View3D > Header), Browser Right-Click: AuxeRef",
    "description": "AuxeRef: Fast Google Images & Pinterest search via F8 and right-click browser bridge for references.",
    "category": "3D View",
}

import os
import json
import webbrowser
import urllib.parse
import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty
from bpy.types import Operator, Panel, AddonPreferences

from . import importer
from . import browser_installer
from . import quick_manager

addon_keymaps = []
INBOX_DIR = "/tmp/blender_open_inbox"

class AuxeRefPreferences(AddonPreferences):
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
        box.label(text=f"AuxeRef Native Bridge ({detected['name']})", icon="WORLD")
        box.prop(self, "default_mode")

        col = box.column(align=True)
        col.operator("wm.auxeref_auto_install", text=f"Auto-Install Extension to {detected['name']}", icon="IMPORT")


class WM_OT_AuxeRefSearch(Operator):
    """Open AuxeRef search prompt for Google Images & Pinterest and access quick references"""
    bl_idname = "wm.auxeref_search"
    bl_label = "AuxeRef Search"
    bl_description = "Search Google Images or Pinterest (F8) and access saved quick references"
    bl_options = {"REGISTER"}

    query: StringProperty(
        name="Search",
        description="Type keyword to search, or paste URL to import immediately",
        default=""
    )

    engine: EnumProperty(
        name="Engine",
        description="Tab to switch between Google Images and Pinterest",
        items=[
            ("GOOGLE", "Google Images", "Search Google Images"),
            ("PINTEREST", "Pinterest", "Search Pinterest")
        ],
        default="GOOGLE"
    )

    def invoke(self, context, event):
        self.query = ""
        return context.window_manager.invoke_props_dialog(self, width=440)

    def draw(self, context):
        layout = self.layout

        # 1. Minimalist Search Box
        col = layout.column(align=True)
        col.prop(self, "query", text="", icon="VIEWZOOM")

        # 2. Engine Tabs
        row = layout.row(align=True)
        row.prop(self, "engine", expand=True)

        # 3. Quick References (Saved Images)
        items = quick_manager.load_quick_references()
        if items:
            layout.separator()
            box = layout.box()
            header_row = box.row()
            header_row.label(text=f"Quicks ({len(items)})", icon="IMAGE_DATA")
            header_row.operator("wm.auxeref_clear_quick", text="Clear", icon="TRASH")
            col = box.column(align=True)
            for idx, item in enumerate(items[:10]):
                r = col.row(align=True)
                title = item.get("title") or f"Quick #{idx + 1}"
                op = r.operator("wm.auxeref_spawn_quick", text=title, icon="RESTRICT_VIEW_OFF")
                op.index = idx
                op_link = r.operator("wm.auxeref_open_url", text="", icon="URL")
                op_link.index = idx
                op_edit = r.operator("wm.auxeref_edit_quick", text="", icon="GREASEPENCIL")
                op_edit.index = idx
                del_op = r.operator("wm.auxeref_remove_quick", text="", icon="X")
                del_op.index = idx

    def execute(self, context):
        q = self.query.strip()
        items = quick_manager.load_quick_references()
        pref = context.preferences.addons.get(__package__, None)
        mode = pref.preferences.default_mode if pref else "REFERENCE"

        # Case 1: Empty input on Enter -> spawn top quick if available
        if not q:
            if items:
                item = items[0]
                filepath = item.get("filepath", "")
                title = item.get("title", "QuickRef")
                if filepath and os.path.exists(filepath):
                    obj, desc = importer.import_image_into_scene(filepath, mode=mode, title=title, context=context)
                    self.report({"INFO"}, f"Added '{obj.name}' as {desc} into scene!")
                    return {"FINISHED"}
            return {"FINISHED"}

        is_url = q.startswith("http://") or q.startswith("https://") or q.startswith("data:image/")

        # Case 2: Pasted URL / Data URI -> Enter directly downloads, rotates 90° on X, and adds to scene & Quicks
        if is_url:
            try:
                clean_title = "DirectImage" if q.startswith("data:") else q.split("/")[-1].split("?")[0]
                if not clean_title or len(clean_title) < 2:
                    clean_title = "DirectImage"
                local_img = importer.download_or_decode_image(q, clean_title)
                obj, desc = importer.import_image_into_scene(local_img, mode=mode, title=clean_title, context=context)
                quick_manager.add_quick_reference(obj.name, q, local_img)
                self.report({"INFO"}, f"Added '{obj.name}' as {desc} into scene (rotated 90° on X)!")
                return {"FINISHED"}
            except Exception as e:
                self.report({"ERROR"}, f"Direct Add failed: {e}")
                return {"CANCELLED"}

        # Case 3: Keyword search -> Enter directly opens browser
        encoded = urllib.parse.quote_plus(q)
        if self.engine == "PINTEREST":
            search_url = f"https://www.pinterest.com/search/pins/?q={encoded}"
            engine_name = "Pinterest"
        else:
            search_url = f"https://www.google.com/search?q={encoded}&udm=2"
            engine_name = "Google Images"

        try:
            webbrowser.open_new_tab(search_url)
            self.report({"INFO"}, f"Opened {engine_name} for '{q}'")
        except Exception as e:
            self.report({"ERROR"}, f"Could not launch browser: {e}")
            return {"CANCELLED"}

        return {"FINISHED"}


class WM_OT_AuxeRefSpawnQuick(Operator):
    """Spawn a saved quick reference image directly into the 3D scene"""
    bl_idname = "wm.auxeref_spawn_quick"
    bl_label = "Spawn Quick Reference"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(default=0)

    def execute(self, context):
        items = quick_manager.load_quick_references()
        if self.index < 0 or self.index >= len(items):
            self.report({"WARNING"}, "Quick reference item not found.")
            return {"CANCELLED"}

        item = items[self.index]
        filepath = item.get("filepath", "")
        title = item.get("title", "QuickRef")

        if not filepath or not os.path.exists(filepath):
            self.report({"ERROR"}, "Image file missing on disk.")
            return {"CANCELLED"}

        pref = context.preferences.addons.get(__package__, None)
        mode = pref.preferences.default_mode if pref else "REFERENCE"

        obj, desc = importer.import_image_into_scene(filepath, mode=mode, title=title, context=context)
        self.report({"INFO"}, f"Spawned '{obj.name}' as {desc} into scene.")
        return {"FINISHED"}


class WM_OT_AuxeRefRemoveQuick(Operator):
    """Remove an item from saved Quick References"""
    bl_idname = "wm.auxeref_remove_quick"
    bl_label = "Remove Quick Reference"
    bl_options = {"REGISTER"}

    index: IntProperty(default=0)

    def execute(self, context):
        quick_manager.remove_quick_reference(self.index)
        return {"FINISHED"}


class WM_OT_AuxeRefClearQuick(Operator):
    """Clear all saved Quick References"""
    bl_idname = "wm.auxeref_clear_quick"
    bl_label = "Clear All Quick References"
    bl_options = {"REGISTER"}

    def execute(self, context):
        quick_manager.clear_quick_references()
        self.report({"INFO"}, "Cleared all Quick References.")
        return {"FINISHED"}


class WM_OT_AuxeRefEditQuick(Operator):
    """Edit the name and link of a saved Quick Reference"""
    bl_idname = "wm.auxeref_edit_quick"
    bl_label = "Edit Quick Reference"
    bl_description = "Change the name or URL of this saved quick reference"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(default=0)
    title: StringProperty(name="Name / Title", default="")
    url: StringProperty(name="Web Link / URL", default="")

    def invoke(self, context, event):
        items = quick_manager.load_quick_references()
        if 0 <= self.index < len(items):
            self.title = items[self.index].get("title", "")
            self.url = items[self.index].get("url", "")
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.prop(self, "title")
        col.prop(self, "url")

    def execute(self, context):
        quick_manager.update_quick_reference(self.index, self.title, self.url)
        self.report({"INFO"}, f"Updated Quick Reference: '{self.title}'")
        return {"FINISHED"}


class WM_OT_AuxeRefOpenUrl(Operator):
    """Open source webpage of this quick reference in your browser"""
    bl_idname = "wm.auxeref_open_url"
    bl_label = "Open Source Link"
    bl_options = {"REGISTER"}

    index: IntProperty(default=0)

    def execute(self, context):
        items = quick_manager.load_quick_references()
        if 0 <= self.index < len(items):
            url = items[self.index].get("url", "")
            if url:
                try:
                    webbrowser.open_new_tab(url)
                    self.report({"INFO"}, f"Opened {url}")
                except Exception as e:
                    self.report({"ERROR"}, f"Could not open browser: {e}")
        return {"FINISHED"}


class WM_OT_AuxeRefAutoInstall(Operator):
    """Automatically install AuxeRef extension into default browser"""
    bl_idname = "wm.auxeref_auto_install"
    bl_label = "Install AuxeRef Browser Extension"
    bl_description = "Configure AuxeRef extension automatically in default browser"
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
        box.label(text="Install AuxeRef extension automatically.")

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


class VIEW3D_PT_AuxeRefPanel(Panel):
    """3D Viewport N-Panel for AuxeRef and Quick References"""
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AuxeRef"
    bl_label = "AuxeRef & Quicks"

    def draw(self, context):
        layout = self.layout
        pref = context.preferences.addons.get(__package__, None)

        # Search Trigger
        col = layout.column(align=True)
        col.operator("wm.auxeref_search", text="Search (F8)", icon="VIEWZOOM")

        if pref:
            layout.separator()
            layout.prop(pref.preferences, "default_mode", text="Import As")

        # Quick References List
        items = quick_manager.load_quick_references()
        if items:
            layout.separator()
            box = layout.box()
            row = box.row()
            row.label(text=f"Quicks ({len(items)})", icon="IMAGE_DATA")
            row.operator("wm.auxeref_clear_quick", text="Clear", icon="TRASH")
            col = box.column(align=True)
            for idx, item in enumerate(items):
                r = col.row(align=True)
                title = item.get("title") or f"Quick #{idx + 1}"
                op = r.operator("wm.auxeref_spawn_quick", text=title, icon="RESTRICT_VIEW_OFF")
                op.index = idx
                op_link = r.operator("wm.auxeref_open_url", text="", icon="URL")
                op_link.index = idx
                op_edit = r.operator("wm.auxeref_edit_quick", text="", icon="GREASEPENCIL")
                op_edit.index = idx
                del_op = r.operator("wm.auxeref_remove_quick", text="", icon="X")
                del_op.index = idx


def draw_header_button(self, context):
    """Quick search button in the 3D Viewport header."""
    layout = self.layout
    layout.separator()
    layout.operator("wm.auxeref_search", text="AuxeRef (F8)", icon="VIEWZOOM")


def draw_add_menu(self, context):
    """Add > Image menu item."""
    layout = self.layout
    layout.separator()
    layout.operator("wm.auxeref_search", text="AuxeRef Search (F8)", icon="IMAGE_DATA")


def _check_inbox_timer():
    """Checks /tmp/blender_open_inbox/ on Blender's main loop and processes Open/QuickAdd."""
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

                action = payload.get("action", "OPEN")
                url = payload.get("url")
                fallback_url = payload.get("fallback_url", "")
                title = payload.get("title", "AuxeRef")

                if url:
                    local_img = importer.download_or_decode_image(url, title, fallback_url=fallback_url)

                    if action == "QUICK_ADD":
                        quick_manager.add_quick_reference(title, url, local_img)
                        print(f"[AuxeRef] Saved '{title}' to Quicks.")
                    else:  # "OPEN"
                        pref = bpy.context.preferences.addons.get(__package__, None)
                        mode = pref.preferences.default_mode if pref else "REFERENCE"
                        obj, desc = importer.import_image_into_scene(local_img, mode=mode, title=title)
                        print(f"[AuxeRef] Opened '{obj.name}' as {desc} in scene.")
                        # Also automatically add to quick references
                        quick_manager.add_quick_reference(title, url, local_img)

                    for window in bpy.context.window_manager.windows:
                        for area in window.screen.areas:
                            if area.type == "VIEW_3D":
                                area.tag_redraw()

            except Exception as e:
                print(f"[AuxeRef Error] {e}")
                try:
                    os.remove(filepath)
                except Exception:
                    pass

    return 0.15


__REG_CLASSES = (
    AuxeRefPreferences,
    WM_OT_AuxeRefSearch,
    WM_OT_AuxeRefSpawnQuick,
    WM_OT_AuxeRefEditQuick,
    WM_OT_AuxeRefOpenUrl,
    WM_OT_AuxeRefRemoveQuick,
    WM_OT_AuxeRefClearQuick,
    WM_OT_AuxeRefAutoInstall,
    VIEW3D_PT_AuxeRefPanel,
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

    # Register Keymaps for F8 (and < / " fallback)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # Window keymap
        km_win = kc.keymaps.new(name="Window", space_type="EMPTY")
        
        # Primary: F8
        kmi_f8_win = km_win.keymap_items.new("wm.auxeref_search", type="F8", value="PRESS")
        addon_keymaps.append((km_win, kmi_f8_win))

        # Secondary: < / " keys
        kmi1 = km_win.keymap_items.new("wm.auxeref_search", type="ACCENT_GRAVE", value="PRESS")
        addon_keymaps.append((km_win, kmi1))
        kmi2 = km_win.keymap_items.new("wm.auxeref_search", type="GRLESS", value="PRESS")
        addon_keymaps.append((km_win, kmi2))

        # 3D View keymap
        km_v3d = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi_f8_v3d = km_v3d.keymap_items.new("wm.auxeref_search", type="F8", value="PRESS")
        addon_keymaps.append((km_v3d, kmi_f8_v3d))
        
        kmi3 = km_v3d.keymap_items.new("wm.auxeref_search", type="ACCENT_GRAVE", value="PRESS")
        addon_keymaps.append((km_v3d, kmi3))
        kmi4 = km_v3d.keymap_items.new("wm.auxeref_search", type="GRLESS", value="PRESS")
        addon_keymaps.append((km_v3d, kmi4))

    # Automatic prompt on first run (non-headless only)
    def _prompt_auto_install():
        if bpy.app.background:
            return None
        pref = bpy.context.preferences.addons.get(__package__, None)
        if pref and not pref.preferences.has_asked_browser_install:
            try:
                bpy.ops.wm.auxeref_auto_install("INVOKE_DEFAULT")
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
