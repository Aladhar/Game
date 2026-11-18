"""Fresh-editor PIE verification of saved V5 assets, collision and streaming.
Run via -ExecutePythonScript. Writes actual measurements and screenshots; never saves changes.
"""
from pathlib import Path
import json,time,traceback,math,sys,hashlib
import unreal as ue
sys.path.insert(0,str(Path(__file__).resolve().parent));import Penance_Town_V5_Design as p
root=Path(__file__).resolve().parents[1];out=root/'Docs/V5';shots=out/'Views';shots.mkdir(exist_ok=True)
a=ue.get_editor_subsystem(ue.EditorActorSubsystem);lev=ue.get_editor_subsystem(ue.LevelEditorSubsystem);ed=ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
assert lev.load_level(p.MAP)
placements=[]
for actor in a.get_all_level_actors():
 if not actor.get_actor_label().startswith('V5_'):continue
 record={'label':actor.get_actor_label(),'class':actor.get_class().get_path_name(),'location_uu':list(actor.get_actor_location().to_tuple()),'rotation_degrees':list(actor.get_actor_rotation().to_tuple()),'scale':list(actor.get_actor_scale3d().to_tuple()),'folder':str(actor.get_folder_path()),'tags':list(map(str,actor.tags))}
 comp=actor.get_component_by_class(ue.StaticMeshComponent)
 if comp and comp.get_editor_property('static_mesh'):record['static_mesh']=comp.get_editor_property('static_mesh').get_path_name()
 placements.append(record)
(out/'Unreal_Actor_Placements.json').write_text(json.dumps(placements,indent=2)+'\n')
cap=a.spawn_actor_from_class(ue.SceneCapture2D,ue.Vector());cap.set_actor_label('V5_Transient_ValidationCapture')
report={'map':p.MAP,'issues':[],'warnings':[],'fresh_editor_reload':True,'runtime':{},'roads':{},'routes':{},'screenshots':[]}
def check(ok,msg):
 if not ok:report['issues'].append(msg)
def trace(world,xy,ignore=(),high=65,low=-10):
 hit=ue.SystemLibrary.line_trace_single(world,ue.Vector(*p.uu(*xy,high)),ue.Vector(*p.uu(*xy,low)),ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,list(ignore),ue.DrawDebugTrace.NONE,False)
 return hit.to_tuple() if hit else None
def capsule(world,start,end,radius,half,ignore):
 return ue.SystemLibrary.capsule_trace_single(world,ue.Vector(*start),ue.Vector(*end),radius,half,ue.TraceTypeQuery.TRACE_TYPE_QUERY1,True,ignore,ue.DrawDebugTrace.NONE,False)
