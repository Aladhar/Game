"""Run in full Unreal Editor before PIE; StaticMeshEditorSubsystem is GUI-only."""
import unreal as u,json
from pathlib import Path
import Penance_Town_V6_Design as p
def apply():
 assets=u.get_editor_subsystem(u.EditorAssetSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem);api=u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
 assert api,'Foliage LOD creation requires the full editor'
 report={}
 for short,src in [('Canopy','Sphere'),('Trunk','Cylinder'),('Pine','Cone')]:
  path=p.GENERATED+'/Foliage/SM_V6_'+short;asset=assets.load_asset(path) if assets.does_asset_exist(path) else assets.duplicate_asset('/Engine/BasicShapes/'+src,path)
  if api.get_lod_count(asset)<3:
   options=u.StaticMeshReductionOptions();settings=[]
   for percent,screen in[(1,1),(.45,.35),(.16,.12)]:
    s=u.StaticMeshReductionSettings();s.percent_triangles=percent;s.screen_size=screen;settings.append(s)
   options.reduction_settings=settings;options.auto_compute_lod_screen_size=False;api.set_lods(asset,options)
  assert assets.save_loaded_asset(asset,False);report[short]=api.get_lod_count(asset)
  for a in A.get_all_level_actors():
   if '99_' in str(a.get_folder_path()):continue
   c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
   if c and c.static_mesh and c.static_mesh.get_name()==src:c.set_static_mesh(asset)
 out=Path(__file__).resolve().parents[1]/'Docs/V6';(out/'Foliage_LODs.json').write_text(json.dumps(report,indent=2)+'\n')
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();assert u.EditorLoadingAndSavingUtils.save_map(world,p.MAP)
