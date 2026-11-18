"""Build V6 from the saved V5 level; never edits a V5 asset.
Unreal 5.7.4, -EnablePlugins=GeometryScripting -run=pythonscript -script=...
Requires host Prepare_Penance_V6_Parcels.py first. Fails rather than overwrites V6.
"""
from pathlib import Path
import sys,math,json,random
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent))
import Penance_Town_V6_Design as p
import Penance_Town_V5_Design as old
import Build_Penance_Town_V5 as g
root=Path(__file__).resolve().parents[1];out=root/'Docs/V6'
assets=u.get_editor_subsystem(u.EditorAssetSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
g.plan=p;g.palette.update({'Residential':'B7B19C','Commerce':'795046','Civic':'936B57','Estate':'979286','Woods':'42584A','Leaf':'58654E','Terrain':'626C58','White':'CEC6AC','Creek':'344C52','Brick':'855C4C','RedBrick':'704C44','Siding':'B0AC97','BlueSiding':'848F8B','Mortar':'9A9481','Asphalt':'474A4B','Faded':'A99E80'})
legacy_spawn=g.spawn
def spawn(cls,name,folder,xyz,rotation=None):
 a=legacy_spawn(cls,name,folder,xyz,rotation);a.set_actor_label('V6_'+name);return a
g.spawn=spawn
# Geometry helper writes supported StaticMesh assets; all V5 meshes are read-only references.
def surface(name,folder,v,f,color,collision=True):
 if not f:return None
 origin=p.uu(v[0][0],v[0][1],0);path=p.GENERATED+'/Meshes/SM_V6_'+name
 mesh=assets.load_asset(path) if assets.does_asset_exist(path) else None
 if not mesh:
  dm=u.DynamicMesh();buf=u.GeometryScriptSimpleMeshBuffers();buf.vertices=[u.Vector(x*100-origin[0],y*100-origin[1],z*100) for x,y,z in v];buf.triangles=[u.IntVector(a,c,b) for a,b,c in f];buf.uv0=[u.Vector2D(x*.1,y*.1) for x,y,z in v]
  u.GeometryScript_MeshEdits.append_buffers_to_mesh(dm,buf)
  opts=u.GeometryScriptCreateNewStaticMeshAssetOptions();opts.enable_recompute_normals=True;opts.enable_recompute_tangents=True;opts.enable_collision=collision
  if collision:opts.collision_mode=u.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
  mesh,result=u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm,path,opts)
  assert mesh and result==u.GeometryScriptOutcomePins.SUCCESS,path
  body=mesh.get_editor_property('body_setup')
  if body:body.set_editor_property('double_sided_geometry',True)
  g.save(mesh)
 return g.set_mesh(spawn(u.StaticMeshActor,name,folder,origin),mesh,color,collision)
g.static_surface=surface
box=g.obox;part=g.part;sign=g.sign
T=p.Terrain();rng=random.Random(62026)
def archive(a):
 a.set_folder_path(u.Name('V6/99_V5_Reference_Archive'));a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True);a.set_actor_enable_collision(False);a.set_editor_property('is_editor_only_actor',True)
 for c in a.get_components_by_class(u.SceneComponent):c.set_visibility(False,True)
def relocate(a,b,prev):
 L=a.get_actor_location();dx,dy=L.x/100-prev['x'],L.y/100-prev['y'];angle=math.radians(b['yaw']-prev['yaw']);c,s=math.cos(angle),math.sin(angle)
 a.set_actor_location(u.Vector(*p.uu(b['x']+dx*c-dy*s,b['y']+dx*s+dy*c,L.z/100+b['z']-prev['z'])),False,False)
 R=a.get_actor_rotation();a.set_actor_rotation(u.Rotator(pitch=R.pitch,yaw=R.yaw+b['yaw']-prev['yaw'],roll=R.roll),False)
 a.set_actor_label(a.get_actor_label().replace('V5_','V6_',1));a.set_folder_path(u.Name(str(a.get_folder_path()).replace('V5/','V6/',1)))
def move(a,xyz):a.set_actor_location(u.Vector(*p.uu(*xyz)),False,False)
def offset(a,xyz):
 l=a.get_actor_location();a.set_actor_location(l+u.Vector(*p.uu(*xyz)),False,False);a.set_actor_label(a.get_actor_label().replace('V5_','V6_',1));a.set_folder_path(u.Name(str(a.get_folder_path()).replace('V5/','V6/',1)))
def road(name,pts,width,color='main',sidewalk=False,skip_shared=False):
 v,f=[],[]
 for a,b in zip(pts,pts[1:]):
  if skip_shared and a[1]==137 and b[1]==137:continue
  dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
  if L<.01:continue
  nx,ny=-dy/L,dx/L;N=max(1,math.ceil(L/1.2));rows=[]
  for i in range(N+1):
   t=i/N;x,y,z=(p.mix(a[k],b[k],t) for k in range(3));rows.append([(x+nx*o,y+ny*o,z+.045) for o in(width/2,-width/2)])
  g.add_grid(v,f,rows)
 return surface(name,1,v,f,color,True)
