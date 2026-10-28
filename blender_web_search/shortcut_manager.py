"""Shortcut management and keymap synchronization for AuxeRef.
Author: Auxerov
"""
import bpy

def sync_keymaps(addon_keymaps):
    primary = None
    for km, kmi in addon_keymaps:
        if km.name == "Window" and kmi.idname == "wm.auxeref_search" and kmi.type not in ("ACCENT_GRAVE", "GRLESS"):
            primary = kmi
            break
    if primary:
        for km, kmi in addon_keymaps:
            if km.name == "3D View" and kmi.idname == "wm.auxeref_search" and kmi.type not in ("ACCENT_GRAVE", "GRLESS"):
                if kmi.type != primary.type or kmi.ctrl != primary.ctrl or kmi.shift != primary.shift or kmi.alt != primary.alt:
                    kmi.type = primary.type
                    kmi.value = primary.value
                    kmi.ctrl = primary.ctrl
                    kmi.shift = primary.shift
                    kmi.alt = primary.alt
                    kmi.oskey = primary.oskey

def get_primary_kmi(addon_keymaps):
    sync_keymaps(addon_keymaps)
    for km, kmi in addon_keymaps:
        if km.name == "Window" and kmi.idname == "wm.auxeref_search" and kmi.type not in ("ACCENT_GRAVE", "GRLESS"):
            return kmi
    return None

def draw_shortcut(layout, addon_keymaps):
    kmi = get_primary_kmi(addon_keymaps)
    if kmi:
        row = layout.row(align=True)
        row.label(text="Shortcut:")
        row.prop(kmi, "type", text="", full_event=True)
