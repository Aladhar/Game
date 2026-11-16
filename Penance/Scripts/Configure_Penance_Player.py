"""Build the player's AnimGraph and save its Blueprint settings in UE Editor."""
import unreal as ue

assets = ue.get_editor_subsystem(ue.EditorAssetSubsystem)
blueprints = ue.BlueprintEditorLibrary
player = assets.load_asset('/Game/Player/BP_PenancePlayer')
anim = assets.load_asset('/Game/Player/Animations/ABP_PenancePlayer')
if not player or not anim:
    raise RuntimeError('Missing Penance player or Animation Blueprint')

if not ue.PenancePlayerAssetLibrary.build_player_animation_graph():
    raise RuntimeError('Player AnimGraph or runtime Blend Space evaluation failed')

reactions = {}
for field, montage_name, clip_name in (
    ('shot_reaction_montage', 'AM_CharacterShot', 'AN_PlayerShotReaction'),
    ('scared_montage', 'AM_ScaredIdle', 'AN_PlayerScaredIdle'),
):
    folder = '/Game/Player/Animations/'
    montage = assets.load_asset(folder + montage_name)
    clip = assets.load_asset(folder + clip_name)
    if not ue.PenancePlayerAssetLibrary.use_recovered_reaction(montage, clip):
        raise RuntimeError('Could not connect the recovered animation to ' + montage_name)
    reactions[field] = montage

default = ue.get_default_object(player.generated_class())
mesh = default.get_editor_property('mesh')
mesh.set_editor_property('animation_mode', ue.AnimationMode.ANIMATION_BLUEPRINT)
mesh.set_editor_property('anim_class', anim.generated_class())
overrides = mesh.get_editor_property('override_materials')
print('PENANCE_PLAYER_MATERIAL_OVERRIDES', [item.get_path_name() if item else None for item in overrides])
if overrides:
    mesh.set_editor_property('override_materials', [])
for field, montage in reactions.items():
    default.set_editor_property(field, montage)
default.set_editor_property('use_controller_rotation_yaw', True)
default.get_component_by_class(ue.CharacterMovementComponent).set_editor_property('orient_rotation_to_movement', False)
blueprints.compile_blueprint(player)

for asset in (
    assets.load_asset('/Game/Player/Animations/BS_PlayerMovement'),
    assets.load_asset('/Game/Player/Animations/BS_PlayerCrouch'),
    anim, player, *reactions.values(),
):
    if not assets.save_loaded_asset(asset, False):
        raise RuntimeError('Could not save ' + asset.get_path_name())
print('PENANCE_PLAYER_GRAPH_READY')