def footpath(name,pts,width=2.8):
 v,f=[],[];g.add_ribbon(v,f,pts,width,lambda x,y:T.surface(x,y)+.055,step=.7,across=4)
 return surface('Path_'+name,1,v,f,'Path',True)
def siding(key,hexcolor,brick=False):
 # World-space procedural brick/siding: no duplicated textures or UV changes.
 m=g.material(key);edit=u.MaterialEditingLibrary
 pos=edit.create_material_expression(m,u.MaterialExpressionWorldPosition,-650,0)
 expr=edit.create_material_expression(m,u.MaterialExpressionCustom,-400,0)
 rgb=[int(hexcolor[i:i+2],16)/255 for i in(0,2,4)];rgb=[((c+.055)/1.055)**2.4 for c in rgb]
 ci=u.CustomInput();ci.set_editor_property('input_name','P');expr.set_editor_property('inputs',[ci]);expr.set_editor_property('output_type',u.CustomMaterialOutputType.CMOT_FLOAT3)
 c='float3('+','.join(str(x) for x in rgb)+')'
 code=('float row=floor(P.z/18.0); float2 uv=float2((P.x+P.y)/55.0+fmod(abs(row),2.0)*0.5,P.z/18.0); float2 f=frac(uv); float mortar=step(min(min(f.x,1-f.x),min(f.y,1-f.y)),0.045); float weather=0.86+0.14*sin(floor(uv.x)*17.0+row*2.1); return lerp('+c+'*weather,float3(.22,.21,.18),mortar);') if brick else ('float seam=step(frac(P.z/22.0),.045); float wear=.9+.1*sin((P.x+P.y)*.005);return '+c+'*wear*(1-.37*seam);')
 expr.set_editor_property('code',code);edit.connect_material_expressions(pos,'',expr,'P');edit.connect_material_property(expr,'',u.MaterialProperty.MP_BASE_COLOR);edit.recompile_material(m);g.save(m);return m

