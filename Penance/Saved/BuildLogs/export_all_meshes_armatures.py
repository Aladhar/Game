import bpy
import os

out = os.environ.get("FBX_OUT")
if not out:
    raise RuntimeError("FBX_OUT environment variable missing")

# Fix old Blender render-engine name if needed.
for scene in bpy.data.scenes:
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        pass

bpy.ops.object.select_all(action="DESELECT")

selected = []
for obj in bpy.context.scene.objects:
    if obj.type in {"MESH", "ARMATURE"}:
        obj.select_set(True)
        selected.append(obj.name)

armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
if armatures:
    bpy.context.view_layer.objects.active = armatures[0]

print("Selected for FBX export:", selected)

bpy.ops.export_scene.fbx(
    filepath=out,
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    apply_unit_scale=True,
    bake_space_transform=False,
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_actions=True,
    bake_anim_use_nla_strips=False,
)

print("EXPORTED FBX:", out)
