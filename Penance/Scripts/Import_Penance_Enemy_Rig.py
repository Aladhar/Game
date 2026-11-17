"""Import the Blender rig and verify its saved Unreal assets in an isolated editor session."""
import json
from pathlib import Path
import re
import sys

import unreal as ue

folder = '/Game/Enemies/Penance'
root = Path(ue.Paths.project_dir()).resolve()
output = Path(sys.argv[1])
source_audit = json.loads((output / 'Blender_Rig_Checks.json').read_text())
verify_only = '--verify-only' in sys.argv
assets = ue.get_editor_subsystem(ue.EditorAssetSubsystem)
tools = ue.AssetToolsHelpers.get_asset_tools()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def import_file(filename, directory, name, options=None, factory=None):
    require(filename.is_file(), 'Missing file: ' + str(filename))
    task = ue.AssetImportTask()
    for key, value in {
        'filename': str(filename), 'destination_path': directory,
        'destination_name': name, 'automated': True, 'save': False,
    }.items():
        task.set_editor_property(key, value)
    if options is not None:
        task.set_editor_property('options', options)
    if factory is not None:
        task.set_editor_property('factory', factory)
    tools.import_asset_tasks([task])
    return task.get_objects()


def fbx_options(mesh_import, skeleton=None, physics=None):
    settings = ue.FbxImportUI()
    for key, value in {
        'automated_import_should_detect_type': False,
        'mesh_type_to_import': (ue.FBXImportType.FBXIT_SKELETAL_MESH if mesh_import
                                else ue.FBXImportType.FBXIT_ANIMATION),
        'import_mesh': mesh_import, 'import_animations': not mesh_import,
        'import_as_skeletal': True, 'import_materials': False, 'import_textures': False,
        'create_physics_asset': mesh_import and physics is None, 'skeleton': skeleton,
        'physics_asset': physics,
    }.items():
        settings.set_editor_property(key, value)
    data = settings.get_editor_property('skeletal_mesh_import_data' if mesh_import
                                        else 'anim_sequence_import_data')
    for key, value in {
        'convert_scene': True, 'convert_scene_unit': True, 'force_front_x_axis': True,
        'import_uniform_scale': 1.0,
    }.items():
        data.set_editor_property(key, value)
    if not mesh_import:
        data.set_editor_property('use_default_sample_rate', False)
        data.set_editor_property('custom_sample_rate', int(source_audit['fps']))
    return settings


def final_name(asset, name):
    path = folder + '/' + name
    require(asset is not None, 'Importer did not create ' + name)
    if not asset.get_path_name().startswith(path + '.'):
        require(not assets.does_asset_exist(path), 'Asset already exists at ' + path)
        require(assets.rename_loaded_asset(asset, path), 'Could not name ' + path)


mesh_path = folder + '/SK_Penance'
material_path = folder + '/Materials/M_Penance'
texture_path = folder + '/Materials/T_Penance_BaseColor'
mesh = assets.load_asset(mesh_path) if assets.does_asset_exist(mesh_path) else None
if mesh is None:
    require(not verify_only, 'Cannot reload ' + mesh_path)
    skeleton_path, physics_path = folder + '/SKEL_Penance', folder + '/PHYS_Penance'
    existing_skeleton = assets.load_asset(skeleton_path) if assets.does_asset_exist(skeleton_path) else None
    existing_physics = assets.load_asset(physics_path) if assets.does_asset_exist(physics_path) else None
    imported = import_file(root / 'Built/FBX/SK_Penance.fbx', folder, 'SK_Penance',
                           fbx_options(True, existing_skeleton, existing_physics))
    mesh = next((item for item in imported if isinstance(item, ue.SkeletalMesh)), None)
require(isinstance(mesh, ue.SkeletalMesh), 'FBX import did not produce a Skeletal Mesh')

skeleton = mesh.get_editor_property('skeleton')
physics = mesh.get_editor_property('physics_asset')
if not verify_only:
    final_name(skeleton, 'SKEL_Penance')
    final_name(physics, 'PHYS_Penance')

texture = assets.load_asset(texture_path) if assets.does_asset_exist(texture_path) else None
if texture is None:
    require(not verify_only, 'Could not reload ' + texture_path)
    ue.SystemLibrary.execute_console_command(None, 'Interchange.FeatureFlags.Import.SyncToBrowser 0')
    imported = import_file(root / 'Built/FBX/SK_Penance_BaseColor.png',
                           folder + '/Materials', 'T_Penance_BaseColor', factory=ue.TextureFactory())
    texture = next((item for item in imported if isinstance(item, ue.Texture2D)), None)
    if texture and texture.get_name() != 'T_Penance_BaseColor':
        require(assets.rename_loaded_asset(texture, texture_path), 'Could not name base color')
require(isinstance(texture, ue.Texture2D), 'Could not import the original base color')

material = assets.load_asset(material_path) if assets.does_asset_exist(material_path) else None
if material is None:
    require(not verify_only, 'Could not reload ' + material_path)
    material = tools.create_asset('M_Penance', folder + '/Materials', ue.Material, ue.MaterialFactoryNew())
    require(material is not None, 'Could not create ' + material_path)
    editor = ue.MaterialEditingLibrary
    sampler = editor.create_material_expression(material, ue.MaterialExpressionTextureSample, -340, -100)
    sampler.set_editor_property('texture', texture)
    require(editor.connect_material_property(sampler, 'RGB', ue.MaterialProperty.MP_BASE_COLOR),
            'Could not assign the Blender base color')
    # Unreal Default Lit uses the same 0.0 metallic and 0.5 roughness/specular defaults.
    material.set_editor_property('used_with_skeletal_mesh', True)
    editor.recompile_material(material)