def main():
 if assets.does_asset_exist(p.MAP):
  assert not (out/'Construction_Complete.json').exists(), 'Completed V6 exists; use a reviewed repair script'
  assert (out/'Original_Building_Scale_Proof.json').exists(), 'Unknown pre-existing V6; refusing overwrite'
  assert level.load_level(p.MAP)  # Resume our initial, unchanged V5 duplicate after an API failure.
 else:assert level.new_level_from_template(p.MAP,old.MAP)
 copied=list(actors.get_all_level_actors());preserved=[];core=[];church=[];story={}
 for a in copied:
  n=a.get_actor_label();folder=str(a.get_folder_path())
  if '99_' in folder:archive(a);continue
  if n.startswith(('V5_Church_','V5_Basement_','V5_Descent_','V5_Escape_')):
   offset(a,(-40,-80,1));church.append(a);continue
  matched=False
  for b in p.BUILDINGS[:29]:
   if n.startswith('V5_'+b['id']+'_'):
    matched=True
    if any(x in n for x in ('Outbuilding','GardenFence','SideFence')):archive(a);break
    prev=old.BUILDING_BY_ID[b['id']];before=list(a.get_actor_scale3d().to_tuple());relocate(a,b,prev);core.append((a,b));preserved.append(dict(label=a.get_actor_label(),building=b['id'],original_scale=before,v6_scale=list(a.get_actor_scale3d().to_tuple())));break
  if matched:continue
  cls=a.get_class().get_name()
  if cls=='PenanceV5WorldDirector':
   a.checkpoints=[u.Vector(*p.uu(*q)) for q in p.CHECKPOINTS];a.chase_path=[u.Vector(*p.uu(x-40,y-80,z+1)) for x,y,z in[(193,367,5.32),(193,376,5.32),(193,386,5.32),(179,388,5.32)]];a.set_actor_label('V6_Opening_Director');a.set_folder_path('V6/09_Story');story['director']=a;continue
  if cls=='PenanceStreamingDoor':
   offset(a,(-9,-12,0));a.exterior_exit_world=u.Vector(*p.uu(100,96,5.8));story['door']=a;continue
  if n.startswith('V5_House01_'):offset(a,(-9,-12,0));continue
  if cls=='PenanceObjectiveTrigger':
   move(a,(92,106,5.8) if 'HousePorch' in n else (58,60,5.6));a.set_actor_label(n.replace('V5_','V6_',1));a.set_folder_path('V6/09_Story/Objectives');continue
  if cls=='PlayerStart':move(a,p.CHECKPOINTS[0]);a.set_actor_rotation(u.Rotator(yaw=57),False);a.set_actor_label('V6_Arrival_PlayerStart');a.set_folder_path('V6/09_Story');continue
  if n=='V5_Memory_Car_AfterHouse':move(a,(90,104,5.6));a.set_actor_label('V6_Memory_Car_AfterHouse');a.set_folder_path('V6/09_Story');continue
  if n=='V5_ParkShortcut_Barrier':move(a,(91,170,T.surface(91,170)+.7));a.set_actor_label('V6_ParkShortcut_Barrier');a.set_folder_path('V6/09_Story');continue
  if n=='V5_Estate_Gate':move(a,(279,293,T.surface(279,293)+1));a.set_actor_rotation(u.Rotator(yaw=43),False);a.set_actor_label('V6_Estate_Gate');a.set_folder_path('V6/09_Story');continue
  if cls in('DirectionalLight','SkyLight','SkyAtmosphere','PostProcessVolume'):
   a.set_actor_label(n.replace('V5_','V6_',1));a.set_folder_path('V6/00_Geography');continue
  if n.startswith(('V5_Grave_','V5_GraveyardWall_')):offset(a,(-44,-49,0));L=a.get_actor_location();L.z=(T.surface(L.x/100,L.y/100)+(.45 if 'Grave_' in n else .6))*100;a.set_actor_location(L,False,False);continue
  if n.startswith(('V5_Tower_Leg_','V5_WaterTower_','V5_TownWater')):offset(a,(-5,-41,0));continue
  archive(a)
 assert len(preserved)>200 and len(church)>60
 (out/'Original_Building_Scale_Proof.json').write_text(json.dumps(preserved,indent=2)+'\n')
 print('V6_PRESERVED',len(preserved),'CHURCH',len(church))
 # New material assignments are instance overrides; shared V5 materials untouched.
 brick=siding('Brick','855C4C',True);red=siding('RedBrick','704C44',True);wood=siding('Siding','B0AC97');blue=siding('BlueSiding','848F8B')
 for a,b in core:
  n=a.get_actor_label();c=a.get_component_by_class(u.StaticMeshComponent)
  if c and any(q in n for q in('Wall','Front_','Header','Wing_','BellTower')):c.set_material(0,(wood if int(b['id'][1:])%3 else blue) if b['category']=='Residential' else red if b['id'] in('BARBER','LIBRARY','SCHOOL') else brick)
 # Terrain: sixteen tiles; church excavation remains aligned to its preserved floors.
 print('V6_TERRAIN')
 for ix in range(4):
  for iy,(y0,y1) in enumerate(zip((0,88,176,264),(88,176,264,350))):
   v,f=[],[];g.add_grid(v,f,[[(x,y,T.surface(x,y)) for x in range(ix*100,ix*100+101,2)] for y in range(y0,y1+1,2)])
   f=[tri for tri in f if not(132<sum(v[i][0] for i in tri)/3<158 and 270<sum(v[i][1] for i in tri)/3<324)]
   surface('Terrain_%d_%d'%(ix,iy),0,v,f,'Terrain',True)
 print('V6_STREETS')
 for name,r in p.ROADS.items():road('Road_'+name.replace(' ','_'),r['points'],r['width'],r['kind'],skip_shared=name=='Mill Road')
 # Continuous 1.8 m sidewalks, culled through other road junctions and bridge.
 for name,r in p.ROADS.items():
  if r['kind']=='service':continue
  for side in(-1,1):
   v,f=[],[]
   for a,b in zip(r['points'],r['points'][1:]):
    if name=='Mill Road' and (a[1]==137==b[1] or a[1]>=189):continue
    dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);nx,ny=-dy/L,dx/L;off=side*(r['width']/2+.95);N=max(1,math.ceil(L))
    rows=[]
    for i in range(N+1):
     t=i/N;x,y,z=(p.mix(a[k],b[k],t) for k in range(3));rows.append([(x+nx*(off+o),y+ny*(off+o),z+.11) for o in(.9,-.9)])
    g.add_grid(v,f,rows)
   def clear(tri):
    for j in tri:
     x,y,z=v[j]
     for other,q in p.ROADS.items():
      if other==name or {other,name}=={'Mill Road','Main Street'}:continue
      if min(p.project(x,y,a,b)[0] for a,b in zip(q['points'],q['points'][1:]))<q['width']/2+.25:return False
    return True
   f=[q for q in f if clear(q)];surface('Sidewalk_'+name.replace(' ','_')+str(side),1,v,f,'Path',True)
 for name,pts in p.PATHS.items():footpath(name.replace(' ','_'),pts)
 for k,pts in p.DRIVES.items():
  if k not in('CHURCH',):road('Drive_'+k,pts,3.1,'Path')
 road('Creek_Water',[(x,p.creek_y(x),0) for x in range(0,402,2)],7,'Creek').set_actor_enable_collision(False)
 box('MainBridge_Deck',2,(250,207.5,4.35),(7,37,.5),'Bridge')
 for x in(246.35,253.65):
  box('MainBridge_Rail_'+str(x),2,(x,207.5,5.2),(.16,37,1.2),'Metal')
  for y in range(190,227,3):box('Bridge_Post_%s_%s'%(x,y),2,(x,y,5),(.2,.2,1.5),'Metal')
 for y in(197,218):box('Bridge_Pier_'+str(y),2,(250,y,1.1),(6,1.2,6),'Stone')
 cy=p.creek_y(128);box('OldFootbridge',2,(128,cy,2.9),(2.6,34,.24),'Bridge')
 for y in(cy-17,cy+17):box('OldBridge_Closed_'+str(y),2,(128,y,3.9),(3,.3,1.8),'Metal');sign('FootbridgeClosed'+str(y),(128,y-1,4.3),'BRIDGE CLOSED',-90,.28)
 # Six new houses use the same simple shell conventions; no skeleton/player changes.
 for b in p.BUILDINGS[29:]:
  g.shell(b);part(b,'Foundation',(0,0,-.22),(b['w']+.5,b['d']+.5,.35),'Stone')
  for a in actors.get_all_level_actors():
   if a.get_actor_label().startswith('V6_'+b['id']+'_') and any(s in a.get_actor_label() for s in('Outbuilding','GardenFence','SideFence')):archive(a)
 # Parapets retain the original maximum building heights; roofs archived only in V6.
 for k in('DINER','BARBER','POST','LIBRARY','HALL','GAS','FIRE'):
  b=p.BUILDING_BY_ID[k]
  for a,_ in core:
   if a.get_actor_label()=='V6_'+k+'_GableRoof':archive(a)
  H=b['h']+b['roof']
  for x,y,w,d in[(0,-b['d']/2,b['w'],.24),(0,b['d']/2,b['w'],.24),(-b['w']/2,0,.24,b['d']),(b['w']/2,0,.24,b['d'])]:
   part(b,'Parapet_'+str(x)+'_'+str(y),(x,y,b['h']+b['roof']/2),(w,d,b['roof']), 'Brick')
  part(b,'FlatRoof',(0,0,H-.28),(b['w'],b['d'],.18),'Roof')
  part(b,'Cornice',(0,-b['d']/2-.18,H-.16),(b['w']+.3,.38,.22),'White')
  part(b,'Shopfront',(0,-b['d']/2-.15,1.45),(b['w']*.69,.05,1.8),'Glass',False)
  for x in(-b['w']*.35,0,b['w']*.35):
   if H>6:part(b,'UpperWindow_'+str(x),(x,-b['d']/2-.17,4.9),(1.3,.06,1.6),'Glass',False)
  sign(k+'_HistoricSign',g.local(b,0,-b['d']/2-.3,3.1),{'BARBER':'PENANCE HARDWARE  /  BARBER','DINER':'MILL ROAD DINER','POST':'UNITED STATES POST OFFICE','GAS':'LAST STOP  •  GAS & GROCERY'}.get(k,b['name'].upper()),b['yaw']-90,.32 if k=='GAS' else .42)
 # Shared district details: foundations original-sized; front windows, rear entries.
 parcels=json.loads((out/'Parcels.json').read_text())['parcels']
 for i,b in enumerate(p.BUILDINGS):
  if b['category']=='Residential':
   for x in(-b['w']*.3,b['w']*.3):
    part(b,'FrontWindow_'+str(x),(x,-b['d']/2-.16,1.9),(1.35,.06,1.45),'Glass',False)
    part(b,'WindowSill_'+str(x),(x,-b['d']/2-.23,1.12),(1.55,.24,.10),'White',False)
   # Lot fence deliberately stays off streets and out of the opening routes.
   poly=next(a['polygon'] for a in parcels if a['id']==b['id'])
   for j,(a,c) in enumerate(zip(poly,poly[1:])):
    mx,my=(a[0]+c[0])/2,(a[1]+c[1])/2;L=math.dist(a,c)
    if L<2 or T.road_candidate(mx,my)[0]<6 or (b['id']=='H01') or my<b['y']:continue
    z=T.surface(mx,my);yaw=math.degrees(math.atan2(c[1]-a[1],c[0]-a[0]));box(b['id']+'_RearFence_'+str(j),3,(mx,my,z+.55),(L,.09,1.1),'White',False,yaw)
   endpoint=p.DRIVES[b['id']][-1];x,y=endpoint[:2];box(b['id']+'_Mailbox',8,(x+2,y,T.surface(x+2,y)+.9),(.35,.48,.28),'Metal',False);box(b['id']+'_MailPost',8,(x+2,y,T.surface(x+2,y)+.4),(.09,.09,.8),'Trunk',False)
   # Rear outbuilding only if its footprint clears every main house and road.
   gx,gy=g.local(b,b['w']/2+3.5,b['d']/2+2,0)[:2]
   if gx>5 and gx<395 and gy<345 and T.road_candidate(gx,gy)[0]>7 and all(math.hypot(gx-q['x'],gy-q['y'])>max(q['w'],q['d'])/2+4 for q in p.BUILDINGS):
    z=T.surface(gx,gy);box(b['id']+'_Garage',3,(gx,gy,z+1.4),(4.2,5.2,2.8),'Siding',True,b['yaw']);box(b['id']+'_GarageRoof',3,(gx,gy,z+2.9),(4.6,5.6,.2),'Roof',False,b['yaw'])
  elif b['id'] not in ('CHURCH','FOSTER'):
   part(b,'RearServiceDoor',(0,b['d']/2+.15,1.05),(1,.1,2.1),'Dark',False)
 # Commercial service alley and civic square.
 road('Rear_Service_Alley',[(115,162,5.1),(183,163,5.1),(195,164,5.2)],3.5,'service')
 box('CivicSquare',5,(211,149,5.05),(23,10,.18),'Path')
 for x in(204,214,221):bench('Square_'+str(x),x,151,5.15,0)
 arrival();park();landmarks();foliage()
 # Reservation markers are editor-only and carry no door/progression logic.
 reservations=[]
 for k,notes,floors,depth in [('DINER','shop / store / office',2,3),('LIBRARY','reading rooms / records / archives',2,4),('HALL','public hall / offices / records',3,4),('SCHOOL','classrooms / staff / utility',2,3),('CHURCH','nave preserved; future crypt / service passages',2,8),('FOSTER','upper floors / cellar / concealed maintenance',3,10)]:
  b=p.BUILDING_BY_ID[k];a=spawn(u.TargetPoint,'FUTURE_Interior_'+k,10,p.uu(b['x'],b['y'],b['z']-depth));a.set_editor_property('is_editor_only_actor',True);a.tags=[u.Name('V6_FutureInterior_NotImplemented')];reservations.append(dict(building=k,center_m=[b['x'],b['y'],b['z']],width_m=b['w']-1,depth_m=b['d']-1,floors=floors,below_ground_m=depth,status='RESERVED ONLY',notes=notes))
 (out/'Future_Interior_Reservations.json').write_text(json.dumps(reservations,indent=2)+'\n')
 for i,q in enumerate(p.CHECKPOINTS):
  if i!=1:spawn(u.TargetPoint,'Checkpoint_'+str(i),10,p.uu(*q))
 for name,xy,target in p.VIEWS:g.camera(name,(*xy,T.surface(*xy)+1.65),target)
 g.camera('Overhead',(200,175,600),(200,175,0),430)
 # Dynamic overcast lighting, explicit single atmosphere sun and priority.
 for a in actors.get_all_level_actors():
  if '99_' in str(a.get_folder_path()):continue
  c=a.get_component_by_class(u.LightComponentBase)
  if c:c.set_mobility(u.ComponentMobility.MOVABLE)
  if isinstance(c,u.DirectionalLightComponent):
   main='Afternoon' in a.get_actor_label();c.set_forward_shading_priority(2 if main else 0);c.set_atmosphere_sun_light(main);c.set_intensity(2.4 if main else .5)
   if main:c.set_light_color(u.LinearColor(.76,.83,1));a.set_actor_rotation(u.Rotator(pitch=-34,yaw=-48),False)
  if isinstance(c,u.SkyLightComponent):c.set_intensity(1.25)
 fog=spawn(u.ExponentialHeightFog,'ValleyMist',0,(20000,18000,200));fc=fog.get_component_by_class(u.ExponentialHeightFogComponent);fc.set_fog_density(.004);fc.set_start_distance(5500);fc.set_fog_max_opacity(.6)
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();world.get_world_settings().set_editor_property('force_no_precomputed_lighting',True)
 assert u.EditorLoadingAndSavingUtils.save_map(world,p.MAP)
 (out/'Construction_Complete.json').write_text(json.dumps(dict(map=p.MAP,actor_count=len(actors.get_all_level_actors()),source=old.MAP),indent=2)+'\n')
 print('PENANCE_V6_SAVED',len(actors.get_all_level_actors()))

