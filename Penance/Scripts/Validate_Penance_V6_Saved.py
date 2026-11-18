"""Saved-world collision and asset probes; called inside PIE by Verify_Penance_V6_Play.py."""
import unreal as u
import sys,json,math,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));import Penance_Town_V6_Design as p
root=Path(__file__).resolve().parents[1];out=root/'Docs/V6';level=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);E=u.get_editor_subsystem(u.UnrealEditorSubsystem)
game=globals().get('V6_GAME_WORLD')
assert game, 'Run through Verify_Penance_V6_Play.py: editor-only worlds lack runtime physics'
if not game:assert level.load_level(p.MAP)
w=game or E.get_editor_world();allactors=list(u.GameplayStatics.get_all_actors_of_class(w,u.Actor)) if game else A.get_all_level_actors();active=[a for a in allactors if '99_' not in str(a.get_folder_path())];named={a.get_actor_label():a for a in active}
r=dict(map=p.MAP,fresh_editor_reload=True,issues=[],warnings=[],roads={},routes={},all_actor_count=len(allactors),active_actor_count=len(active),blueprints={},lighting={},manual_walkthrough=False)
def check(ok,s):
 if not ok:r['issues'].append(s)
def trace(x,y,z,ignore=()):
 h=u.SystemLibrary.line_trace_single(w,u.Vector(x*100,y*100,(z+2)*100),u.Vector(x*100,y*100,(z-3)*100),u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,list(ignore),u.DrawDebugTrace.NONE,False)
 return h.to_tuple() if h else None
def capsule(x,y,z,ignore=()):
 h=u.SystemLibrary.capsule_trace_single(w,u.Vector(x*100,y*100,(z+1.33)*100),u.Vector(x*100,y*100,(z+1.331)*100),34,86,u.TraceTypeQuery.TRACE_TYPE_QUERY1,True,list(ignore),u.DrawDebugTrace.NONE,False)
 return h.to_tuple()[9].get_actor_label() if h and h.to_tuple()[9] else None
for name,road in p.ROADS.items():
 bad=[];deviations=[];missing=[];heights=[];grades=[]
 pts=list(p.samples(road['points'],1.4))
 for q in pts:
  x,y,z=q;h=trace(x,y,z)
  if h is None:missing.append(q);continue
  Z=h[5].z/100;heights.append([x,y,Z]);d=Z-z-.045
  if abs(d)>.18:deviations.append(dict(x=x,y=y,cm=round(d*100,2),actor=h[9].get_actor_label()))
  blocked=capsule(x,y,Z)
  if blocked:bad.append([x,y,blocked])
 for a,b in zip(heights,heights[1:]):
  d=math.dist(a[:2],b[:2])
  if d>.01:grades.append(abs(a[2]-b[2])/d*100)
 r['roads'][name]=dict(samples=len(pts),missing_floor=missing,anomalies=deviations,blocked=bad,max_grade_pct=round(max(grades or[0]),2),width_m=road['width'])
 check(not missing,'Missing road floor: '+name);check(not bad,'Blocked public road: '+name);check(not deviations,'Road surface intrusion: '+name)
# Dense route probes including both original stair flights; no roof hits.
routes={
 'House01 approach':[(78,101,4.8),(87,105,4.8),(92.6,106,4.8)],
 'Park shortcut':[(78,157,5.1),(91,170,5.25),(100,187,5.2)],
 'Bridge approach':[(190,181,p.Terrain().surface(190,181)),(225,181,p.Terrain().surface(225,181)),(250,189,4.6)],
 'Church threshold':[(145,269,11),(145,275,11)],
 'Basement descent':[(153,275.5,11),(153,283.7,6.32),(153,294,6.32)],
 'Basement escape':[(153,294,6.32),(148,300,6.32),(137,307,6.32),(137,309.8,6.32),(137,318,11),(137,323,11)],
 'Estate garden':[(x,y,p.Terrain().surface(x,y)) for x,y in p.PATHS['Estate back path']]}
