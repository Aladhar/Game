"""Independent comparison map with seven experimental stations and originals."""
from pathlib import Path
import json,unreal as u
R=Path(__file__).resolve().parents[1];F='/Game/Enemies/Penance/Experimental';MAP=F+'/L_Penance_ExperimentShowcase'
A=u.get_editor_subsystem(u.EditorAssetSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert not A.does_asset_exist(MAP),'Preserve existing experiment map; use a new name for reruns'
assert L.new_level(MAP);world=editor.get_editor_world();world.get_world_settings().set_editor_property('default_game_mode',u.load_class(None,'/Script/Engine.GameModeBase'))
manifest=json.loads((R/'Reports/ClipManifest.json').read_text());mesh=A.load_asset(F+'/SK_Penance_Experimental');original=A.load_asset('/Game/Enemies/Penance/SK_Penance');assert mesh and original

def spawn(cls,name,xyz=(0,0,0),rot=None):
 a=E.spawn_actor_from_class(cls,u.Vector(*xyz),rot or u.Rotator());a.set_actor_label(name);return a
floor=spawn(u.StaticMeshActor,'Experiment_Floor',(0,0,-5));c=floor.get_component_by_class(u.StaticMeshComponent);c.set_static_mesh(A.load_asset('/Engine/BasicShapes/Cube'));floor.set_actor_scale3d(u.Vector(30,40,.1));c.set_collision_profile_name('BlockAll')
info={};positions={}
for i,(name,spec) in enumerate(manifest.items()):
 x,y=(i//4)*650,(i%4-1.5)*420;clip=A.load_asset(F+'/Animations/'+name);assert clip
 actor=spawn(u.SkeletalMeshActor,name,(x,y,0));comp=actor.get_component_by_class(u.SkeletalMeshComponent);comp.set_skeletal_mesh_asset(mesh);comp.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE);comp.set_update_animation_in_editor(True);comp.override_animation_data(clip,True,True,0.,1.);comp.set_collision_profile_name('NoCollision');comp.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
 label=spawn(u.TextRenderActor,'Label_'+name,(x+100,y,8));text=label.get_component_by_class(u.TextRenderComponent);text.set_text(name.replace('AN_EXP_','')+' | '+str(spec['frames']/30)+' s');text.set_world_size(22);text.set_horizontal_alignment(u.HorizTextAligment.EHTA_CENTER)
 positions[name]=[x,y,0];info[name]={'actor':actor.get_actor_label(),'asset':clip.get_path_name(),'position':[x,y,0],'loop_in_showcase':True,'clip_loop':spec['loop']}
for i,name in enumerate(['StalkWalk','Chase','Attack']):
 x,y=-650,(i-1)*450;actor=spawn(u.SkeletalMeshActor,'Original_'+name,(x,y,0));comp=actor.get_component_by_class(u.SkeletalMeshComponent);comp.set_skeletal_mesh_asset(original);comp.set_animation_mode(u.AnimationMode.ANIMATION_SINGLE_NODE);comp.set_update_animation_in_editor(True);comp.override_animation_data(A.load_asset('/Game/Enemies/Penance/Animations/AN_Penance_'+name),True,True,0.,1.);comp.set_editor_property('visibility_based_anim_tick_option',u.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
 label=spawn(u.TextRenderActor,'Original_Label_'+name,(x+100,y,8));label.get_component_by_class(u.TextRenderComponent).set_text('Original '+name);label.get_component_by_class(u.TextRenderComponent).set_world_size(22)
for name,xyz,rot,intensity in [('Experiment_Key',(100,-100,600),u.Rotator(pitch=-45,yaw=-150),4),('Experiment_Fill',(-300,400,500),u.Rotator(pitch=-40,yaw=25),2)]:
 a=spawn(u.DirectionalLight,name,xyz,rot);a.get_component_by_class(u.DirectionalLightComponent).set_intensity(intensity)
a=spawn(u.SkyLight,'Experiment_Ambient',(0,0,500));a.get_component_by_class(u.SkyLightComponent).set_editor_properties({'intensity':1.2,'source_type':u.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP,'cubemap':A.load_asset('/Engine/MapTemplates/Sky/DaylightAmbientCubemap')})
loc=u.Vector(2700,-2200,1300);cam=spawn(u.CameraActor,'Experiment_Camera',loc.to_tuple(),u.MathLibrary.find_look_at_rotation(loc,u.Vector(0,0,110)));cam.get_component_by_class(u.CameraComponent).set_editor_properties({'projection_mode':u.CameraProjectionMode.ORTHOGRAPHIC,'ortho_width':2850.});cam.set_editor_property('auto_activate_for_player',u.AutoReceiveInput.PLAYER0)
spawn(u.PlayerStart,'Experiment_PlayerStart',(1800,-1300,100));E.clear_actor_selection_set();assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
(R/'Reports/ShowcaseConstruction.json').write_text(json.dumps({'map':MAP,'stations':info,'original_stations':['StalkWalk','Chase','Attack'],'camera':cam.get_actor_label(),'note':'Attack stations repeat only for review; attack clips are authored as one-shots.'},indent=2)+'\n')
print('EXPERIMENT_SHOWCASE_SAVED',MAP)