def bench(name,x,y,z,yaw):
 for dx in(-.7,.7):box('BenchLeg_'+name+str(dx),8,(x+dx,y,z+.25),(.12,.5,.5),'Metal',False)
 box('BenchSeat_'+name,8,(x,y,z+.5),(1.9,.6,.12),'Trunk',True,yaw);box('BenchBack_'+name,8,(x,y+.27,z+.85),(1.9,.1,.6),'Trunk',False,yaw)
def car(name,x,y,z,yaw=0):
 box(name+'_Body',8,(x,y,z+.65),(1.8,4.2,1.3),'Utility',True,yaw);box(name+'_Cabin',8,(x,y,z+1.35),(1.6,2.2,.5),'Glass',False,yaw)
 for side in(-1,1):
  for dy in(-1.3,1.3):box(name+'_Wheel'+str(side)+str(dy),8,(x+side*.88,y+dy,z+.32),(.22,.65,.65),'Dark',False)
def line(name,a,b,thickness,color='Metal',collision=False,folder=8):
 A=u.Vector(*p.uu(*a));B=u.Vector(*p.uu(*b));D=B-A;L=D.length()/100;rotation=u.MathLibrary.find_look_at_rotation(A,B)
 obj=box(name,folder,tuple((a[k]+b[k])/2 for k in range(3)),(L,thickness,thickness),color,collision);obj.set_actor_rotation(rotation,False);return obj

