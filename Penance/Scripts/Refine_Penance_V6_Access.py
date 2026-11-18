"""V6-only road/yard grading repair and final material usage; idempotent."""
import sys,math,json
from pathlib import Path
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent))
import Penance_Town_V6_Design as p
import Build_Penance_Town_V6 as b
assert b.level.load_level(p.MAP)
A=b.actors;T=p.Terrain();allactors=list(A.get_all_level_actors())
def retire_matching(prefix):
 for a in A.get_all_level_actors():
  if '99_' not in str(a.get_folder_path()) and a.get_actor_label().startswith(prefix):b.archive(a)
# On a revised road layout, regenerate only V6 terrain; V5 geometry remains untouched.
for a in allactors:
 n=a.get_actor_label()
 if '99_' in str(a.get_folder_path()):continue
 if n.startswith('V6_Terrain_') or n.startswith('V6_Road_Tower_Service') or n=='V6_Path_Bridge_approach':b.archive(a)
 if n.startswith(('V6_Tower_Leg_','V6_WaterTower_','V6_TownWater')):
  q=a.get_actor_location();q.y=(180 if n.endswith('_221') else 186 if n.endswith('_227') else 177 if 'TownWater' in n else 183)*100;a.set_actor_location(q,False,False)
for ix in range(4):
 for iy,(y0,y1) in enumerate(zip((0,88,176,264),(88,176,264,350))):
  v,f=[],[];b.g.add_grid(v,f,[[(x,y,T.surface(x,y)) for x in range(ix*100,ix*100+101,2)] for y in range(y0,y1+1,2)])
  f=[tri for tri in f if not(132<sum(v[i][0] for i in tri)/3<158 and 270<sum(v[i][1] for i in tri)/3<324)]
  b.surface('Terrain_%d_%d_Graded'%(ix,iy),0,v,f,'Terrain')
b.road('Road_Tower_Service_Graded',p.ROADS['Tower Service']['points'],4,'service');b.footpath('Bridge_approach_Graded',p.PATHS['Bridge approach'])
b.box('Church_NaveFrontFloorJoint',6,(152,273.8,10.9),(2.2,2.9,.2),'Stone')
for key in('Woods','Leaf','Trunk'):
 m=b.g.material(key);m.set_editor_property('used_with_instanced_static_meshes',True);u.MaterialEditingLibrary.recompile_material(m);b.g.save(m)
# Distinct new rooflines, preserving the same outer footprint and peak height.
for k in('H19',):
 house=p.BUILDING_BY_ID[k];retire_matching('V6_'+k+'_GableRoof');w,d,h,r=house['w']+.8,house['d']+.8,house['h'],house['roof']
 v=[b.g.local(house,*q) for q in[(-w/2,-d/2,h),(w/2,-d/2,h),(w/2,d/2,h),(-w/2,d/2,h),(0,-d/2+2,h+r),(0,d/2-2,h+r)]]
 b.surface(k+'_HipRoof',3,v,[(0,1,4),(1,2,5),(1,5,4),(2,3,5),(3,0,4),(3,4,5)],'Roof')
for k in('H18','H20'):
 house=p.BUILDING_BY_ID[k];b.part(house,'Dormer',(0,-house['d']/4,house['h']+.7),(2.5,2,1.4),'Siding',False);b.part(house,'DormerRoof',(0,-house['d']/4,house['h']+1.45),(2.8,2.3,.15),'Roof',False)
for a in A.get_all_level_actors():
 n=a.get_actor_label()
 if any(n.startswith('V6_H'+str(i)+'_') for i in range(15,21)) and any(q in n for q in('Wall','Front_','Header')) and '99_' not in str(a.get_folder_path()):
  c=a.get_component_by_class(u.StaticMeshComponent)
  if c:c.set_material(0,b.g.material('Siding'))
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert u.EditorLoadingAndSavingUtils.save_map(w,p.MAP)
print('V6_ACCESS_REFINED')
