"""Allow queries on both sides of generated thin environment surfaces."""
import unreal as ue
assets=ue.get_editor_subsystem(ue.EditorAssetSubsystem)
count=0
for path in assets.list_assets('/Game/Environment/V5/Meshes',recursive=True,include_folder=False):
 mesh=assets.load_asset(path)
 if not isinstance(mesh,ue.StaticMesh):continue
 body=mesh.get_editor_property('body_setup')
 if body:
  body.set_editor_property('double_sided_geometry',True)
  assert assets.save_loaded_asset(mesh,False)
  count+=1
print('V5_TWO_SIDED_COLLISION_SAVED',count)
