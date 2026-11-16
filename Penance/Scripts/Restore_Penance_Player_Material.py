"""Import the supplied PNG and repair Untitled's existing material slot in UE Editor."""
from pathlib import Path

import unreal as ue

folder = '/Game/Player/MeshyPlayer'
texture_path = folder + '/Textures/Material_1_basecolor'
material_path = folder + '/M_PenancePlayer'
source = Path(ue.Paths.project_content_dir()) / 'Player/MeshyPlayer/Material_1_basecolor.png'
assets = ue.get_editor_subsystem(ue.EditorAssetSubsystem)
tools = ue.AssetToolsHelpers.get_asset_tools()

if not assets.does_asset_exist(texture_path):
    if not source.is_file():
        raise RuntimeError('Missing original Penance texture: ' + str(source.resolve()))
    ue.SystemLibrary.execute_console_command(None, "Interchange.FeatureFlags.Import.SyncToBrowser 0")
    task = ue.AssetImportTask()
    task.set_editor_property('filename', str(source.resolve()))
    task.set_editor_property('destination_path', folder + '/Textures')
    task.set_editor_property('automated', True)
    task.set_editor_property('save', True)
    tools.import_asset_tasks([task])
texture = assets.load_asset(texture_path)
if not isinstance(texture, ue.Texture2D):
    raise RuntimeError('Base color import did not produce a Texture2D')
texture.set_editor_property('srgb', True)
assert assets.save_loaded_asset(texture)

editor = ue.MaterialEditingLibrary
if assets.does_asset_exist(material_path):
    material = assets.load_asset(material_path)
else:
    material = tools.create_asset('M_PenancePlayer', folder, ue.Material, ue.MaterialFactoryNew())
    sampler = editor.create_material_expression(material, ue.MaterialExpressionTextureSample, -420, -120)
    sampler.set_editor_property('texture', texture)
    assert editor.connect_material_property(sampler, 'RGB', ue.MaterialProperty.MP_BASE_COLOR)
    for y, value, prop in [
        (170, 0.0, ue.MaterialProperty.MP_METALLIC),
        (255, 0.75, ue.MaterialProperty.MP_ROUGHNESS),
    ]:
        constant = editor.create_material_expression(material, ue.MaterialExpressionConstant, -220, y)
        constant.set_editor_property('r', value)
        assert editor.connect_material_property(constant, '', prop)
    material.set_editor_property('material_domain', ue.MaterialDomain.MD_SURFACE)
    material.set_editor_property('blend_mode', ue.BlendMode.BLEND_OPAQUE)
    material.set_editor_property('shading_model', ue.MaterialShadingModel.MSM_DEFAULT_LIT)
    material.set_editor_property('two_sided', False)
material.set_editor_property('used_with_skeletal_mesh', True)
editor.recompile_material(material)
assert assets.save_loaded_asset(material, False)

mesh = assets.load_asset(folder + '/Untitled')
slots = mesh.get_editor_property('materials')
if len(slots) != 1:
    raise RuntimeError('Untitled material slots changed; inspect before assigning')
if slots[0].get_editor_property('material_interface') != material:
    if not ue.PenancePlayerAssetLibrary.assign_skeletal_mesh_material(mesh, 0, material):
        raise RuntimeError('Could not update the original material slot')
    assert assets.save_loaded_asset(mesh)
print('PENANCE_PLAYER_MATERIAL_RESTORED', texture.get_path_name(), material.get_path_name())
