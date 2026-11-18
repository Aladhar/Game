"""Final V6-only collision, grade, lighting and canopy LOD pass."""
from pathlib import Path
import sys,json,math
import unreal as u
sys.path.insert(0,str(Path(__file__).resolve().parent));import Build_Penance_Town_V6 as b;import Penance_Town_V6_Design as p
assert b.level.load_level(p.MAP);A=b.actors;T=p.Terrain()
for a in list(A.get_all_level_actors()):
 if '99_' in str(a.get_folder_path()):continue
 n=a.get_actor_label()
 if n.startswith(('V6_Terrain_','V6_Road_Tower_Service','V6_Road_Grave_Lane','V6_Path_Estate_back_path','V6_Drive_')):b.archive(a)
 if n.startswith('V6_FOSTER_GardenHedge'):
  h=p.BUILDING_BY_ID['FOSTER'];s=-1 if n.endswith('-1') else 1;loc=b.g.local(h,s*25,4,1);a.set_actor_location(u.Vector(*p.uu(*loc)),False,False);a.set_actor_scale3d(u.Vector(1,30,2))
 if n=='V6_Review_Foster' or n=='V6_Review_Church':
  name=n.replace('V6_Review_','');q=next(x for x in p.VIEWS if x[0]==name);eye=u.Vector(*p.uu(*q[1],T.surface(*q[1])+1.65));a.set_actor_location(eye,False,False);a.set_actor_rotation(u.MathLibrary.find_look_at_rotation(eye,u.Vector(*p.uu(*q[2]))),False)
 c=a.get_component_by_class(u.DirectionalLightComponent)
 if c:
  intensity=6 if 'Afternoon' in n else 5 if 'SouthFill' in n else 4;c.set_intensity(intensity);c.set_light_color(u.LinearColor(.82,.88,1));c.set_forward_shading_priority(2 if 'Afternoon' in n else 0)
 sc=a.get_component_by_class(u.SkyLightComponent)
 if sc:sc.set_intensity(3);sc.recapture_sky()
for ix in range(4):
 for iy,(y0,y1) in enumerate(zip((0,88,176,264),(88,176,264,350))):
  v,f=[],[];b.g.add_grid(v,f,[[(x,y,T.surface(x,y)) for x in range(ix*100,ix*100+101,2)] for y in range(y0,y1+1,2)])
  f=[tri for tri in f if not(132<sum(v[i][0] for i in tri)/3<158 and 270<sum(v[i][1] for i in tri)/3<324)]
  b.surface('Terrain_%d_%d_Final'%(ix,iy),0,v,f,'Terrain')
for name in('Tower Service','Grave Lane'):b.road('Road_'+name.replace(' ','_')+'_Final',p.ROADS[name]['points'],p.ROADS[name]['width'],p.ROADS[name]['kind'])
for k,pts in p.DRIVES.items():
 if k!='CHURCH':b.road('Drive_'+k+'_Final',pts,3.1,'Path')
b.footpath('Estate_back_path_Final',p.PATHS['Estate back path'])
b.box('WestStair_UpperJoint',6,(137,317.73,10.9),(3,.4,.2),'Stone')
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert u.EditorLoadingAndSavingUtils.save_map(w,p.MAP)
u.SystemLibrary.execute_console_command(w,'MAP CHECK DONTDISPLAYDIALOG');print('V6_FINISHED')