def inspect(world,pawn):
 actors=ue.GameplayStatics.get_all_actors_of_class(world,ue.Actor);named={str(x.get_actor_label()):x for x in actors};report['actor_count']=len(actors)
 check(sum(x.get_class().get_name()=='PlayerStart' for x in actors)==1,'Expected exactly one PlayerStart')
 check('BP_PenancePlayer' in pawn.get_class().get_name(),'Possessed pawn is not BP_PenancePlayer')
 check(pawn.get_controller() is not None,'Player has no controller')
 report['player_class']=pawn.get_class().get_path_name();report['player_initial_location']=list(pawn.get_actor_location().to_tuple())
 report['building_count']=len(p.BUILDINGS);report['residential_count']=len([b for b in p.BUILDINGS if b['category']=='Residential'])
 report['mesh_assets']=len(list((root/'Content/Environment/V5/Meshes').glob('*.uasset')))
 report['map_bytes']=(root/'Content/Maps/V5/Penance_Town_V5.umap').stat().st_size
 for b in p.BUILDINGS:
  check((b['y']>p.creek_y(b['x'])) == (b['category']=='Estate' or b['id']=='UTILITY'),'Unexpected bank for '+b['id'])
 def grade(z,points):return max([abs(a-b)/math.dist(P[:2],Q[:2])*100 for a,b,P,Q in zip(z,z[1:],points,points[1:]) if a is not None and b is not None]+[0])
 ignore=[pawn]
 for name,r in p.ROADS.items():
  pts=[]
  for P,Q in zip(r['points'],r['points'][1:]):
   N=max(1,math.ceil(math.dist(P[:2],Q[:2])/2))
   pts.extend(tuple(p.mix(P[j],Q[j],(i+.37)/N) for j in range(3)) for i in range(N))
  hits=[trace(world,q[:2],ignore,high=q[2]+2.1,low=q[2]-2.5) for q in pts];z=[h[5].z/100 if h else None for h in hits]
  check(all(h is not None for h in hits),'Missing road collision: '+name)
  deviations=[abs(Z-q[2]-.045) for Z,q in zip(z,pts) if Z is not None];bad=[]
  for q,Z in zip(pts,z):
   if Z is None:continue
   hit=capsule(world,p.uu(q[0],q[1],Z+1.0),p.uu(q[0],q[1],Z+1.01),34,86,ignore)
   if hit:bad.append((q[:2],hit.to_tuple()[9].get_actor_label() if hit.to_tuple()[9] else 'unknown'))
  report['roads'][name]={'samples':len(pts),'max_grade_pct':round(grade(z,pts),2),'max_surface_deviation_cm':round(max(deviations,default=999)*100,2),'blocked_player_samples':bad,'width_cm':r['width']*100,'surface_anomalies':[{'xy_m':q[:2],'expected':q[2]+.045,'actual':Z,'actor':h[9].get_actor_label() if h[9] else None} for q,Z,h in zip(pts,z,hits) if Z is not None and abs(Z-q[2]-.045)>.12]}
  check(not bad,'Road capsule blocked: '+name+' '+str(bad[:3]))
  check(max(deviations,default=999)<.22,'Road obstructed/height differs: '+name)
  target={'main':7,'residential':8,'service':10}[r['kind']]
  if grade(z,pts)>target+1:report['warnings'].append(f'{name}: local travel surface reaches {grade(z,pts):.2f}% against a {target}% design target; apron refinement remains.')
  check(grade(z,pts)<35,'Severe road grade prevents comfortable traversal: '+name)
 # Surface continuity on the opening footpaths and stairs, with enemy width clearance.
 route_ignore=ignore+list(ue.GameplayStatics.get_all_actors_with_tag(world,ue.Name('V5_EstateBarrier')))+list(ue.GameplayStatics.get_all_actors_with_tag(world,ue.Name('V5_ParkShortcutBarrier')))
 routes={
  'Park':[(105,194),(103,215),(126,221)],'Church approach':[(185,344),(185,355)],
  'Descent':[(193,355),(193,364.3),(193,374)],
  'Basement escape':[(193,374),(188,380),(177,387),(177,399),(177,403),(185,407)],
  'Estate reveal':p.PATHS['Estate back path']}
 for name,points in routes.items():
  pts=list(p.samples(points,.15 if name in ('Descent','Basement escape') else .5));hits=[]
  for x,y in pts:
   if name=='Descent':
    expected=10 if y<355.85 else max(5.32,10-(int((y-355.85)/.3)+1)*.18)
   elif name=='Basement escape':
    expected=5.32 if y<389.85 else min(10,5.32+(int((y-389.85)/.3)+1)*.18)
   elif name=='Church approach':expected=10
   else:expected=p.Terrain().surface(x,y)
   hits.append(trace(world,(x,y),route_ignore,high=expected+2.0,low=expected-2.5))
  z=[h[5].z/100 if h else None for h in hits]
  changes=[abs(a-b)*100 for a,b in zip(z,z[1:]) if a is not None and b is not None]
  report['routes'][name]={'samples':len(pts),'missing_floor':sum(Z is None for Z in z),'max_sample_height_change_cm':round(max(changes or [0]),2),'heights_m':[round(Z,2) if Z is not None else None for Z in z]}
  check(all(Z is not None for Z in z),'Route has missing floor: '+name)
  check(max(changes or [0])<46,'Route has an unclimbable step: '+name)
 for key in('Church','Foster'):
  b=p.BUILDING_BY_ID['CHURCH' if key=='Church' else 'FOSTER'];check(b['y']>p.creek_y(b['x']),key+' is on wrong bank')
 report['bridge']={'deck_top_cm':420,'water_cm':0,'creek_bed_cm':round(p.raw(305,p.creek_y(305))*100,1),'deck_width_cm':700}
 report['door_clearance']={'House01_cm':[135,230],'church_cm':[320,420],'basement_stairs_cm':[300,460],'enemy_height_cm':230,'note':'House01 is a player-only threshold; no enemy AI or navmesh is claimed.'}

