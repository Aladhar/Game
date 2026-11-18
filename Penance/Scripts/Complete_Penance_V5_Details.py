import sys,json
from pathlib import Path
import unreal as ue
sys.path.insert(0,'/Users/amritladhar/Documents/GitHub/Game/Penance/Scripts')
import Penance_Town_V5_Design as p
assets=ue.get_editor_subsystem(ue.EditorAssetSubsystem);lev=ue.get_editor_subsystem(ue.LevelEditorSubsystem);api=ue.get_editor_subsystem(ue.EditorActorSubsystem);assert lev.load_level(p.MAP)
existing={a.get_actor_label() for a in api.get_all_level_actors()};cube=ue.load_asset('/Engine/BasicShapes/Cube');added=[]
def box(n,pos,dim,mat,yaw=0):
 label='V5_'+n
 if label in existing:return
 a=api.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(*p.uu(*pos)),ue.Rotator(yaw=yaw));a.set_actor_label(label);a.set_folder_path(ue.Name('V5/08_Props'));a.set_actor_scale3d(ue.Vector(*dim));c=a.get_component_by_class(ue.StaticMeshComponent);c.set_static_mesh(cube);c.set_material(0,assets.load_asset(p.GENERATED+'/Materials/M_V5_'+mat));c.set_collision_profile_name('BlockAll');added.append(dict(name=label,position_m=pos,dimensions_m=dim,yaw=yaw))
t=p.Terrain()
# Small settlement details with practical cover and recognizable functions.
box('Gas_Canopy',(100,64,8.6),(13,8,.35),'White',-25)
for x,y in[(96,61),(104,66)]:
 box('Gas_Pump_'+str(x),(x,y,t.surface(x,y)+.7),(.65,1,1.4),'Utility',-25)
 box('Gas_Post_'+str(x),(x+3,y+1,t.surface(x+3,y+1)+1.6),(.2,.2,3.2),'Metal')
for x in(313,323):box('Fire_Bay_'+str(x),(x,156.85,7.9),(6,.05,4),'Dark')
# Retaining walls run beside cut ground, away from road and driveway corridors.
for n,x,y,L,yaw in[('Briar',400,134,10,0),('Tower',39,229,8,90),('Ridge',230,337,14,-30)]:
 z=t.surface(x,y);box('Retaining_'+n,(x,y,z-.55),(L,.4,1.5),'Stone',yaw)
# Estate outbuildings and garden edges reserve later stealth branches.
box('Estate_CarriageHouse',(421,402,t.surface(421,402)+2.2),(12,9,4.4),'Estate')
box('Estate_CarriageRoof',(421,402,t.surface(421,402)+4.5),(13,10,.3),'Roof')
for x in(341,389):box('Estate_GardenHedge_'+str(x),(x,386,t.surface(x,386)+.8),(.8,12,1.6),'Woods')
# Low benches provide landmarks without barricading the park paths.
for x,y in[(108,230),(139,228),(242,181)]:box('Bench_'+str(x),(x,y,t.surface(x,y)+.4),(2,.6,.8),'Dark')
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();assert ue.EditorLoadingAndSavingUtils.save_map(world,p.MAP)
Path('/Users/amritladhar/Documents/GitHub/Game/Penance/Docs/V5/Additional_Placements.json').write_text(json.dumps(added,indent=2))
print('V5_DETAILS_SAVED',len(added))
