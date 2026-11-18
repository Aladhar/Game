"""Reviewed local fixes after fresh PIE collision validation."""
from pathlib import Path
import sys,json
import unreal as ue
sys.path.insert(0,str(Path(__file__).resolve().parent))
import Penance_Town_V5_Design as p
import Build_Penance_Town_V5 as g
assert g.level.load_level(p.MAP)
actors={a.get_actor_label():a for a in g.actor_api.get_all_level_actors()};t=p.Terrain()
def archive(name):
 a=actors.get('V5_'+name)
 if a:
  a.set_actor_enable_collision(False);a.set_actor_hidden_in_game(True);a.get_component_by_class(ue.StaticMeshComponent).set_visibility(False);a.set_folder_path(ue.Name('V5/99_Trash_Archive'))
# New mesh names retain the old saved geometry for review; only corrected actors collide.
for ix,iy in[(3,1),(3,2)]:
 archive('Terrain_%s_%s'%(ix,iy));v,f=[],[]
 g.add_grid(v,f,[[(x,y,t.surface(x,y)) for x in range(ix*120,ix*120+121,2)] for y in range(iy*110,iy*110+111,2)])
 g.static_surface('Terrain_Validated_%s_%s'%(ix,iy),0,v,f,'Terrain',True)
archive('Road_Grave_Lane');r=p.ROADS['Grave Lane'];g.road_surface('Road_Grave_Lane_Validated',r['points'],r['width'],r['kind'])
archive('Drive_H14');b=p.BUILDING_BY_ID['H14'];pts=p.DRIVES['H14'];g.road_surface('Drive_H14_Validated',[(*pt,5.42) for pt in pts],3.2,'Path',3)
archive('Path_Estate_back_path');g.surface_ribbon('Estate_Back_Path_Validated',1,p.PATHS['Estate back path'],2.6,'Path',t,.055,True)
# Keep all cemetery markers above the refitted ground, away from the service road.
for name,a in actors.items():
 if name.startswith(('V5_Grave_','V5_GraveyardWall_')):
  q=a.get_actor_location();q.z=(t.surface(q.x/100,q.y/100)+(.45 if name.startswith('V5_Grave_') else .6))*100;a.set_actor_location(q,False,False)
square=actors['V5_CivicSquare'];square.set_actor_location(ue.Vector(26000,18000,488),False,False);square.set_actor_scale3d(ue.Vector(30,7,.15))
cover=actors['V5_Basement_Cover_181_385'];cover.set_actor_location(ue.Vector(18100,38000,605),False,False)
gate=actors['V5_Estate_Gate'];gate.set_actor_location(ue.Vector(*p.uu(332,367,t.surface(332,367)+1)),False,False);gate.set_actor_scale3d(ue.Vector(6,.25,2))
director=actors['V5_Opening_Director'];director.set_editor_property('chase_path',[ue.Vector(*p.uu(*q)) for q in[(193,367,5.32),(193,376,5.32),(193,386,5.32),(179,388,5.32)]])
assert ue.EditorLoadingAndSavingUtils.save_map(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(),p.MAP)
p.export(Path(__file__).resolve().parents[1]/'Docs/V5/Penance_V5_Implementation.json')
print('V5_LOCAL_ROUTES_SAVED')
