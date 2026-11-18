"""Validate actual PIE player ownership, UMG updates and saved checkpoint data."""
from pathlib import Path
import json,time,traceback
import unreal as u
R=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));OUT=R/'Docs/ObjectiveHUD';(OUT/'Screenshots').mkdir(parents=True,exist_ok=True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.UnrealEditorSubsystem)
assert L.load_level('/Game/Maps/V5/Penance_Town_V5')
report={'checks':{},'screenshots':[],'errors':[]}
def ck(key,ok):
 report['checks'][key]=bool(ok)
 if not ok:report['errors'].append(key)
def dump():
 (OUT/'Validation.json').write_text(json.dumps(report,indent=2)+'\n')
def layout(name,w=1920,h=1080,color=u.LinearColor(.03,.035,.04,1)):
 filename=OUT/'Screenshots'/f'{name}.png';assert u.PenanceObjectiveEditorLibrary.render_tracker_layout(pc,u.IntPoint(w,h),str(filename),color);report['screenshots'].append(filename.name)
def state():return m.get_editor_property('state')
def mid():return str(state().get_editor_property('main_id'))
def completed(id):return m.is_objective_completed(u.Name(id))
start=time.monotonic();last=start;phase='boot';busy=False;world=None;pc=None;pawn=None;hud=None;widget=None;m=None;baseline=None;pos=None;door=None;snapshot=None
u.EditorPythonScripting.set_keep_python_script_alive(True)
def tick(dt):
 global last,phase,busy,world,pc,pawn,hud,widget,m,baseline,pos,door,snapshot
 if busy:return
 busy=True
 try:
  now=time.monotonic()
  if now-start>220:raise RuntimeError('HUD verification exceeded its time limit')
  if phase=='boot':
   if now-start<1:return
   u.PenanceObjectiveEditorLibrary.begin_validation_play(1920,1080);last=now;phase='world'
  elif phase=='world':
   if not L.is_in_play_in_editor():return
   world=E.get_game_world();pc=u.GameplayStatics.get_player_controller(world,0);pawn=u.GameplayStatics.get_player_pawn(world,0)
   if not pawn or now-last<2:return
   hud=pc.get_hud();widget=hud.get_editor_property('objective_tracker');m=u.PenanceObjectiveSubsystem.get_objective_manager(pc)
   ck('possessed_BP_PenancePlayer','BP_PenancePlayer' in pawn.get_class().get_name() and pawn.get_controller()==pc)
   ck('camera_views_player',pc.get_view_target()==pawn)
   ck('single_local_player',len(u.GameplayStatics.get_all_actors_of_class(world,u.PlayerController))==1)
   ck('saved_UMG_blueprint_used',widget.get_class().get_name()=='WBP_ObjectiveTracker_C' and widget.is_in_viewport())
   ck('tracker_passes_mouse_input',widget.get_visibility()==u.SlateVisibility.HIT_TEST_INVISIBLE and not widget.get_editor_property('is_focusable'))
   ck('chapter_1_initial_objective',mid()=='Ch01.House' and widget.get_editor_property('visible_row_count')==4)
   report['player_class']=pawn.get_class().get_path_name();report['background_opacity']=widget.get_editor_property('background_opacity')
   ck('subtle_background',.05<=report['background_opacity']<=.10)
   for tag,W,H in [('1080p',1920,1080),('1440p',2560,1440),('4K',3840,2160)]:
    for light,C in [('Dark',u.LinearColor(.02,.025,.03,1)),('Bright',u.LinearColor(.8,.8,.76,1))]:layout(tag+'_'+light,W,H,C)
   # Screenshot-only: hide engine debug overlays, leaving warnings in the log.
   u.SystemLibrary.execute_console_command(world,'DisableAllScreenMessages')
   u.PenanceObjectiveEditorLibrary.capture_gameplay(str(OUT/'Screenshots/PIE_V5_ObjectiveTracker.png'))
   pos=pawn.get_actor_location();phase='walk';last=now
  elif phase=='walk':
   pawn.add_movement_input(u.Vector(.5,.866,0),1,False)
   moved=u.Vector.distance(pos,pawn.get_actor_location())
   if moved<100 and now-last<10:return
   report['movement_cm']=moved;ck('actual_player_movement',moved>50);pawn.get_movement_component().stop_movement_immediately()
   if (OUT/'Screenshots/PIE_V5_ObjectiveTracker.png').exists():report['screenshots'].append('PIE_V5_ObjectiveTracker.png')
   m.set_objective_available(u.Name('Ch01.House.Porch'),False);ck('unavailable_hidden',widget.get_editor_property('visible_row_count')==3)
   m.set_objective_available(u.Name('Ch01.House.Porch'),True)
   m.add_sub_objective(u.Name('Test.Extra'),u.Text('Temporary test step'),True);ck('add_subobjective',widget.get_editor_property('visible_row_count')==5)
   m.remove_sub_objective(u.Name('Test.Extra'));ck('remove_subobjective',widget.get_editor_property('visible_row_count')==4)
   pawn.set_actor_location(u.Vector(10000,6400,560),False,False);phase='gas';last=now
  elif phase=='gas':
   if now-last<.5:return
   ck('gas_optional_real_overlap',completed('Ch01.Gas.Search'));ck('optional_does_not_advance_story',mid()=='Ch01.House')
   pawn.set_actor_location(u.Vector(10100,11800,580),False,False);last=now;phase='porch'
  elif phase=='porch':
   if now-last<.4:return
   ck('porch_real_overlap',completed('Ch01.House.Porch'))
   ck('completed_checkmark_state',any(str(x.get_editor_property('id'))=='Ch01.House.Porch' for x in m.get_editor_property('recent_completions')))
   layout('Completed_Steps');u.PenanceObjectiveEditorLibrary.capture_gameplay(str(OUT/'Screenshots/PIE_Completed_Porch.png'))
   phase='expire';last=now
  elif phase=='expire':
   if now-last<3.4:return
   ck('completion_expires',len(m.get_editor_property('recent_completions'))==0)
   u.SystemLibrary.execute_console_command(world,'EnableAllScreenMessages')
   snapshot=m.capture_snapshot();save=u.GameplayStatics.create_save_game_object(u.PenanceObjectiveSaveGame);save.set_editor_property('objectives',snapshot)
   slot='ObjectiveHUD_Validation_'+str(time.time_ns());saved=u.GameplayStatics.save_game_to_slot(save,slot,0);loaded=u.GameplayStatics.load_game_from_slot(slot,0);u.GameplayStatics.delete_game_in_slot(slot,0)
   ck('real_save_serialization',saved and loaded is not None)
   m.set_main_objective(u.Name('Test.Ch14'),u.Text('Chapter fourteen test'),14);ck('chapter_14_supported',state().get_editor_property('chapter')==14)
   m.restore_snapshot(loaded.get_editor_property('objectives'));ck('checkpoint_restores_flags',mid()=='Ch01.House' and completed('Ch01.Gas.Search') and completed('Ch01.House.Porch'))
   hud.toggle_objectives();ck('collapse_action',not state().get_editor_property('expanded'));layout('Collapsed');hud.toggle_objectives();ck('expand_action',state().get_editor_property('expanded'))
   m.set_suppressed(u.Name('CutsceneTest'),True);ck('cutscene_hidden',widget.get_visibility()==u.SlateVisibility.COLLAPSED)
   m.set_suppressed(u.Name('SecondScene'),True);m.set_suppressed(u.Name('CutsceneTest'),False);ck('overlapping_cutscenes_stay_hidden',m.is_suppressed());m.set_suppressed(u.Name('SecondScene'),False)
   ck('cutscene_restores',widget.get_visibility()==u.SlateVisibility.HIT_TEST_INVISIBLE)
   baseline=widget.get_editor_property('refresh_count');last=now;phase='idle'
  elif phase=='idle':
   if now-last<.8:return
   ck('event_driven_no_idle_refresh',widget.get_editor_property('refresh_count')==baseline)
   pawn.set_actor_location(u.Vector(10000,11800,580),False,False)
   door=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.PenanceStreamingDoor) if a.get_editor_property('exterior_entrance'));door.interact(pawn);last=now;phase='enter'
  elif phase=='enter':
   if pawn.get_actor_location().x<150000:
    if now-last>25:raise RuntimeError('House01 streaming entry failed')
    return
   if now-last<1:return
   ck('entered_house_updates_main',mid()=='Ch02.Exit');ck('encounter_hides_tracker',m.is_suppressed() and widget.get_visibility()==u.SlateVisibility.COLLAPSED)
   ck('same_possessed_player_after_streaming',u.GameplayStatics.get_player_pawn(world,0)==pawn and pc.get_view_target()==pawn)
   phase='encounter';last=now
  elif phase=='encounter':
   if m.is_suppressed():
    if now-last>13:raise RuntimeError('Tracker remained hidden after the silhouette')
    return
   ck('encounter_restores_tracker',widget.get_visibility()==u.SlateVisibility.HIT_TEST_INVISIBLE)
   exit=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.PenanceStreamingDoor) if not a.get_editor_property('exterior_entrance'));exit.interact(pawn);last=now;phase='exit'
  elif phase=='exit':
   if pawn.get_actor_location().x>100000:
    if now-last>15:raise RuntimeError('House01 exit failed')
    return
   if now-last<1:return
   ck('house_exit_updates_main',mid()=='Ch03.Neighborhood');ck('optional_expires_by_chapter',not state().get_editor_property('optional_objectives'))
   L.editor_request_end_play();phase='old_map'
  elif phase=='old_map':
   if L.is_in_play_in_editor():return
   assert L.load_level('/Game/Maps/Penance_Persistent');u.PenanceObjectiveEditorLibrary.begin_validation_play(1280,720);phase='old_world';last=now
  elif phase=='old_world':
   if not L.is_in_play_in_editor():return
   old=E.get_game_world();P=u.GameplayStatics.get_player_pawn(old,0);C=u.GameplayStatics.get_player_controller(old,0)
   if not P or now-last<2:return
   M=u.PenanceObjectiveSubsystem.get_objective_manager(C)
   ck('persistent_map_player_possessed','BP_PenancePlayer' in P.get_class().get_name() and C.get_view_target()==P)
   ck('persistent_map_existing_objectives_connected',str(M.get_editor_property('state').get_editor_property('main_id')).startswith('Legacy.'))
   ck('persistent_map_UMG_active',C.get_hud().get_editor_property('objective_tracker').is_in_viewport())
   M.complete_sub_objective(u.Name('Legacy.House.Porch'));old_manager=u.GameplayStatics.get_actor_of_class(old,u.PenanceProgressionManager);old_manager.debug_reset_progression();ck('legacy_reset_clears_HUD_completion',not M.is_objective_completed(u.Name('Legacy.House.Porch')))
   L.editor_request_end_play();phase='finish'
  elif phase=='finish':
   if L.is_in_play_in_editor():return
   assert L.load_level('/Game/Maps/V5/Penance_Town_V5');u.PenanceObjectiveEditorLibrary.configure_player_play_settings()
   for name in ['PIE_Completed_Porch.png']:
    if (OUT/'Screenshots'/name).exists():report['screenshots'].append(name)
   dump();print('PENANCE_HUD_PIE_VERIFIED',json.dumps({'checks':len(report['checks']),'errors':report['errors'],'movement_cm':report.get('movement_cm'),'screenshots':len(report['screenshots'])}));u.unregister_slate_post_tick_callback(handle);u.EditorPythonScripting.set_keep_python_script_alive(False)
 except Exception:
  report['errors'].append(traceback.format_exc());dump();print('PENANCE_HUD_ERROR',traceback.format_exc());u.unregister_slate_post_tick_callback(handle);L.editor_request_end_play();u.EditorPythonScripting.set_keep_python_script_alive(False)
 finally:busy=False
handle=u.register_slate_post_tick_callback(tick)
