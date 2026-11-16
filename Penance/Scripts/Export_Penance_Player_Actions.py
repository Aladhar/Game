"""Run with Blender --background Untitled.blend --python this_script -- <FBX output folder>."""
from pathlib import Path
import sys

import bpy

output = Path(sys.argv[sys.argv.index('--') + 1])
output.mkdir(parents=True, exist_ok=True)
armature = bpy.data.objects['Armature']
bpy.context.view_layer.objects.active = armature
# A file saved in Edit Mode evaluates action channels but freezes pose matrices.
if armature.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
armature.select_set(True)
data = armature.animation_data
data.use_nla = False

for name, filename in [
    ('Jogging Forward', 'AN_PlayerJog'),
    ('Character Shot', 'AN_PlayerShotReaction'),
    ('Scared/Looking around if afk for longer than 30 seconds', 'AN_PlayerScaredIdle'),
]:
    action = bpy.data.actions[name]
    data.action = action
    data.action_slot = action.slots[0]
    bpy.context.scene.frame_start, bpy.context.scene.frame_end = (round(frame) for frame in action.frame_range)
    bpy.ops.export_scene.fbx(
        filepath=str(output / (filename + '.fbx')),
        use_selection=True, object_types={'ARMATURE'}, add_leaf_bones=True,
        bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0.0,
    )
