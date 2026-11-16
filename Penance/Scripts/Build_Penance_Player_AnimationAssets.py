"""Create player Blend Space, Animation Blueprint, and reaction Montages in UE Editor."""
import unreal

TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
SKELETON_PATH = '/Game/Player/MeshyPlayer/Untitled_Skeleton'
ANIMATION_FOLDER = '/Game/Player/Animations'
unreal.EditorAssetLibrary.make_directory(ANIMATION_FOLDER)
skeleton = unreal.EditorAssetLibrary.load_asset(SKELETON_PATH)
if not skeleton:
    raise RuntimeError('Missing Penance player skeleton: ' + SKELETON_PATH)


def create_or_load(name, asset_class, factory):
    path = ANIMATION_FOLDER + '/' + name
    obj = unreal.EditorAssetLibrary.load_asset(path)
    if obj:
        print('PENANCE_PLAYER_ASSET_REUSED', obj.get_path_name())
        return obj
    obj = TOOLS.create_asset(name, ANIMATION_FOLDER, asset_class, factory)
    if not obj:
        raise RuntimeError('Failed to create ' + path)
    print('PENANCE_PLAYER_ASSET_CREATED', obj.get_path_name())
    return obj


blend_factory = unreal.BlendSpaceFactory1D()
blend_factory.set_editor_property('target_skeleton', skeleton)
blend_space = create_or_load('BS_PlayerMovement', unreal.BlendSpace1D, blend_factory)

anim_factory = unreal.AnimBlueprintFactory()
anim_factory.set_editor_property('target_skeleton', skeleton)
anim_factory.set_editor_property('parent_class', unreal.AnimInstance.static_class())
anim_blueprint = create_or_load('ABP_PenancePlayer', unreal.AnimBlueprint, anim_factory)

for name, animation_name in [
    ('AM_CharacterShot', 'Untitled_Anim_Armature_Character_Shot'),
    ('AM_ScaredIdle', 'Untitled_Anim_Armature_Scared_Looking_around_if_afk_for_longer_than_30_seconds'),
]:
    animation_path = '/Game/Player/MeshyPlayer/' + animation_name
    sequence = unreal.EditorAssetLibrary.load_asset(animation_path)
    if not sequence:
        raise RuntimeError('Missing reaction animation: ' + animation_path)
    montage_factory = unreal.AnimMontageFactory()
    montage_factory.set_editor_property('source_animation', sequence)
    montage_factory.set_editor_property('target_skeleton', skeleton)
    montage = create_or_load(name, unreal.AnimMontage, montage_factory)

for obj in [blend_space, anim_blueprint]:
    unreal.EditorAssetLibrary.save_loaded_asset(obj)
for name in ['AM_CharacterShot', 'AM_ScaredIdle']:
    obj = unreal.EditorAssetLibrary.load_asset(ANIMATION_FOLDER + '/' + name)
    unreal.EditorAssetLibrary.save_loaded_asset(obj)

print('PENANCE_PLAYER_ANIMATION_ASSETS_READY')