def arrival():
 # Washout and boulders are behind the PlayerStart and visible on turning back.
 box('Washout_Gap',0,(25,12,2.4),(12,7,1.5),'Dark',True,55)
 box('Arrival_Barricade',8,(27,15,5.4),(7,.3,1.2),'Metal',True,-33);sign('RoadClosed',(27,14,6.1),'ROAD WASHED OUT\nNO THROUGH ROAD',57,.33)
 for i in range(12):
  x,y=20+rng.random()*11,6+rng.random()*7;box('Washout_Debris'+str(i),0,(x,y,3.4+rng.random()),(rng.uniform(1,2.4),1.6,1),'Stone',True,rng.randrange(180))
 for s in(-1,1):
  a=(30+s*5,22,4.9);b=(40+s*5,36,4.9);line('Guardrail'+str(s),a,b,.16)
  for t in(0,.33,.67,1):box('RailPost'+str(s)+str(t),8,(p.mix(a[0],b[0],t),p.mix(a[1],b[1],t),4.6),(.12,.12,1.3),'Metal')
  road('DrainageDitch'+str(s),[(29+s*6,21,4.2),(39+s*6,36,4.1)],.8,'Dark')
 sign('Welcome',(40,30,7),'PENANCE\nPopulation  2,431',-120,.48)
 # Full forecourt at the existing full-sized gas store.
 box('Gas_Forecourt',4,(59,60,4.98),(22,25,.18),'Asphalt')
 for x in(52,64):
  for y in(53,67):box('CanopyPost'+str(x)+str(y),4,(x,y,6.9),(.18,.18,3.8),'Metal')
 box('Gas_Canopy',4,(58,60,8.95),(15,16,.35),'White',False)
 box('Gas_Canopy_Fascia',4,(65.5,60,8.8),(.15,16,.55),'RedBrick',False)
 for x in(55,61):
  for y in(55,65):
   box('FuelPump'+str(x)+str(y),4,(x,y,5.8),(.65,.65,1.6),'White',True);box('PumpScreen'+str(x)+str(y),4,(x+.34,y,6.1),(.03,.4,.35),'Dark',False);line('PumpHose'+str(x)+str(y),(x+.4,y,6.3),(x+.5,y,5.3),.045,'Dark')
 sign('LastStopPylon',(70,49,9),'LAST STOP\nGAS  •  GROCERY',-90,.48)
 box('GasSignPost',8,(70,49,6.7),(.18,.18,4.5),'Metal',True)
 car('Stranded_Sedan',61,47,5.1,0)
 for x in(51,54,57):
  line('GasParking'+str(x),(x,70,5.09),(x,73,5.09),.06,'Faded')
 for x in(40,42):box('GasBins'+str(x),8,(x,66,5.5),(.7,.75,1.0),'Dark',True)
 box('Gas_AC',8,(38.5,56,5.7),(.6,1.1,1.2),'Metal',False)
 # Occludes the first house until the road bends past the gas station.
 box('Arrival_Hedge',7,(50,46,6.1),(6,1.3,2.4),'Woods',True,0)
 # Abandoned bus shelter, kept beside rather than inside the carriageway.
 box('BusShelter_Slab',8,(70,83,4.9),(3,5,.14),'Path')
 box('BusShelter_Roof',8,(70,83,7.5),(3,5,.15),'Roof',False)
 box('BusShelter_Back',8,(68.7,83,6.1),(.1,4.7,2.3),'Glass',False)
 for y in(80.8,85.2):box('BusShelter_Post'+str(y),8,(71.2,y,6.1),(.10,.1,2.5),'Metal')
 bench('BusShelter',69.7,83,5,90);sign('BusSchedule',(68.85,81.3,6.2),'COUNTY BUS\n6:40  /  17:20',0,.15)
 box('Forgotten_Suitcase',8,(70.4,84.3,5.2),(.65,.28,.4),'Trunk',False)
 sign('BusStop',(73,85,7),'BUS STOP',-90,.22)
 # Utility poles and gently sagged wires follow the opening road.
 poles=[(25,30),(42,43),(68,51),(71,75),(71,98),(81,123),(108,142),(139,142),(172,142),(205,142)]
 for i,(x,y) in enumerate(poles):
  z=T.surface(x,y);box('UtilityPole'+str(i),8,(x,y,z+4.3),(.24,.24,8.6),'Trunk',True);box('Crossarm'+str(i),8,(x,y,z+7.9),(2,.18,.18),'Trunk',False)
  if i:
   x0,y0=poles[i-1];z0=T.surface(x0,y0)+8.2
   for s in(-.75,.75):
    pts=[(p.mix(x0,x,t)+s,p.mix(y0,y,t),p.mix(z0,z+8.2,t)-.7*math.sin(math.pi*t)) for t in(0,.25,.5,.75,1)]
    for j,(a,b) in enumerate(zip(pts,pts[1:])):line('Wire'+str(i)+str(s)+str(j),a,b,.018,'Dark')
 for i,(x,y) in enumerate([(118,143),(176,142),(208,143),(262,89),(315,113)]):car('Parked_'+str(i),x,y,T.surface(x,y),90)
 # Crosswalks are paint at asphalt height, not raised collision bars.
 for x,y in[(78,89),(139,137),(219,137)]:
  z=T.road_candidate(x,y)[1]+.054
  for j in range(-3,4):box('Crossing'+str(x)+str(j),1,(x+j*.55,y,z),(.3,6.5,.012),'Faded',False)
 for i,(x,y) in enumerate([(77,56),(78,103),(139,136),(248,155)]):box('StormDrain'+str(i),1,(x-3.2,y,T.road_candidate(x,y)[1]+.056),(.4,.9,.02),'Dark',False)

