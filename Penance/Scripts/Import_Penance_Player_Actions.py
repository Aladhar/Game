"""Import animation-only Blender exports onto the existing Untitled_Skeleton."""
from pathlib import Path
import sys

import unreal as ue

source = Path(sys.argv[1])
folder = '/Game/Player/Animations'
skeleton = ue.load_asset('/Game/Player/MeshyPlayer/Untitled_Skeleton')
assets = ue.get_editor_subsystem(ue.EditorAssetSubsystem)
tools = ue.AssetToolsHelpers.get_asset_tools()
for name in ('AN_PlayerJog', 'AN_PlayerShotReaction', 'AN_PlayerScaredIdle'):
    path = folder + '/' + name
    if assets.does_asset_exist(path):
        continue
    filename = source / (name + '.fbx')
    if not filename.is_file():
        raise RuntimeError('Missing ' + str(filename))
    options = ue.FbxImportUI()
    options.set_editor_property('automated_import_should_detect_type', False)
    options.set_editor_property('mesh_type_to_import', ue.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property('import_mesh', False)
    options.set_editor_property('import_animations', True)
    options.set_editor_property('import_as_skeletal', True)
    options.set_editor_property('skeleton', skeleton)
    anim_data = options.get_editor_property('anim_sequence_import_data')
    anim_data.set_editor_property('use_default_sample_rate', False)
    anim_data.set_editor_property('custom_sample_rate', 60)
    task = ue.AssetImportTask()
    task.set_editor_property('filename', str(filename))
    task.set_editor_property('destination_path', folder)
    task.set_editor_property('destination_name', name)
    task.set_editor_property('automated', True)
    task.set_editor_property('options', options)
    tools.import_asset_tasks([task])
    clip = assets.load_asset(path)
    if not isinstance(clip, ue.AnimSequence) or clip.get_editor_property('skeleton') != skeleton:
        raise RuntimeError('Expected an animation on Untitled_Skeleton at ' + path)
    clip.set_editor_property('enable_root_motion', False)
    if not assets.save_loaded_asset(clip, False):
        raise RuntimeError('Could not save ' + path)
    print('PENANCE_BLENDER_ACTION_IMPORTED', path, clip.get_play_length())
