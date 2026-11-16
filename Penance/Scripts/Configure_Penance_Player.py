"""Configure the existing Penance player Blueprint and build its AnimGraph in UE 5.7."""
import unreal

player_path = '/Game/Player/BP_PenancePlayer'
player_bp = unreal.EditorAssetLibrary.load_asset(player_path)
if not player_bp:
    raise RuntimeError('Missing player Blueprint: ' + player_path)

player_class = unreal.load_class(None, '/Script/PenanceDemoUE.PenancePlayerCharacter')
if not player_class:
    raise RuntimeError('Could not load APenancePlayerCharacter')
unreal.BlueprintEditorLibrary.reparent_blueprint(player_bp, player_class)
unreal.BlueprintEditorLibrary.compile_blueprint(player_bp)

anim_bp = unreal.EditorAssetLibrary.load_asset('/Game/Player/Animations/ABP_PenancePlayer')
anim_class = unreal.load_class(None, '/Script/PenanceDemoUE.PenancePlayerAnimInstance')
if not anim_bp or not anim_class:
    raise RuntimeError('Missing Anim Blueprint or native Anim Instance class')
unreal.BlueprintEditorLibrary.reparent_blueprint(anim_bp, anim_class)
unreal.BlueprintEditorLibrary.compile_blueprint(anim_bp)

if not unreal.PenancePlayerAssetLibrary.build_player_animation_graph():
    raise RuntimeError('BuildPlayerAnimationGraph returned false')

# Persist the animation class and physics asset on the Blueprint's mesh template
# so the setup is visible and editable in the component details panel.
player_class = player_bp.generated_class()
player_default = unreal.get_default_object(player_class)
mesh_component = player_default.get_editor_property('mesh')
mesh_asset = unreal.EditorAssetLibrary.load_asset('/Game/Player/MeshyPlayer/Untitled')
physics_asset = unreal.EditorAssetLibrary.load_asset('/Game/Player/MeshyPlayer/Untitled_PhysicsAsset')
if not mesh_asset or not physics_asset:
    raise RuntimeError('Missing Untitled mesh or physics asset')
mesh_component.set_editor_property('skeletal_mesh_asset', mesh_asset)
mesh_component.set_editor_property('physics_asset_override', physics_asset)
mesh_component.set_editor_property('animation_mode', unreal.AnimationMode.ANIMATION_BLUEPRINT)
mesh_component.set_editor_property('anim_class', anim_bp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(player_bp)

for path in [
    '/Game/Player/Input/IA_Move', '/Game/Player/Input/IA_Look',
    '/Game/Player/Input/IA_Sprint', '/Game/Player/Input/IMC_Player',
    '/Game/Player/Animations/BS_PlayerMovement',
    '/Game/Player/Animations/ABP_PenancePlayer',
    '/Game/Player/Animations/AM_CharacterShot',
    '/Game/Player/Animations/AM_ScaredIdle', player_path,
]:
    obj = unreal.EditorAssetLibrary.load_asset(path)
    if not obj:
        raise RuntimeError('Missing configured asset ' + path)
    unreal.EditorAssetLibrary.save_loaded_asset(obj)
    print('PENANCE_PLAYER_CONFIGURED', obj.get_path_name(), obj.get_class().get_name())

player_class = player_bp.generated_class()
player_default = unreal.get_default_object(player_class)
mesh = player_default.get_editor_property('mesh')
print('PENANCE_PLAYER_PARENT', player_class.get_path_name())
print('PENANCE_PLAYER_MESH', mesh.get_editor_property('skeletal_mesh_asset').get_path_name())
print('PENANCE_PLAYER_SKELETON', mesh_asset.get_editor_property('skeleton').get_path_name())
print('PENANCE_PLAYER_PHYSICS', mesh.get_editor_property('physics_asset_override').get_path_name())
print('PENANCE_PLAYER_ANIM_CLASS', mesh.get_editor_property('anim_class').get_path_name())
print('PENANCE_PLAYER_ABP', anim_bp.generated_class().get_path_name())
print('PENANCE_PLAYER_GRAPH_READY')
