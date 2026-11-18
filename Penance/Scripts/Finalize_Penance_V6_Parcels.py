"""Final saved-world parcel alignment and off-route road cleanup; V6 only."""
import sys,math,json
from pathlib import Path
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent));import Build_Penance_Town_V6 as b;import Penance_Town_V6_Design as p
assert b.level.load_level(p.MAP);A=b.actors;T=p.Terrain();out=b.out
for a in list(A.get_all_level_actors()):
 if '99_' in str(a.get_folder_path()):continue
 n=a.get_actor_label()
 if n.startswith(('V6_Terrain_','V6_Road_Tower_Service','V6_Sidewalk_Foundry_Cut','V6_Drive_H01')) or '_RearFence_' in n:b.archive(a)
 if n.startswith(('V6_Tower_Leg_','V6_WaterTower_','V6_TownWater')):
  loc=a.get_actor_location();loc.x=(51 if '_Leg_27_' in n else 57 if '_Leg_33_' in n else 54)*100;loc.y=(189 if n.endswith('_221') else 195 if n.endswith('_227') else 186.9 if 'TownWater' in n else 192)*100;a.set_actor_location(loc,False,False)
 if n in('V6_Review_Foster','V6_Review_Church'):
  name=n.replace('V6_Review_','');q=next(x for x in p.VIEWS if x[0]==name);eye=u.Vector(*p.uu(*q[1],T.surface(*q[1])+1.65));a.set_actor_location(eye,False,False);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(eye,u.Vector(*p.uu(*q[2]))),False)
for ix in range(4):
 for iy,(y0,y1) in enumerate(zip((0,88,176,264),(88,176,264,350))):
  v,f=[],[];b.g.add_grid(v,f,[[(x,y,T.surface(x,y)) for x in range(ix*100,ix*100+101,2)] for y in range(y0,y1+1,2)])
  f=[tri for tri in f if not(132<sum(v[i][0] for i in tri)/3<158 and 270<sum(v[i][1] for i in tri)/3<324)];b.surface('Terrain_%d_%d_ParcelFinal'%(ix,iy),0,v,f,'Terrain')
b.road('Road_Tower_Service_ParcelFinal',p.ROADS['Tower Service']['points'],4,'service');b.road('Drive_H01_ParcelFinal',p.DRIVES['H01'],2.6,'Path')
# Re-cut the Foundry sidewalks against the relocated Grave Lane junction.
r=p.ROADS['Foundry Cut']
for side in(-1,1):
 v,f=[],[]
 for a,c in zip(r['points'],r['points'][1:]):
  dx,dy=c[0]-a[0],c[1]-a[1];L=math.hypot(dx,dy);nx,ny=-dy/L,dx/L;off=side*(r['width']/2+.95);N=max(1,math.ceil(L));rows=[]
  for i in range(N+1):
   t=i/N;x,y,z=(p.mix(a[k],c[k],t) for k in range(3));rows.append([(x+nx*(off+o),y+ny*(off+o),z+.11) for o in(.9,-.9)])
  b.g.add_grid(v,f,rows)
 def clear(tri):
  for i in tri:
   x,y,z=v[i]
   for name,q in p.ROADS.items():
    if name=='Foundry Cut':continue
    if min(p.project(x,y,a,c)[0] for a,c in zip(q['points'],q['points'][1:]))<q['width']/2+.6:return False
  return True
 b.surface('Sidewalk_Foundry_Cut_ParcelFinal'+str(side),1,v,[q for q in f if clear(q)],'Path')
# Garages retain their size, adjusting three centers into their owner's lot.
for item in json.loads((out/'Garage_Adjustments.json').read_text()):
 h=p.BUILDING_BY_ID[item['id']]
 for a in A.get_all_level_actors():
  if a.get_actor_label() not in('V6_'+item['id']+'_Garage','V6_'+item['id']+'_GarageRoof') or '99_' in str(a.get_folder_path()):continue
  if not item['center']:b.archive(a);continue
  x,y=item['center'];z=T.surface(x,y)+(2.9 if a.get_actor_label().endswith('Roof') else 1.4);a.set_actor_location(u.Vector(*p.uu(x,y,z)),False,False)
 if item['center']:
  x,y=item['center'];angle=math.radians(h['yaw']);front=(x+math.sin(angle)*2.65,y-math.cos(angle)*2.65,T.surface(x,y)+1.0);b.box(item['id']+'_GarageRollup',3,front,(2.7,.05,2.0),'Dark',False,h['yaw'])
for item in json.loads((out/'Parcels.json').read_text())['parcels']:
 h=p.BUILDING_BY_ID[item['id']]
 if h['category']!='Residential' or h['id']=='H01':continue
 poly=item['polygon']
 for j,(a,c) in enumerate(zip(poly,poly[1:])):
  x,y=(a[0]+c[0])/2,(a[1]+c[1])/2;L=math.dist(a,c)
  if L<2 or T.road_candidate(x,y)[0]<6 or y<h['y']:continue
  if any(min(p.project(x,y,a,c)[0] for a,c in zip(d,d[1:]))<2.8 for d in p.DRIVES.values()):continue
  b.box(h['id']+'_RearFence_Final_'+str(j),3,(x,y,T.surface(x,y)+.55),(L,.09,1.1),'White',False,math.degrees(math.atan2(c[1]-a[1],c[0]-a[0])))
# Small historical street furniture, no new gameplay systems.
for i,(x,y,text) in enumerate([(110,142,'MAIN ST  /  MILL RD'),(70,91,'ORCHARD LOOP'),(143,131,'BRIAR RISE'),(319,164,'GRAVE LANE'),(26,135,'TOWER SERVICE')]):
 z=T.surface(x,y);b.box('StreetSignPost_'+str(i),8,(x,y,z+1.25),(.075,.075,2.5),'Metal',False);b.sign('StreetSign_'+str(i),(x,y,z+2.35),text,-90,.17)
# A bicycle left near the bus shelter, with wheels and frame rather than a marker cube.
x,y=67,76;z=T.surface(x,y)
for wheel in(0,1.15):
 for j in range(12):
  a=j*math.tau/12;c=(j+1)*math.tau/12;b.line('BicycleWheel_'+str(wheel)+'_'+str(j),(x+wheel+.31*math.cos(a),y,z+.33+.31*math.sin(a)),(x+wheel+.31*math.cos(c),y,z+.33+.31*math.sin(c)),.035,'Dark')
for j,(a,c) in enumerate([((0,.33),(.45,.75)),((.45,.75),(.7,.33)),((.7,.33),(0,.33)),((.45,.75),(.95,.75)),((.95,.75),(1.15,.33)),((.7,.33),(.95,.75))]):b.line('BicycleFrame_'+str(j),(x+a[0],y,z+a[1]),(x+c[0],y,z+c[1]),.035,'Metal')
b.box('BicycleSeat',8,(x+.43,y,z+.83),(.22,.12,.06),'Dark',False)
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert u.EditorLoadingAndSavingUtils.save_map(w,p.MAP);print('V6_PARCELS_FINAL_SAVED')
