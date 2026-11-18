"""Remove H01 fence ends that project into the public road; keep them archived."""
import unreal as ue
lev=ue.get_editor_subsystem(ue.LevelEditorSubsystem);api=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert lev.load_level('/Game/Maps/V5/Penance_Town_V5')
for a in api.get_all_level_actors():
 if a.get_actor_label() in('V5_H01_SideFence','V5_H01_GardenFence'):
  a.set_actor_enable_collision(False);a.set_actor_hidden_in_game(True);a.get_component_by_class(ue.StaticMeshComponent).set_visibility(False);a.set_folder_path(ue.Name('V5/99_Trash_Archive'))
assert ue.EditorLoadingAndSavingUtils.save_map(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(),'/Game/Maps/V5/Penance_Town_V5')
print('V5_HOUSE01_ROAD_ACCESS_CLEAR')