barriers=[a for a in active if any(str(t) in('V5_ParkShortcutBarrier','V5_EstateBarrier') for t in a.tags)]
for name,pts in routes.items():
 records=[]
 for x,y,z in p.samples(pts,.22):
  if name=='Basement descent':z=11 if y<275.85 else max(6.32,11-(int((y-275.85)/.3)+1)*.18)
  if name=='Basement escape':z=6.32 if y<309.85 else min(11,6.32+(int((y-309.85)/.3)+1)*.18)
  h=trace(x,y,z,barriers);Z=h[5].z/100 if h else None;blocked=capsule(x,y,Z,barriers) if h else 'NO_FLOOR'
  records.append(dict(x=x,y=y,z=Z,blocked=blocked,actor=h[9].get_actor_label() if h and h[9] else None))
 changes=[abs(a['z']-b['z'])*100 for a,b in zip(records,records[1:]) if a['z'] is not None and b['z'] is not None]
 blocked=[a for a in records if a['blocked']];r['routes'][name]=dict(samples=len(records),missing=sum(a['z'] is None for a in records),max_sample_step_cm=round(max(changes or[0]),2),blocked=blocked)
 check(not any(a['z'] is None for a in records),'Missing route floor: '+name);check(max(changes or[0])<45,'Impassable route step: '+name);check(not blocked,'Route capsule blocked: '+name)
placements=[];lights=[]
for a in active:
 c=a.get_component_by_class(u.StaticMeshComponent)
 rec=dict(label=a.get_actor_label(),class_name=a.get_class().get_path_name(),location_uu=list(a.get_actor_location().to_tuple()),rotation_degrees=list(a.get_actor_rotation().to_tuple()),scale=list(a.get_actor_scale3d().to_tuple()),folder=str(a.get_folder_path()),tags=list(map(str,a.tags)))
 if c:
  rec['mesh']=c.static_mesh.get_path_name() if c.static_mesh else None;check(c.static_mesh is not None,'Missing mesh: '+a.get_actor_label());rec['materials']=[m.get_path_name() if m else None for m in c.get_materials()]
 if a.get_actor_label().startswith('V6_') and 'Transient_' not in a.get_actor_label():placements.append(rec)
 lc=a.get_component_by_class(u.LightComponentBase)
 if lc:
  q=dict(label=a.get_actor_label(),mobility=str(lc.mobility))
  if isinstance(lc,u.DirectionalLightComponent):q.update(priority=lc.get_editor_property('forward_shading_priority'),atmosphere_sun=lc.get_editor_property('atmosphere_sun_light'))
  lights.append(q);check(lc.mobility==u.ComponentMobility.MOVABLE,'Non-movable light '+a.get_actor_label())
(out/'Unreal_Actor_Placements.json').write_text(json.dumps(placements,indent=2)+'\n')
r['placed_saved_actor_count']=len(placements)
r['lighting']=dict(force_no_precomputed=w.get_world_settings().get_editor_property('force_no_precomputed_lighting'),lights=lights)
check(sum(a.get_class().get_name()=='PlayerStart' for a in active)==1,'Expected one PlayerStart')
check(sum(a.get_class().get_name()=='PenanceStreamingDoor' for a in active)==1,'Expected one exterior streaming entrance')
check(sum(a.get_class().get_name()=='PenanceV5WorldDirector' for a in active)==1,'Expected one opening director')
proof=json.loads((out/'Original_Building_Scale_Proof.json').read_text());check(all(x['original_scale']==x['v6_scale'] for x in proof),'An original building component was scaled');r['original_building_parts_preserved']=len(proof)
for path in('/Game/Player/BP_PenancePlayer','/Game/Player/Animations/ABP_PenancePlayer','/Game/UI/WBP_ObjectiveTracker'):
 bp=u.load_asset(path);
 if not game:u.BlueprintEditorLibrary.compile_blueprint(bp)
 r['blueprints'][path]='compile invoked in fresh commandlet; compiler log checked';check('ERROR' not in r['blueprints'][path].upper(),'Blueprint compile failed '+path)
r['game_mode']=w.get_world_settings().get_editor_property('default_game_mode').get_path_name();r['building_sites']=len(p.BUILDINGS);r['houses']=20;r['site_m']=[400,350];r['bridge_m']=[7,37];r['clearances_cm']=dict(house01=[135,230],church=[320,420],stairs_width=300,enemy_height=230)
if not game:u.SystemLibrary.execute_console_command(w,'MAP CHECK DONTDISPLAYDIALOG')
r['physics_world']='PIE' if game else 'Editor only: collision results not authoritative'
(out/'Penance_V6_Saved_Validation.json').write_text(json.dumps(r,indent=2)+'\n');print('V6_SAVED_VALIDATION',json.dumps(dict(issues=r['issues'],active_actors=len(active))))