def park():
 road('Park_Path',[(91,170,5.25),(100,187,5.2),(110,196,5.2)],2.8,'Path')
 for i,(x,y) in enumerate([(96,186),(108,186),(103,194)]):bench('Park'+str(i),x,y,T.surface(x,y)+.05,0)
 for x in(104,112):box('SwingFrame'+str(x),5,(x,194,T.surface(x,194)+2.2),(.15,.15,4.4),'Metal')
 line('SwingCrossbar',(104,194,9.3),(112,194,9.3),.18)
 for x in(106,110):
  line('SwingRopeL'+str(x),(x-.35,194,9.3),(x-.35,194,5.6),.035);line('SwingRopeR'+str(x),(x+.35,194,9.3),(x+.35,194,5.6),.035);box('SwingSeat'+str(x),5,(x,194,5.6),(.85,.4,.08),'Trunk',False)
 sign('ParkSign',(91,174,6.8),'ORCHARD PARK',-90,.3)

def landmarks():
 b=p.BUILDING_BY_ID['CHURCH']
 for x in(-12.7,12.7):
  for y in(-11,-3,5,13):part(b,'StoneQuoin'+str(x)+str(y),(x,y,4),(.35,.85,8),'Stone',False)
 for x in(-6,6):part(b,'FrontTallWindow'+str(x),(x,-18.17,5),(1.1,.04,3.6),'Glass',False)
 sign('Church_Inscription',(145,271.8,16.6),'ST. AGNES  •  1908',-90,.35)
 for i,(x,y) in enumerate([(136,267),(154,267),(135,263),(155,263)]):box('ChurchLawnWall'+str(i),6,(x,y,11.5),(2,.4,1),'Stone',True)
 b=p.BUILDING_BY_ID['FOSTER']
 for x in(-11,-5,5,11):
  for z in(2.5,6.5,9):part(b,'EstateWindow'+str(x)+str(z),(x,-12.65,z),(1.2,.08,1.7),'Glass',False)
 for s in(-1,1):
  part(b,'GardenHedge'+str(s),(s*25,0,1.0),(1,38,2),'Woods',True)
  part(b,'GardenWalk'+str(s),(s*27,0,.03),(2,38,.1),'Path',False)
 # Future garden/perimeter stays inside site boundary.
 road('Estate_GardenWalk',[(305,314,13),(326,317,13),(347,314,13)],2.4,'Path')
 for x,y in[(310,314),(337,318)]:box('EstateGardenBed'+str(x),6,(x,y,13.3),(6,3,.6),'Stone',False)
 # Faded advertisements and ordinary signs, not apocalypse dressing.
 sign('HardwareWallAd',(157.2,151,9.5),'PENANCE\nHARDWARE\nSINCE 1926',0,.33)
 sign('DinerOpen',(124,146.7,7),'COFFEE  •  PIE',-90,.28)
 for x,y in[(122,164),(182,164),(216,172)]:box('ServiceBins'+str(x),8,(x,y,T.surface(x,y)+.6),(1.4,.8,1.2),'Metal',True)
 # Mail left outdoors; laundry and a bicycle are quiet interrupted routines.
 for i in range(4):box('UncollectedMail'+str(i),8,(91.7+i*.12,106,4.98),(.17,.23,.02),'White',False,rng.randrange(40))
 line('LaundryLine',(112,91,7.0),(119,91,7.0),.025,'Dark')
 for i in range(4):box('Laundry'+str(i),8,(113+i*1.3,91,6.55),(.65,.03,.8),'White',False)

