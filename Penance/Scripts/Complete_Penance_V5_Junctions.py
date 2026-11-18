"""Finish curb breaks at junctions and the water-tower service-road bend."""
import sys,math
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(__file__).resolve().parent))
import Penance_Town_V5_Design as p
import Build_Penance_Town_V5 as g
assert g.level.load_level(p.MAP);actors={a.get_actor_label():a for a in g.actor_api.get_all_level_actors()};t=p.Terrain()
def archive(name):
 a=actors.get('V5_'+name)
 if a:a.set_actor_enable_collision(False);a.set_actor_hidden_in_game(True);a.get_component_by_class(ue.StaticMeshComponent).set_visibility(False);a.set_folder_path(ue.Name('V5/99_Trash_Archive'))
archive('Road_Tower_Service');g.road_surface('Road_Tower_Service_Final',p.ROADS['Tower Service']['points'],4,'service')
for ix,iy in[(0,1),(0,2)]:
 archive('Terrain_Final_%s_%s'%(ix,iy));v,f=[],[];g.add_grid(v,f,[[(x,y,t.surface(x,y)) for x in range(ix*120,ix*120+121,2)] for y in range(iy*110,iy*110+111,2)])
 g.static_surface('Terrain_ServiceFinal_%s_%s'%(ix,iy),0,v,f,'Terrain',True)
for name,r in p.ROADS.items():
 if r['kind'] not in('main','residential'):continue
 for side in(-1,1):
  old='Walk_'+name.replace(' ','_')+str(side);archive(old);v,f=[],[]
  for a,b in zip(r['points'],r['points'][1:]):
   if name=='Mill Road' and a[1]>=220:continue
   dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy);nx,ny=-dy/L,dx/L;off=side*(r['width']/2+.85);N=max(1,math.ceil(L/2));rows=[]
   for i in range(N+1):
    q=[p.mix(a[j],b[j],i/N) for j in range(3)];rows.append([(q[0]+nx*(off+o),q[1]+ny*(off+o),q[2]+.08) for o in(.75,-.75)])
   g.add_grid(v,f,rows)
  # Open actual curb breaks at crossing roads; no raised walkway across asphalt.
  others=[R for key,R in p.ROADS.items() if key!=name]
  def in_crossing(tri):
   return any(p.project(v[j][0],v[j][1],A,B)[0]<R['width']/2+.25 for R in others for A,B in zip(R['points'],R['points'][1:]) for j in tri)
  f=[tri for tri in f if not in_crossing(tri)]
  if f:g.static_surface(old+'_Final',1,v,f,'Path',True)
assert ue.EditorLoadingAndSavingUtils.save_map(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(),p.MAP)
p.export(Path(__file__).resolve().parents[1]/'Docs/V5/Penance_V5_Implementation.json')
print('V5_JUNCTIONS_FINISHED')
