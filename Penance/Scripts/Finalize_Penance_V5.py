"""Final collision and readable-lighting corrections, only within V5."""
import sys
from pathlib import Path
import unreal as ue
sys.path.insert(0,str(Path(__file__).resolve().parent))
import Penance_Town_V5_Design as p
import Build_Penance_Town_V5 as g
assert g.level.load_level(p.MAP);t=p.Terrain();actors={a.get_actor_label():a for a in g.actor_api.get_all_level_actors()}
def archive(a):
 a.set_actor_enable_collision(False);a.set_actor_hidden_in_game(True);a.get_component_by_class(ue.StaticMeshComponent).set_visibility(False);a.set_folder_path(ue.Name('V5/99_Trash_Archive'))
for name,a in actors.items():
 if name.startswith(('V5_Terrain_','V5_Estate_Back_Path_Validated')):archive(a)
for ix in range(4):
 for iy in range(4):
  v,f=[],[];g.add_grid(v,f,[[(x,y,t.surface(x,y)) for x in range(ix*120,ix*120+121,2)] for y in range(iy*110,iy*110+111,2)])
  f=[tri for tri in f if not(172<=sum(v[j][0] for j in tri)/3<=198 and 350<=sum(v[j][1] for j in tri)/3<=404)]
  g.static_surface('Terrain_Final_%s_%s'%(ix,iy),0,v,f,'Terrain',True)
g.surface_ribbon('Estate_Back_Path_Final',1,p.PATHS['Estate back path'],2.6,'Path',t,.055,True)
g.obox('Escape_Landing_Joint',6,(177,401.9,9.9),(3,.6,.2),'Stone')
for a in actors.values():
 if a.get_actor_label().startswith('V5_Play_Swing_'):
  q=a.get_actor_location();q.y=21700;a.set_actor_location(q,False,False)
# Keep a lowland reveal route outside the estate wings, approaching from the west.
gate=actors['V5_Estate_Gate'];gate.set_actor_location(ue.Vector(*p.uu(334,367,t.surface(334,367)+1)),False,False)
for name,xy,target in p.VIEWS:
 if name in('ChurchApproach','FosterApproach'):
  a=actors['V5_Review_'+name];eye=ue.Vector(*p.uu(*xy,t.surface(*xy)+1.65));a.set_actor_location(eye,False,False);a.set_actor_rotation(ue.MathLibrary.find_look_at_rotation(eye,ue.Vector(*p.uu(*target))),False)
sky=actors['V5_SkyFill'].get_component_by_class(ue.SkyLightComponent);sky.set_editor_property('real_time_capture',True);sky.set_intensity(1.4);sky.recapture_sky()
for name,pitch,yaw,intensity in[('SouthFill',-40,90,2.5),('WestFill',-50,0,1.4)]:
 if 'V5_'+name not in actors:
  a=g.spawn(ue.DirectionalLight,name,0,(24000,22000,9000),ue.Rotator(pitch=pitch,yaw=yaw));c=a.get_component_by_class(ue.DirectionalLightComponent);c.set_intensity(intensity);c.set_editor_property('cast_shadows',False)
assert ue.EditorLoadingAndSavingUtils.save_map(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(),p.MAP)
p.export(Path(__file__).resolve().parents[1]/'Docs/V5/Penance_V5_Implementation.json')
print('V5_FINAL_SAVED')