slots = mesh.get_editor_property('materials')
require(len(slots) == 1, 'Expected the single original material slot')
if not verify_only and slots[0].get_editor_property('material_interface') != material:
    require(ue.PenancePlayerAssetLibrary.assign_skeletal_mesh_material(mesh, 0, material),
            'Could not assign the material to the enemy skeletal mesh')

require(mesh.get_editor_property('materials')[0].get_editor_property('material_interface') == material,
        'Base color material is not bound to the mesh')
require(skeleton.get_name() == 'SKEL_Penance' and physics.get_name() == 'PHYS_Penance',
        'Expected the named skeleton and physics asset')

# Use a transient component to validate the actual reference skeleton and imported bounds.
component = ue.SkeletalMeshComponent()
component.set_skeletal_mesh_asset(mesh)
bone_names = [str(component.get_bone_name(i)) for i in range(component.get_num_bones())]
require(bone_names and bone_names[0] == 'root' and sorted(bone_names) == sorted(source_audit['bones']),
        'Unexpected reference skeleton: ' + str(bone_names))
parents = {name: str(component.get_parent_bone(name)) for name in bone_names}
require(parents['pelvis'] == 'root' and parents['bell_r'] == 'hand_r', 'Broken bone hierarchy')
pose_api = ue.AnimPoseExtensions
reference = pose_api.get_reference_pose(skeleton)


def get_position(bone):
    return pose_api.get_bone_pose(reference, bone, ue.AnimPoseSpaces.WORLD).translation


bounds = mesh.get_imported_bounds()
height = 2 * bounds.box_extent.z
require(abs(height - source_audit['source_height_cm']) < 0.2, 'Unexpected physical height: ' + str(height))
root_position = get_position('root')
toe_forward = get_position('ball_l') - get_position('foot_l')
root_scale = pose_api.get_bone_pose(reference, 'root', ue.AnimPoseSpaces.LOCAL).scale3d
print('PENANCE_UNREAL_REFERENCE', height, root_position, toe_forward, root_scale)
require(root_position.length() < 0.1, 'Root is not at the origin: ' + str(root_position))
require(toe_forward.x > abs(toe_forward.y), 'Character does not face Unreal +X: ' + str(toe_forward))
require((root_scale - ue.Vector(1, 1, 1)).length() < .001, 'Root scale is not 1: ' + str(root_scale))

if not verify_only:
    for asset in (texture, material, skeleton, physics, mesh):
        require(assets.save_loaded_asset(asset, False), 'Could not save ' + asset.get_path_name())

require(ue.SkeletalMeshEditorSubsystem.is_physics_asset_compatible(mesh, physics),
        'Physics asset has a body on an incompatible bone')
physics_text = output / 'Unreal_Physics_Bodies.t3d'
export = ue.AssetExportTask()
for key, value in {
    'object': physics, 'filename': str(physics_text), 'automated': True,
    'prompt': False, 'replace_identical': True,
}.items():
    export.set_editor_property(key, value)
require(ue.Exporter.run_asset_export_task(export), 'Could not inspect physics asset bodies')
physics_bones = re.findall(r'^\s*BoneName="?([a-z0-9_]+)', physics_text.read_text(), re.MULTILINE)
require(physics_bones and set(physics_bones) <= set(bone_names),
        'Unexpected physics coverage: ' + str(physics_bones))

audit = {
    'height_cm': height, 'bone_count': len(bone_names), 'parents': parents,
    'forward': '+X', 'physics_bones': physics_bones, 'material': material.get_path_name(),
    'mesh_reloaded': verify_only,
}

if not verify_only:
    # Import the Blender review animation on the new skeleton but leave it unsaved.
    clip_path = Path(sys.argv[2])
    imported = import_file(clip_path, folder + '/_Validation', 'AN_Penance_Validation',
                           fbx_options(False, skeleton))
    clip = next((item for item in imported if isinstance(item, ue.AnimSequence)), None)
    require(clip is not None and clip.get_editor_property('skeleton') == skeleton,
            'Could not evaluate the Blender poses on the Unreal skeleton')
    options = ue.AnimPoseEvaluationOptions()
    options.set_editor_property('optional_skeletal_mesh', mesh)
    options.set_editor_property('should_retarget', False)
    print('PENANCE_UNREAL_CLIP_LENGTH', clip.get_play_length())
    bones_to_check = ('root', 'head', 'hand_l', 'hand_r', 'calf_l', 'calf_r', 'shrine_mount')
    results = {}
    neutral = None
    frames = (1, 20, 40, 60, 80, 100, 120)
    for (label, _), frame in zip(source_audit['poses'].items(), frames):
        time = min((frame - 1) / source_audit['fps'], clip.get_play_length())
        pose = pose_api.get_anim_pose_at_time(clip, time, options)
        positions = {bone: pose_api.get_bone_pose(pose, bone, ue.AnimPoseSpaces.WORLD).translation
                     for bone in bones_to_check}
        if neutral is None:
            neutral = positions
        offsets = {bone: round((positions[bone] - neutral[bone]).length(), 3) for bone in bones_to_check}
        print('PENANCE_UNREAL_POSE', label, time, offsets)
        require(offsets['root'] < 0.1, 'Grounded root drifted in ' + label)
        if frame in (1, 120):
            require(max(offsets.values()) < 0.1, 'Neutral pose did not match')
        else:
            require(max(offsets.values()) > 3., 'Expected visible bone motion in ' + label)
        results[label] = offsets
    audit['pose_joint_motion_cm'] = results

report = output / ('Unreal_Rig_Reload_Check.json' if verify_only else 'Unreal_Rig_Import_Check.json')
report.write_text(json.dumps(audit, indent=2) + '\n')
print('PENANCE_ENEMY_UNREAL_RIG_PASSED', json.dumps(audit))

