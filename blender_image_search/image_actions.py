"""Operators to import and apply downloaded images inside Blender 5.0."""
import os
import bpy
from bpy.types import Operator

def get_or_load_image(filepath: str, name: str = "") -> bpy.types.Image:
    """Loads an image into Blender, reusing existing data-block if already loaded."""
    abs_path = os.path.abspath(filepath)
    for img in bpy.data.images:
        if img.filepath and os.path.abspath(bpy.path.abspath(img.filepath)) == abs_path:
            return img
    img = bpy.data.images.load(filepath, check_existing=True)
    if name:
        img.name = name
    return img

class IMAGE_OT_AddReference(Operator):
    """Add the selected image as a 3D Viewport Reference Image (Empty)"""
    bl_idname = "image_search.add_reference"
    bl_label = "Add as Reference Image"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        props = context.scene.img_search_props
        return bool(props.active_image_path and os.path.exists(props.active_image_path))

    def execute(self, context):
        props = context.scene.img_search_props
        filepath = props.active_image_path
        if not filepath or not os.path.exists(filepath):
            self.report({"ERROR"}, "Image file not found on disk.")
            return {"CANCELLED"}

        img_name = props.active_image_title or "ReferenceImage"
        bimg = get_or_load_image(filepath, img_name)

        # Create Empty Image
        empty = bpy.data.objects.new(name=img_name, object_data=None)
        empty.empty_display_type = "IMAGE"
        empty.data = bimg
        empty.location = context.scene.cursor.location

        # Set size based on aspect ratio
        w, h = bimg.size[0], bimg.size[1]
        if w > 0 and h > 0:
            scale_factor = 3.0
            if w >= h:
                empty.empty_display_size = scale_factor
            else:
                empty.empty_display_size = scale_factor * (h / w)

        context.collection.objects.link(empty)

        # Select and make active
        bpy.ops.object.select_all(action="DESELECT")
        empty.select_set(True)
        context.view_layer.objects.active = empty

        self.report({"INFO"}, f"Added Reference Image: '{img_name}'")
        return {"FINISHED"}


class IMAGE_OT_AddPlane(Operator):
    """Create a Mesh Plane textured with the selected image (Images as Planes)"""
    bl_idname = "image_search.add_plane"
    bl_label = "Add as Image Plane"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        props = context.scene.img_search_props
        return bool(props.active_image_path and os.path.exists(props.active_image_path))

    def execute(self, context):
        props = context.scene.img_search_props
        filepath = props.active_image_path
        if not filepath or not os.path.exists(filepath):
            self.report({"ERROR"}, "Image file not found on disk.")
            return {"CANCELLED"}

        img_name = props.active_image_title or "ImagePlane"
        bimg = get_or_load_image(filepath, img_name)

        w, h = bimg.size[0], bimg.size[1]
        aspect = (w / h) if (w > 0 and h > 0) else 1.0

        # Create Plane Mesh
        bpy.ops.mesh.primitive_plane_add(size=2.0, location=context.scene.cursor.location)
        plane = context.active_object
        plane.name = f"Plane_{img_name}"

        # Adjust dimensions for aspect ratio
        if aspect >= 1.0:
            plane.scale[0] = aspect
            plane.scale[1] = 1.0
        else:
            plane.scale[0] = 1.0
            plane.scale[1] = 1.0 / aspect
        bpy.ops.object.transform_apply(scale=True)

        # Create Material
        mat_name = f"Mat_{img_name}"
        mat = bpy.data.materials.new(name=mat_name)
        if hasattr(mat, "use_nodes"):
            mat.use_nodes = True
        
        # Link image to Principled BSDF
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")

        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = bimg
        tex_node.location = (-300, 0)

        if bsdf and "Base Color" in bsdf.inputs:
            links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
            # If image has alpha transparency, connect alpha
            if "Alpha" in bsdf.inputs and "Alpha" in tex_node.outputs:
                links.new(tex_node.outputs["Alpha"], bsdf.inputs["Alpha"])
                if hasattr(mat, "blend_method"):
                    mat.blend_method = "BLEND"

        plane.data.materials.append(mat)

        # Attempt to set viewport shading to Material Preview for immediate visual feedback
        for area in context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"

        self.report({"INFO"}, f"Created Image Plane: '{plane.name}'")
        return {"FINISHED"}


class IMAGE_OT_ApplyToMaterial(Operator):
    """Apply the selected image as Base Color to the active object's material"""
    bl_idname = "image_search.apply_to_material"
    bl_label = "Apply to Active Material"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        props = context.scene.img_search_props
        has_img = bool(props.active_image_path and os.path.exists(props.active_image_path))
        has_obj = bool(context.active_object and context.active_object.type == "MESH")
        return has_img and has_obj

    def execute(self, context):
        props = context.scene.img_search_props
        filepath = props.active_image_path
        obj = context.active_object

        bimg = get_or_load_image(filepath, props.active_image_title or "Texture")

        mat = obj.active_material
        if not mat:
            mat = bpy.data.materials.new(name=f"Mat_{obj.name}")
            if hasattr(mat, "use_nodes"):
                mat.use_nodes = True
            obj.data.materials.append(mat)

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")

        # Find or create Texture Node
        tex_node = None
        for n in nodes:
            if n.type == "TEX_IMAGE":
                tex_node = n
                break
        if not tex_node:
            tex_node = nodes.new("ShaderNodeTexImage")
            tex_node.location = (-300, 0)

        tex_node.image = bimg
        if bsdf and "Base Color" in bsdf.inputs:
            links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

        self.report({"INFO"}, f"Applied '{bimg.name}' to material '{mat.name}'")
        return {"FINISHED"}


class IMAGE_OT_OpenInEditor(Operator):
    """Open the selected image in Blender's Image Editor"""
    bl_idname = "image_search.open_in_editor"
    bl_label = "Open in Image Editor"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        props = context.scene.img_search_props
        return bool(props.active_image_path and os.path.exists(props.active_image_path))

    def execute(self, context):
        props = context.scene.img_search_props
        bimg = get_or_load_image(props.active_image_path, props.active_image_title or "SearchImage")

        # Set image in any visible Image Editor space
        opened = False
        for area in context.screen.areas:
            if area.type == "IMAGE_EDITOR":
                for space in area.spaces:
                    if space.type == "IMAGE_EDITOR":
                        space.image = bimg
                        opened = True
                        break

        if not opened:
            # Change any available non-3d area or notify user
            self.report({"INFO"}, f"Loaded '{bimg.name}' into Blender Images (select it in Image Editor)")
        else:
            self.report({"INFO"}, f"Opened '{bimg.name}' in Image Editor")

        return {"FINISHED"}


__REG_CLASSES = (
    IMAGE_OT_AddReference,
    IMAGE_OT_AddPlane,
    IMAGE_OT_ApplyToMaterial,
    IMAGE_OT_OpenInEditor,
)

def register():
    for cls in __REG_CLASSES:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(__REG_CLASSES):
        bpy.utils.unregister_class(cls)