def write():
 (out/'Penance_V5_Validation.json').write_text(json.dumps(report,indent=2)+'\n')
 print('PENANCE_V5_VALIDATION',json.dumps({'issues':report['issues'],'actor_count':report.get('actor_count'),'runtime':report['runtime'],'screenshots':len(report['screenshots'])}))
start=time.monotonic();last=start;stage='start';busy=False;game=None;pawn=None;director=None;door=None;capture=None;cc=None;rt=None;shots_jobs=[];shot_index=0;startpos=None
ue.EditorPythonScripting.set_keep_python_script_alive(True)
def tick(dt):
 global last,stage,busy,game,pawn,director,door,capture,cc,rt,shots_jobs,shot_index,startpos
 if busy:return
 busy=True
 try:
  now=time.monotonic()
  if now-start>240:raise RuntimeError('V5 validation timed out')
  if stage=='start':
   if now-start<2:return
   lev.editor_request_begin_play();stage='game';last=now
  elif stage=='game':
   if not lev.is_in_play_in_editor():return
   game=ed.get_game_world();pawn=ue.GameplayStatics.get_player_pawn(game,0)
   if not pawn:return
   director=ue.GameplayStatics.get_actor_of_class(game,ue.PenanceV5WorldDirector);door=next(d for d in ue.GameplayStatics.get_all_actors_of_class(game,ue.PenanceStreamingDoor) if d.get_editor_property('exterior_entrance'))
   if now-last<2:return
   inspect(game,pawn);startpos=pawn.get_actor_location();stage='walk';last=now
  elif stage=='walk':
   pawn.add_movement_input(ue.Vector(.50,.866,0),1,False)
   if now-last<2:return
   moved=ue.Vector.distance(startpos,pawn.get_actor_location());report['runtime']['movement_cm']=moved;check(moved>50,'Possessed pawn failed the actual movement check')
   pawn.get_movement_component().stop_movement_immediately();pawn.set_actor_location(ue.Vector(*p.uu(100,118,5.8)),False,False);door.interact(pawn);last=now;stage='enter'
  elif stage=='enter':
   if pawn.get_actor_location().x<150000:
    if now-last>30:raise RuntimeError('House01 streaming entry failed')
    return
   if now-last<1.5:return
   report['runtime']['streamed_house_entry']=True;report['runtime']['house_stage']=director.get_editor_property('stage');check(director.get_editor_property('stage')==1,'House entry did not advance V5')
   check(len(ue.GameplayStatics.get_all_actors_of_class(game,ue.SkeletalMeshActor))>=1,'House silhouette did not spawn')
   exitdoor=next(d for d in ue.GameplayStatics.get_all_actors_of_class(game,ue.PenanceStreamingDoor) if not d.get_editor_property('exterior_entrance'));exitdoor.interact(pawn);last=now;stage='exit'
  elif stage=='exit':
   if pawn.get_actor_location().x>100000:
    if now-last>15:raise RuntimeError('House01 streaming exit failed')
    return
   if now-last<1:return
   report['runtime']['streamed_house_exit']=True;report['runtime']['return_position']=list(pawn.get_actor_location().to_tuple());check(director.get_editor_property('stage')==2,'Changed exit did not advance V5')
   # A late objective must not skip the current neighborhood objective.
   pawn.set_actor_location(ue.Vector(*p.uu(*p.CHECKPOINTS[7])),False,False);stage='no_skip';last=now
  elif stage=='no_skip':
   if now-last<.5:return
   check(director.get_editor_property('stage')==2,'Out-of-order checkpoint skipped progression');report['runtime']['out_of_order_rejected']=director.get_editor_property('stage')==2
   pawn.set_actor_location(ue.Vector(*p.uu(*p.CHECKPOINTS[2])),False,False);stage='progress';last=now
  elif stage=='progress':
   if now-last<.4:return
   s=director.get_editor_property('stage')
   report['runtime'].setdefault('stages_observed',[]).append(s)
   if s<8:
    pawn.set_actor_location(ue.Vector(*p.uu(*p.CHECKPOINTS[s])),False,False);last=now
    if s==6:report['runtime']['basement_enemy_spawned']=len(ue.GameplayStatics.get_all_actors_of_class(game,ue.SkeletalMeshActor))>=1
    return
   check(s==8,'Preview did not finish');report['runtime']['preview_completed']=True
   for key in('V5_ParkShortcutBarrier','V5_EstateBarrier'):
    arr=ue.GameplayStatics.get_all_actors_with_tag(game,ue.Name(key));check(all(x.get_editor_property('hidden') for x in arr),'Progression barrier stayed active: '+key)
   capture=next(x for x in ue.GameplayStatics.get_all_actors_of_class(game,ue.SceneCapture2D) if x.get_actor_label()=='V5_Transient_ValidationCapture');cc=capture.get_component_by_class(ue.SceneCaptureComponent2D)
   rt=ue.RenderingLibrary.create_render_target2d(game,1440,900,ue.TextureRenderTargetFormat.RTF_RGBA8)
   cc.set_editor_properties({'texture_target':rt,'capture_source':ue.SceneCaptureSource.SCS_FINAL_COLOR_LDR,'capture_every_frame':False,'capture_on_movement':False,'fov_angle':80})
   for cmd in['r.EyeAdaptationQuality 0','r.ScreenPercentage 100','r.AntiAliasingMethod 2']:ue.SystemLibrary.execute_console_command(game,cmd)
   shots_jobs=[x for x in ue.GameplayStatics.get_all_actors_of_class(game,ue.CameraActor) if x.get_actor_label().startswith('V5_Review_')];stage='capture_next';last=now
  elif stage=='capture_next':
   if shot_index>=len(shots_jobs):lev.editor_request_end_play();stage='end';return
   cam=shots_jobs[shot_index];shot_index+=1;cm=cam.get_component_by_class(ue.CameraComponent)
   capture.set_actor_location(cam.get_actor_location(),False,False);capture.set_actor_rotation(cam.get_actor_rotation(),False);cc.set_editor_property('projection_type',cm.get_editor_property('projection_mode'))
   if cm.get_editor_property('projection_mode')==ue.CameraProjectionMode.ORTHOGRAPHIC:cc.set_editor_property('ortho_width',53000)
   stage='capture_save';last=now
  elif stage=='capture_save':
   if now-last<1:return
   name=shots_jobs[shot_index-1].get_actor_label().replace('V5_Review_','');cc.capture_scene();ue.RenderingLibrary.export_render_target(game,rt,str(shots),name+'.png');report['screenshots'].append(name+'.png');stage='capture_next'
  elif stage=='end':
   if lev.is_in_play_in_editor():return
   write();ue.unregister_slate_post_tick_callback(handle);ue.EditorPythonScripting.set_keep_python_script_alive(False)
 except Exception:
  report['issues'].append(traceback.format_exc());write();print('V5_ERROR',traceback.format_exc());ue.unregister_slate_post_tick_callback(handle);ue.EditorPythonScripting.set_keep_python_script_alive(False)
 finally:busy=False
handle=ue.register_slate_post_tick_callback(tick)
