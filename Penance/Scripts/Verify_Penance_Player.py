"""Read-only verification of the implemented Penance player setup (UE 5.7)."""
import unreal

failures = []
def check(ok, label):
    print(('PLAYER_CHECK_OK ' if ok else 'PLAYER_CHECK_FAIL ') + label)
    if not ok:
        failures.append(label)

def load(path):
    return unreal.EditorAssetLibrary.load_asset(path)

mesh = load('/Game/Player/MeshyPlayer/Untitled')
skeleton = load('/Game/Player/MeshyPlayer/Untitled_Skeleton')
physics = load('/Game/Player/MeshyPlayer/Untitled_PhysicsAsset')
check(mesh and mesh.get_editor_property('skeleton') == skeleton, 'Untitled uses Untitled_Skeleton')
check(mesh and mesh.get_editor_property('physics_asset') == physics, 'Untitled uses Untitled_PhysicsAsset')

walk = load('/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Walk_Forward')
jog = load('/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Jogging_Forward')
walking = load('/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Walking')
shot = load('/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Character_Shot')
scared = load('/Game/Player/MeshyPlayer/Untitled_Anim_Armature_Scared_Looking_around_if_afk_for_longer_than_30_seconds')
turn_safe = load('/Game/Player/MeshyPlayer/Untitled_Anim_Armature_AN_WalkTurnLeft_InPlace_BODY_AXIS_SAFE')
turn_yaw = load('/Game/Player/MeshyPlayer/Untitled_Anim_Armature_AN_WalkTurnLeft_InPlace_OBJECT_YAW')
for label, anim in [('walk', walk), ('jog', jog), ('walking', walking), ('shot', shot), ('scared', scared), ('safe turn', turn_safe), ('object yaw turn', turn_yaw)]:
    check(anim and anim.get_editor_property('skeleton') == skeleton, label + ' references Untitled_Skeleton')
    if anim: check(not anim.get_editor_property('enable_root_motion'), label + ' uses in-place movement')


for name in ['IA_Move','IA_Look']:
    action=load('/Game/Player/Input/'+name)
    check(action and action.get_editor_property('value_type') == unreal.InputActionValueType.AXIS2D, name + ' is Axis2D')
sprint_action=load('/Game/Player/Input/IA_Sprint')
check(sprint_action and sprint_action.get_editor_property('value_type') == unreal.InputActionValueType.BOOLEAN, 'IA_Sprint is Boolean')
shot_action=load('/Game/Player/Input/IA_TestShot')
check(shot_action and shot_action.get_editor_property('value_type') == unreal.InputActionValueType.BOOLEAN, 'IA_TestShot is Boolean')
context=load('/Game/Player/Input/IMC_Player')
check(context is not None, 'IMC_Player exists')
if context:
    mappings=context.get_editor_property('default_key_mappings').get_editor_property('mappings')
    keys={m.get_editor_property('key').get_editor_property('key_name').__str__(): m for m in mappings}
    check(all(key in keys for key in ['W','A','S','D','MouseX','MouseY','LeftShift','T']), 'IMC_Player maps WASD, mouse and Left Shift')
    for key in ['A','S']:
        mods=keys[key].get_editor_property('modifiers')
        check(any(m.get_class().get_name() == 'InputModifierNegate' for m in mods), key + ' has a Negate modifier')
    for key in ['W','S','MouseY']:
        mods=keys[key].get_editor_property('modifiers')
        check(any(m.get_class().get_name() == 'InputModifierSwizzleAxis' for m in mods), key + ' swizzles to Y')

blend=load('/Game/Player/Animations/BS_PlayerMovement')
check(blend and blend.get_editor_property('skeleton') == skeleton, 'BS_PlayerMovement uses Untitled_Skeleton')
if blend:
    samples=blend.get_editor_property('sample_data')
    check(len(samples)==3, 'standing Blend Space has idle, walk and sprint samples')
    expected=[(0.0,'AN_PlayerIdle'),(200.0,walk.get_name()),(420.0,'AN_PlayerJog')]
    for sample, (speed, name) in zip(samples, expected):
        anim=sample.get_editor_property('animation')
        value=sample.get_editor_property('sample_value').x
        check(anim and anim.get_name()==name and abs(value-speed)<0.1, 'Blend Space sample '+str(int(speed))+' uses '+name)

crouch_blend = load('/Game/Player/Animations/BS_PlayerCrouch')
check(crouch_blend and crouch_blend.get_editor_property('skeleton') == skeleton, 'crouch Blend Space uses Untitled_Skeleton')
if crouch_blend:
    samples = crouch_blend.get_editor_property('sample_data')
    by_speed = {sample.get_editor_property('sample_value').x: sample.get_editor_property('animation') for sample in samples}
    for speed, name in [(0, 'AN_PlayerCrouchIdle'), (140, 'AN_PlayerCrouchWalk')]:
        clip = by_speed.get(speed)
        check(clip and clip.get_name() == name and clip.get_editor_property('skeleton') == skeleton,
              f'crouch sample {speed} uses {name}')

for name in ('AN_PlayerStrafe', 'AN_PlayerAirborne'):
    clip = load('/Game/Player/Animations/' + name)
    check(clip and clip.get_editor_property('skeleton') == skeleton, name + ' uses Untitled_Skeleton')

