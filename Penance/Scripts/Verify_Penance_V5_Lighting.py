"""Fresh rendered-editor validation. Leaves Unreal open on the corrected map."""
from pathlib import Path
import json,time,traceback
import unreal as u
R=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=R/'Docs/Lighting';OUT.mkdir(exist_ok=True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert L.load_level('/Game/Maps/V5/Penance_Town_V5')
report={'checks':{},'errors':[],'baked_lightmass_build_performed':False,'lighting_mode':'dynamic'}
def ck(name,ok):
 report['checks'][name]=bool(ok)
 if not ok:report['errors'].append(name)
def inspect(world):
 settings=world.get_world_settings();ck('no_precomputed_lighting_needed',settings.get_editor_property('force_no_precomputed_lighting'))
 lights=[c for a in u.GameplayStatics.get_all_actors_of_class(world,u.Actor) for c in a.get_components_by_class(u.LightComponentBase)]
 ck('all_lights_movable',all(c.get_editor_property('mobility')==u.ComponentMobility.MOVABLE for c in lights))
 dirs=[c for c in lights if isinstance(c,u.DirectionalLightComponent)];priorities=[c.get_editor_property('forward_shading_priority') for c in dirs]
 ck('unique_primary_directional_light',priorities.count(max(priorities))==1)
 report['light_count']=len(lights);report['directional_priorities']=priorities
 u.SystemLibrary.execute_console_command(world,'EnableAllScreenMessages')
 u.SystemLibrary.execute_console_command(world,'DumpUnbuiltLightInteractions')
 u.SystemLibrary.execute_console_command(world,'MAP CHECK DONTDISPLAYDIALOG')
world=E.get_editor_world();inspect(world)
start=time.monotonic();last=start;phase='start';busy=False;pawn=None;pc=None;pos=None
u.EditorPythonScripting.set_keep_python_script_alive(True)
def finish():
 (OUT/'Rendered_Validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PENANCE_LIGHTING_RENDERED_VERIFIED',json.dumps(report));u.unregister_slate_post_tick_callback(handle)
 # Keep this normal, interactive editor open for the user after validation.
def tick(dt):
 global phase,last,busy,pawn,pc,pos
 if busy:return
 busy=True
 try:
  now=time.monotonic()
  if now-start>100:raise RuntimeError('Lighting verification timed out')
  if phase=='start':
   if now-last<2:return
   inspect(E.get_editor_world());L.editor_request_begin_play();phase='play';last=now
  elif phase=='play':
   if not L.is_in_play_in_editor():return
   game=E.get_game_world();pc=u.GameplayStatics.get_player_controller(game,0);pawn=u.GameplayStatics.get_player_pawn(game,0)
   if not pawn or now-last<2:return
   ck('player_possessed','BP_PenancePlayer' in pawn.get_class().get_name() and pawn.get_controller()==pc);ck('player_camera_active',pc.get_view_target()==pawn)
   ck('objective_hud_active',pc.get_hud().get_editor_property('objective_tracker').is_in_viewport())
   inspect(game);pos=pawn.get_actor_location();phase='move';last=now
  elif phase=='move':
   pawn.add_movement_input(u.Vector(.5,.866,0),1,False)
   d=u.Vector.distance(pos,pawn.get_actor_location())
   if d<70 and now-last<8:return
   report['actual_player_movement_cm']=d;ck('player_moves',d>50)
   pawn.get_movement_component().stop_movement_immediately()
   u.PenanceObjectiveEditorLibrary.capture_gameplay(str(OUT/'V5_Lighting_Gameplay.png'));last=now;phase='capture'
  elif phase=='capture':
   if now-last<1:return
   ck('screenshot_saved',(OUT/'V5_Lighting_Gameplay.png').exists());L.editor_request_end_play();phase='end'
  elif phase=='end':
   if L.is_in_play_in_editor():return
   u.PenanceObjectiveEditorLibrary.configure_player_play_settings();finish()
 except Exception:
  report['errors'].append(traceback.format_exc());print('PENANCE_LIGHTING_VERIFY_ERROR',traceback.format_exc())
  if L.is_in_play_in_editor():L.editor_request_end_play()
  finish()
 finally:busy=False
handle=u.register_slate_post_tick_callback(tick)
