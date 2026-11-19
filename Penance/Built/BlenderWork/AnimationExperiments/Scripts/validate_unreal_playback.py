"""Fresh UE 5.7.4 reload, actual PIE advancement at every review station,
plus native three-quarter screenshots. Raises/writes failure on any failed check.
"""
import unreal as u,json,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];F='/Game/Enemies/Penance/Experimental';out=R/'Previews/Unreal';out.mkdir(parents=True,exist_ok=True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem);editor=u.get_editor_subsystem(u.UnrealEditorSubsystem);A=u.get_editor_subsystem(u.EditorAssetSubsystem)
assert '5.7.4' in u.SystemLibrary.get_engine_version();assert L.load_level(F+'/L_Penance_ExperimentShowcase')
manifest=json.loads((R/'Reports/ClipManifest.json').read_text());mesh=A.load_asset(F+'/SK_Penance_Experimental');skel=A.load_asset('/Game/Enemies/Penance/SKEL_Penance');assert mesh.get_editor_property('skeleton')==skel
assert abs(mesh.get_imported_bounds().box_extent.z*2-230)<.01
ref=u.AnimPoseExtensions.get_reference_pose(skel);names=list(map(str,u.AnimPoseExtensions.get_bone_names(ref)));assert len(names)==31
foot=u.AnimPoseExtensions.get_bone_pose(ref,'foot_l',u.AnimPoseSpaces.WORLD).translation;ball=u.AnimPoseExtensions.get_bone_pose(ref,'ball_l',u.AnimPoseSpaces.WORLD).translation;assert (ball-foot).x>abs((ball-foot).y)
report={'engine':u.SystemLibrary.get_engine_version(),'fresh_reload':True,'skeleton':skel.get_path_name(),'mesh_height_cm':mesh.get_imported_bounds().box_extent.z*2,'bone_count':len(names),'orientation_forward_x':True,'native_clips':{}}
for name,s in manifest.items():
 clip=A.load_asset(F+'/Animations/'+name);assert clip.get_editor_property('skeleton')==skel;assert not clip.get_editor_property('enable_root_motion');assert abs(clip.get_play_length()-s['frames']/30)<.001
 frames=u.AnimationLibrary.get_num_frames(clip);assert frames==s['frames'],(name,'Unexpected native frame count',frames,s['frames'])
 opt=u.AnimPoseEvaluationOptions();root=[]
 for f in range(s['frames']+1):
  pose=u.AnimPoseExtensions.get_anim_pose_at_time(clip,f/30,opt);t=u.AnimPoseExtensions.get_bone_pose(pose,'root',u.AnimPoseSpaces.LOCAL);root.append(list(t.translation.to_tuple())+list(t.rotation.to_tuple())+list(t.scale3d.to_tuple()))
 assert max(abs(a-b) for row in root for a,b in zip(row,root[0]))<.001
 report['native_clips'][name]={'duration':clip.get_play_length(),'frames_evaluated':len(root),'sample_rate':frames/clip.get_play_length(),'root_stationary':True}
cap=E.spawn_actor_from_class(u.SceneCapture2D,u.Vector());cap.set_actor_label('Transient_Experiment_Capture')
u.EditorPythonScripting.set_keep_python_script_alive(True);started=time.monotonic();last=started;phase='start';busy=False;world=None;found=None;first=None;capture=None;cc=None;rt=None;index=0;pending=None

def bones(comp):return {b:list(comp.get_bone_transform(b,u.RelativeTransformSpace.RTS_COMPONENT).translation.to_tuple()) for b in ['root','pelvis','hand_l','hand_r','foot_l','foot_r','head']}
def tick(dt):
 global phase,busy,last,world,found,first,capture,cc,rt,index,pending
 if busy:return
 busy=True
 try:
  now=time.monotonic()
  if now-started>180:raise RuntimeError('PIE animation verification timed out')
  if phase=='start':
   if now-started<2:return
   L.editor_request_begin_play();phase='wait';last=now
  elif phase=='wait':
   if not L.is_in_play_in_editor() or now-last<2:return
   world=editor.get_game_world()
   if not world:return
   found={a.get_actor_label():a for a in u.GameplayStatics.get_all_actors_of_class(world,u.SkeletalMeshActor)}
   if not all(n in found for n in manifest):return
   first={n:bones(found[n].get_component_by_class(u.SkeletalMeshComponent)) for n in manifest};phase='advance';last=now
  elif phase=='advance':
   if now-last<.57:return
   report['PIE']={'started':True,'stations':{},'all_actor_scales_unit':True}
   for n in manifest:
    comp=found[n].get_component_by_class(u.SkeletalMeshComponent);after=bones(comp);movement=max(abs(x-y) for b in after if b!='root' for x,y in zip(first[n][b],after[b]));rootdev=max(abs(x-y) for x,y in zip(first[n]['root'],after['root']));assert movement>.01,(n,'Animation did not advance',movement);assert rootdev<.001,(n,'Runtime root moved',rootdev);assert (found[n].get_actor_scale3d()-u.Vector(1,1,1)).length()<.001
    report['PIE']['stations'][n]={'sampled_bone_movement_cm':movement,'root_deviation_cm':rootdev}
   capture=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.SceneCapture2D) if a.get_actor_label()=='Transient_Experiment_Capture');cc=capture.get_component_by_class(u.SceneCaptureComponent2D);rt=u.RenderingLibrary.create_render_target2d(world,900,1000,u.TextureRenderTargetFormat.RTF_RGBA8);cc.set_editor_properties({'texture_target':rt,'projection_type':u.CameraProjectionMode.ORTHOGRAPHIC,'ortho_width':370.,'capture_source':u.SceneCaptureSource.SCS_FINAL_COLOR_LDR,'capture_every_frame':False,'capture_on_movement':False,'primitive_render_mode':u.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST})
   u.SystemLibrary.execute_console_command(world,'r.EyeAdaptationQuality 0');phase='capture';last=now
  elif phase=='capture':
   if pending:
    if now-last<.5:return
    cc.capture_scene();u.RenderingLibrary.export_render_target(world,rt,str(out),pending+'.png');pending=None
   if index>=len(manifest):L.editor_request_end_play();phase='end';return
   n=list(manifest)[index];index+=1;actor=found[n];comp=actor.get_component_by_class(u.SkeletalMeshComponent);comp.stop();spec=manifest[n];comp.set_position((spec.get('impact',round(spec['frames']*.25)+1)-1)/30,False)
   cc.clear_show_only_components();cc.show_only_actor_components(actor);floor=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.StaticMeshActor) if a.get_actor_label()=='Experiment_Floor');cc.show_only_actor_components(floor)
   loc=actor.get_actor_location()+u.Vector(600,-500,220);target=actor.get_actor_location()+u.Vector(25,0,115);capture.set_actor_location(loc,False,False);capture.set_actor_rotation(u.MathLibrary.find_look_at_rotation(loc,target),False);pending=n;last=now
  elif phase=='end':
   if L.is_in_play_in_editor():return
   (R/'Reports/UnrealPlaybackValidation.json').write_text(json.dumps(report,indent=2)+'\n');print('EXPERIMENT_PIE_ALL_SEVEN_ADVANCED',json.dumps(report['PIE']));u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
 except Exception:
  (R/'Reports/UnrealPlaybackFailure.txt').write_text(traceback.format_exc());print('EXPERIMENT_PIE_FAILURE',traceback.format_exc());L.editor_request_end_play();u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
 finally:busy=False
handle=u.register_slate_post_tick_callback(tick)