def foliage():
 # Existing engine sphere/cylinder LODs + HISM culling; no scattered per-tree actors.
 sphere=u.load_asset('/Engine/BasicShapes/Sphere');cylinder=u.load_asset('/Engine/BasicShapes/Cylinder');cone=u.load_asset('/Engine/BasicShapes/Cone')
 groups={}
 for key,mesh,color in [('CrownA',sphere,'Woods'),('CrownB',sphere,'Leaf'),('Pine',cone,'Woods'),('Trunk',cylinder,'Trunk'),('Shrub',sphere,'Leaf'),('Deadwood',cylinder,'Trunk')]:
  g.material(color).set_editor_property('used_with_instanced_static_meshes',True);g.save(g.material(color))
  a=spawn(u.PenanceV6InstancedSet,'Foliage_'+key,7,(0,0,0));c=a.instances;c.set_static_mesh(mesh);c.set_material(0,g.material(color));groups[key]=c
 clusters=[(14,25,16),(84,22,18),(170,25,30),(326,32,26),(390,84,15),(390,228,15),(280,338,30),(210,300,22),(92,286,25),(26,269,22),(220,216,12),(82,237,18)]
 def allowed(x,y):
  if not(2<x<398 and 2<y<348):return False
  if abs(y-p.creek_y(x))<9:return False
  if T.road_candidate(x,y)[0]<7:return False
  if any(abs(x-b['x'])<max(b['w'],b['d'])/2+8 and abs(y-b['y'])<max(b['w'],b['d'])/2+8 for b in p.BUILDINGS):return False
  if 82<x<122 and 169<y<201:return False
  if 333<x<374 and 171<y<205:return False
  if any(min(p.project(x,y,a,b)[0] for a,b in zip(q,q[1:]))<5 for q in p.PATHS.values()):return False
  if any(min(p.project(x,y,a,b)[0] for a,b in zip(q,q[1:]))<5 for q in p.DRIVES.values()):return False
  return True
 count=0
 for i in range(2300):
  cx,cy,r=clusters[i%len(clusters)];x,y=rng.gauss(cx,r*.55),rng.gauss(cy,r*.55)
  if i%4==0:
   side=i%16//4;x,y=(rng.uniform(3,397),rng.uniform(2,9)) if side==0 else (rng.uniform(3,397),rng.uniform(341,348)) if side==1 else (rng.uniform(2,9),rng.uniform(3,347)) if side==2 else (rng.uniform(391,398),rng.uniform(3,347))
  if not allowed(x,y):continue
  z=T.surface(x,y);h=rng.uniform(7,16);r=rng.uniform(1.8,3.6);yaw=rng.uniform(0,360)
  groups['Trunk'].add_instance(u.Transform(location=u.Vector(*p.uu(x,y,z+h*.3)),rotation=u.Rotator(yaw=yaw),scale=u.Vector(.23,.23,h*.6)),False)
  pine=rng.random()<.2
  if pine:groups['Pine'].add_instance(u.Transform(location=u.Vector(*p.uu(x,y,z+h*.65)),rotation=u.Rotator(yaw=yaw),scale=u.Vector(r*2,r*2,h*.7)),False)
  else:
   for j in range(3):
    ox,oy=(j-1)*r*.5,rng.uniform(-.6,.6)*r
    groups['CrownA' if count%3 else 'CrownB'].add_instance(u.Transform(location=u.Vector(*p.uu(x+ox,y+oy,z+h*.73+rng.uniform(-.5,.5))),rotation=u.Rotator(yaw=yaw),scale=u.Vector(r*1.8,r*1.6,h*.46)),False)
  if count%3==0:groups['Shrub'].add_instance(u.Transform(location=u.Vector(*p.uu(x+1,y+1,z+.6)),scale=u.Vector(2.1,1.5,1.2)),False)
  if count%28==0:groups['Deadwood'].add_instance(u.Transform(location=u.Vector(*p.uu(x+2,y,z+.3)),rotation=u.Rotator(pitch=78,yaw=yaw),scale=u.Vector(.18,.18,3.8)),False)
  count+=1
 (out/'Foliage.json').write_text(json.dumps(dict(tree_count=count,instancing='HISM',cull_start_m=180,cull_end_m=320,meshes='Engine primitives with built-in LODs',seed=62026),indent=2)+'\n')
 print('V6_FOREST',count)
if __name__=='__main__':main()
