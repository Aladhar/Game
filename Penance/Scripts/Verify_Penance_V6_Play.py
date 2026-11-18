"""Actual PIE: saved level, collision, possession, streaming and continuous opening walk.
No checkpoint teleports. Only the existing House01 portal changes pawn position.
Output honestly distinguishes automated traversal from a human manual walkthrough.
"""
from pathlib import Path
import sys,json,time,math,traceback
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent));import Penance_Town_V6_Design as p
root=Path(__file__).resolve().parents[1];out=root/'Docs/V6';PROBE_ONLY=Path('/private/tmp/PenanceV6/ProbeOnly').exists();shots=out/'Views';shots.mkdir(exist_ok=True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level(p.MAP)
import Complete_Penance_V6_Foliage;Complete_Penance_V6_Foliage.apply()
cap=A.spawn_actor_from_class(u.SceneCapture2D,u.Vector());cap.set_actor_label('V6_Transient_ValidationCapture')
report=dict(map=p.MAP,issues=[],runtime={},screenshots=[],traversal='Continuous AddMovementInput on possessed pawn; no checkpoint teleports; House01 uses original portal',human_manual_walkthrough=False)
start=time.monotonic();last=start;phase='start';busy=False;game=None;pawn=None;pc=None;director=None;door=None;capture=None;cc=None;rt=None;jobs=[];si=0;wi=0;route=[];walkstage='';previous=None;stucktime=0;distance=0;laststage=-1
u.EditorPythonScripting.set_keep_python_script_alive(True)
def write():
 report['elapsed_seconds']=round(time.monotonic()-start,2);(out/('Penance_V6_Final_Reload.json' if PROBE_ONLY else 'Penance_V6_Gameplay_Validation.json')).write_text(json.dumps(report,indent=2)+'\n')
def setroute(name,pts):
 global route,wi,walkstage,phase,last,stucktime
 route=pts;wi=0;walkstage=name;phase='walk';last=time.monotonic();stucktime=0
 print('V6_WALK_ROUTE',name)
def setupcapture():
 global capture,cc,rt,jobs,phase,last
 capture=next(a for a in u.GameplayStatics.get_all_actors_of_class(game,u.SceneCapture2D) if a.get_actor_label()=='V6_Transient_ValidationCapture');cc=capture.get_component_by_class(u.SceneCaptureComponent2D)
 rt=u.RenderingLibrary.create_render_target2d(game,1440,900,u.TextureRenderTargetFormat.RTF_RGBA8);cc.set_editor_properties({'texture_target':rt,'capture_source':u.SceneCaptureSource.SCS_FINAL_COLOR_LDR,'capture_every_frame':False,'capture_on_movement':False,'fov_angle':80})
 for cmd in('r.EyeAdaptationQuality 0','r.ScreenPercentage 100','r.AntiAliasingMethod 2'):u.SystemLibrary.execute_console_command(game,cmd)
 jobs=[a for a in u.GameplayStatics.get_all_actors_of_class(game,u.CameraActor) if a.get_actor_label().startswith('V6_Review_')];phase='capture_next';last=time.monotonic()
keyboard_start=None
def tick(dt):
 global phase,last,busy,game,pawn,pc,director,door,si,wi,previous,stucktime,distance,laststage,keyboard_start
 if busy:return
 busy=True
 try:
  now=time.monotonic()
  if now-start>1400:raise RuntimeError('PIE validation exceeded 23 minutes')
  if phase=='start':
   if now-last<3:return
   L.editor_request_begin_play();phase='wait_game';last=now
  elif phase=='wait_game':
   if now-last<3:return
   worlds=u.EditorLevelLibrary.get_pie_worlds(False)
   if not worlds:return
   game=worlds[0];pawn=u.GameplayStatics.get_player_pawn(game,0)
   if not pawn:return
   pc=pawn.get_controller();director=u.GameplayStatics.get_all_actors_of_class(game,u.PenanceV5WorldDirector)[0];door=next(x for x in u.GameplayStatics.get_all_actors_of_class(game,u.PenanceStreamingDoor) if x.exterior_entrance)
   assert 'BP_PenancePlayer' in pawn.get_class().get_name() and pc,'Incorrect possession'
   report['runtime']['possessed_class']=pawn.get_class().get_path_name();report['runtime']['spawn_position_uu']=list(pawn.get_actor_location().to_tuple())
   assert pawn.get_component_by_class(u.SkeletalMeshComponent).get_skeletal_mesh_asset().get_name()=='Untitled','Wrong player mesh'
   report['runtime']['player_mesh']='Untitled';report['runtime']['animation_class']=pawn.get_component_by_class(u.SkeletalMeshComponent).get_anim_instance().get_class().get_path_name()
   scope={'__file__':str(root/'Scripts/Validate_Penance_V6_Saved.py'),'V6_GAME_WORLD':game};exec((root/'Scripts/Validate_Penance_V6_Saved.py').read_text(),scope)
   setupcapture()
  elif phase=='capture_next':
   if si>=len(jobs):
    if PROBE_ONLY:
     keyboard_start=pawn.get_actor_location();phase='keyboard';last=now;report['keyboard_smoke_test']='awaiting physical keyboard';write();return
    setroute('Arrival to House01',[(30,20),(40,37),(66,47),(68,60),(68,73),(74,88),(78,99),(87,106),(92.0,106)]);return
   cam=jobs[si];cm=cam.get_component_by_class(u.CameraComponent);si+=1;capture.set_actor_location(cam.get_actor_location(),False,False);capture.set_actor_rotation(cam.get_actor_rotation(),False)
   cc.set_editor_property('projection_type',cm.projection_mode)
   if cm.projection_mode==u.CameraProjectionMode.ORTHOGRAPHIC:cc.set_editor_property('ortho_width',60000)
   phase='capture_save';last=now
  elif phase=='capture_save':
   if now-last<2:return
   name=jobs[si-1].get_actor_label().replace('V6_Review_','');cc.capture_scene();u.RenderingLibrary.export_render_target(game,rt,str(shots),name+'.png');report['screenshots'].append(name+'.png');phase='capture_next';write()
  elif phase=='walk':
   pos=pawn.get_actor_location();xy=(pos.x/100,pos.y/100)
   if previous:
    delta=math.dist(xy,previous);distance+=delta
    stucktime=stucktime+dt if delta<.001 else 0
   previous=xy
   stage=director.get_editor_property('stage')
   if stage!=laststage:report['runtime'].setdefault('stages_observed',[]).append(stage);laststage=stage;write()
   if wi>=len(route):
    pawn.get_movement_component().stop_movement_immediately();report['runtime'].setdefault('walked_routes',[]).append(walkstage)
    if walkstage=='Arrival to House01':
     pc.set_control_rotation(u.Rotator(yaw=0));door.interact(pawn);phase='enter';last=now
    elif walkstage=='Interior return':
     exitdoor=next(x for x in u.GameplayStatics.get_all_actors_of_class(game,u.PenanceStreamingDoor) if not x.exterior_entrance);exitdoor.interact(pawn);phase='exit';last=now
    elif walkstage=='Neighborhood and park':
     assert stage>=4,'Park checkpoint did not advance';setroute('Bridge and church',[(100,187),(124,202),(160,199),(190,181),(225,181),(250,189),(250,226),(250,239),(218,246),(181,251),(154,258),(135,261),(145,265),(145,269),(145,273.5),(152.7,273.5),(153,275.5),(153,284),(153,294)])
    elif walkstage=='Bridge and church':
     assert stage>=6,'Basement encounter failed';report['runtime']['basement_encounter_spawned']=len(u.GameplayStatics.get_all_actors_of_class(game,u.SkeletalMeshActor))>=1
     setroute('Basement west escape',[(153,294),(148,300),(137,307),(137,309),(137,318),(137,323),(137,325)])
    elif walkstage=='Basement west escape':
     assert stage>=7,'Escape checkpoint failed';setroute('Estate approach',p.PATHS['Estate back path'])
    elif walkstage=='Estate approach':
     assert stage==8,'Estate reveal failed';report['runtime']['opening_preview_completed']=True;report['runtime']['walk_distance_m_excluding_house_portal']=round(distance,2);report['runtime']['no_checkpoint_teleports']=True
     for tag in('V5_ParkShortcutBarrier','V5_EstateBarrier'):
      assert all(a.get_editor_property('hidden') for a in u.GameplayStatics.get_all_actors_with_tag(game,u.Name(tag))),tag+' stayed closed'
     write();L.editor_request_end_play();phase='end';last=now
    return
   target=route[wi];dx,dy=target[0]-xy[0],target[1]-xy[1];d=math.hypot(dx,dy)
   if d<.45:wi+=1;stucktime=0;return
   if stucktime>8 or now-last>480:raise RuntimeError(f'Stuck on {walkstage} waypoint {wi}: {xy}, target={target}, z={pos.z/100}')
   yaw=math.degrees(math.atan2(dy,dx));pc.set_control_rotation(u.Rotator(yaw=yaw));pawn.add_movement_input(u.Vector(dx/d,dy/d,0),1,False)
   if int(now)%10==0:write()
  elif phase=='keyboard':
   pos=pawn.get_actor_location();report['keyboard_initial_uu']=list(keyboard_start.to_tuple());report['keyboard_current_uu']=list(pos.to_tuple());report['keyboard_displacement_cm']=u.Vector.distance(keyboard_start,pos);write()
   if Path('/private/tmp/PenanceV6/ManualComplete').exists():
    report['keyboard_smoke_test']='physical keyboard movement verified' if Path('/private/tmp/PenanceV6/KeyboardInputSent').exists() and report['keyboard_displacement_cm']>50 else 'not verified: keyboard delivery unavailable';u.PenanceObjectiveEditorLibrary.capture_gameplay(str(shots/'PIE_Player_HUD.png'));phase='keyboard_capture';last=now
   elif now-last>300:raise RuntimeError('Keyboard smoke test timed out')
  elif phase=='keyboard_capture':
   if now-last<2:return
   L.editor_request_end_play();phase='end';last=now
  elif phase=='enter':
   if pawn.get_actor_location().x<150000:
    if now-last>30:raise RuntimeError('House01 did not stream in')
    return
   if now-last<2:return
   assert director.get_editor_property('stage')==1,'House stage failed';report['runtime']['streamed_entry']=True
   report['runtime']['interior_silhouette']=len(u.GameplayStatics.get_all_actors_of_class(game,u.SkeletalMeshActor))>=1
   # Walk inside the real interior, back toward the existing exit door.
   previous=None
   setroute('Interior return',[(1996.1,0),(1996.7,0)])
  elif phase=='exit':
   if pawn.get_actor_location().x>100000:
    if now-last>20:raise RuntimeError('House01 did not stream out')
    return
   if now-last<1:return
   assert director.get_editor_property('stage')==2,'Exit stage failed';report['runtime']['streamed_exit']=True;report['runtime']['return_position_uu']=list(pawn.get_actor_location().to_tuple());previous=None
   setroute('Neighborhood and park',[(100,96),(84,96),(78,88),(54,91),(34,109),(34,136),(53,154),(78,157),(91,170),(100,187)])
  elif phase=='end':
   if L.is_in_play_in_editor():return
   write();print('V6_PLAY_VALIDATION_COMPLETE',json.dumps(report['runtime']));u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
 except Exception:
  report['issues'].append(traceback.format_exc());write();print('V6_PLAY_ERROR',traceback.format_exc())
  if L.is_in_play_in_editor():L.editor_request_end_play()
  u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
 finally:busy=False
handle=u.register_slate_post_tick_callback(tick)