material = load('/Game/Player/MeshyPlayer/M_PenancePlayer')
texture = load('/Game/Player/MeshyPlayer/Textures/Material_1_basecolor')
materials = mesh.get_editor_property('materials')
check(material and len(materials) == 1 and materials[0].get_editor_property('material_interface') == material, 'Untitled has M_PenancePlayer in its original material slot')
check(texture and texture.get_editor_property('srgb') and texture.blueprint_get_size_x() == 2048
      and texture.blueprint_get_size_y() == 2048, 'source base color is sRGB at 2048 x 2048')
if material:
    edit = unreal.MaterialEditingLibrary
    color = edit.get_material_property_input_node(material, unreal.MaterialProperty.MP_BASE_COLOR)
    metallic = edit.get_material_property_input_node(material, unreal.MaterialProperty.MP_METALLIC)
    rough = edit.get_material_property_input_node(material, unreal.MaterialProperty.MP_ROUGHNESS)
    check(color and color.get_editor_property('texture') == texture, 'material base color uses original PNG')
    check(metallic and metallic.get_editor_property('r') == 0, 'material metallic is 0')
    check(rough and rough.get_editor_property('r') == 0.75, 'material roughness is 0.75')
    check(not material.get_editor_property('two_sided'), 'material is single sided')
    check(material.get_editor_property('used_with_skeletal_mesh'), 'material compiles for skeletal meshes')

abp=load('/Game/Player/Animations/ABP_PenancePlayer')
check(abp and abp.get_editor_property('target_skeleton') == skeleton, 'ABP_PenancePlayer uses Untitled_Skeleton')

shot_montage=load('/Game/Player/Animations/AM_CharacterShot')
scared_montage=load('/Game/Player/Animations/AM_ScaredIdle')
for montage, name in ((shot_montage, 'AN_PlayerShotReaction'), (scared_montage, 'AN_PlayerScaredIdle')):
    clip = montage.get_first_anim_reference() if montage else None
    check(clip and clip.get_name() == name and clip.get_editor_property('skeleton') == skeleton,
          name + ' uses the authored Blender action on Untitled_Skeleton')

player_bp=load('/Game/Player/BP_PenancePlayer')
player_cdo=unreal.get_default_object(player_bp.generated_class()) if player_bp else None
check(player_cdo is not None, 'BP_PenancePlayer generated class loads')
if player_cdo:
    check(player_cdo.get_editor_property('shot_reaction_montage') == shot_montage, 'player assigns shot montage')
    check(player_cdo.get_editor_property('scared_montage') == scared_montage, 'player assigns scared montage')
    player_mesh=player_cdo.get_editor_property('mesh')
    mesh_asset=player_mesh.get_editor_property('skeletal_mesh_asset')
    check(mesh_asset == mesh, 'BP_PenancePlayer mesh is Untitled')
    check(mesh_asset.get_editor_property('physics_asset') == physics, 'BP_PenancePlayer mesh uses Untitled_PhysicsAsset')
    check(player_mesh.get_editor_property('physics_asset_override') == physics, 'BP_PenancePlayer explicitly assigns Untitled_PhysicsAsset')
    check(player_mesh.get_editor_property('animation_mode') == unreal.AnimationMode.ANIMATION_BLUEPRINT, 'player mesh uses Animation Blueprint mode')
    check(player_mesh.get_editor_property('anim_class') == abp.generated_class(), 'player mesh uses ABP_PenancePlayer')
    check(abs(player_cdo.get_editor_property('walk_speed')-200.0)<0.1, 'walk speed is 200 cm/s')
    check(abs(player_cdo.get_editor_property('sprint_speed')-420.0)<0.1, 'sprint speed is 420 cm/s')
    movement=player_cdo.get_component_by_class(unreal.CharacterMovementComponent)
    check(movement and abs(movement.get_editor_property('max_acceleration')-1000.0)<0.1, 'max acceleration is 1000 cm/s^2')
    check(movement and abs(movement.get_editor_property('braking_deceleration_walking')-1000.0)<0.1, 'walking braking is 1000 cm/s^2')
    check(movement and not movement.get_editor_property('orient_rotation_to_movement'), 'strafe and reverse preserve yaw')
    check(player_cdo.get_editor_property('use_controller_rotation_yaw'), 'controller yaw drives character facing')
    check(abs(movement.get_editor_property('rotation_rate').yaw-360.0)<0.1, 'character yaw rotation rate is 360 deg/s')
    boom = player_cdo.get_editor_property('camera_boom')
    camera = player_cdo.get_editor_property('follow_camera')
    check(boom.get_editor_property('use_pawn_control_rotation') and not camera.get_editor_property('use_pawn_control_rotation'), 'camera boom alone uses controller rotation')
    check(not player_mesh.get_editor_property('override_materials'), 'Blueprint uses mesh material without override')

gm_class=unreal.load_class(None, '/Script/PenanceDemoUE.PenanceDemoGameMode')
gm_cdo=unreal.get_default_object(gm_class) if gm_class else None
default_pawn=gm_cdo.get_editor_property('default_pawn_class') if gm_cdo else None
check(default_pawn and default_pawn.get_path_name() == '/Game/Player/BP_PenancePlayer.BP_PenancePlayer_C', 'PenanceDemoGameMode defaults to BP_PenancePlayer')

unreal.EditorLevelLibrary.load_level('/Game/Maps/Penance_Persistent')
actors=unreal.EditorLevelLibrary.get_all_level_actors()
starts=[a for a in actors if a.get_class().get_name()=='PlayerStart']
check(len(starts)==1, 'persistent map has exactly one PlayerStart')

if failures:
    print('PENANCE_PLAYER_VERIFICATION_FAILED', len(failures))
    raise RuntimeError('; '.join(failures))
print('PENANCE_PLAYER_VERIFICATION_PASSED')
