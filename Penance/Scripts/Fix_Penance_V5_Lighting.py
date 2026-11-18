"""Repair V5 lighting through Unreal Python/editor APIs; safe in the live editor
or via UnrealEditor -run=pythonscript -script=<absolute path>.
V5 uses dynamic lighting; other levels keep their existing bake configuration.
"""
from pathlib import Path
import hashlib,json,shutil
import unreal as u
MAP='/Game/Maps/V5/Penance_Town_V5'
L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.UnrealEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
world=E.get_editor_world()
if not world or world.get_path_name().split('.')[0]!=MAP:
 assert L.load_level(MAP);world=E.get_editor_world()
root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));out=root/'Docs/Lighting';out.mkdir(parents=True,exist_ok=True)
backup=root/'Built/Checkpoints/BeforeV5LightingFix';backup.mkdir(parents=True,exist_ok=True)
file=root/'Content/Maps/V5/Penance_Town_V5.umap'
if not (backup/'Penance_Town_V5_OnDisk.umap').exists():shutil.copy2(file,backup/'Penance_Town_V5_OnDisk.umap')
# Preserve the complete live world, including any edits made since opening it.
assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
if not (backup/'Penance_Town_V5_LiveBeforeFix.umap').exists():shutil.copy2(file,backup/'Penance_Town_V5_LiveBeforeFix.umap')
def transforms():
 return {a.get_path_name():{'location':list(a.get_actor_location().to_tuple()),'rotation':list(a.get_actor_rotation().to_tuple()),'scale':list(a.get_actor_scale3d().to_tuple())} for a in A.get_all_level_actors()}
before=transforms();settings=world.get_world_settings();lights=[]
for actor in A.get_all_level_actors():
 for c in actor.get_components_by_class(u.LightComponentBase):
  record={'actor':actor.get_actor_label(),'component':c.get_name(),'mobility_before':str(c.get_editor_property('mobility'))}
  c.set_mobility(u.ComponentMobility.MOVABLE)
  if isinstance(c,u.DirectionalLightComponent):
   main=actor.get_actor_label()=='V5_Afternoon_Light'
   record['priority_before']=c.get_editor_property('forward_shading_priority')
   c.set_forward_shading_priority(2 if main else 0)
   c.set_atmosphere_sun_light(main)
   if main:c.set_atmosphere_sun_light_index(0)
   record['priority_after']=c.get_editor_property('forward_shading_priority');record['atmosphere_sun']=main
  record['mobility_after']=str(c.get_editor_property('mobility'));lights.append(record)
settings.set_editor_property('force_no_precomputed_lighting',True)
assert len([r for r in lights if r.get('priority_after')==2])==1,'Expected exactly one priority sun'
assert transforms()==before,'Lighting repair unexpectedly moved actors'
assert u.EditorLoadingAndSavingUtils.save_map(world,MAP)
report={'map':MAP,'lighting_mode':'dynamic / movable','force_no_precomputed_lighting':True,'lights':lights,'actor_transforms_preserved':True,'actor_count':len(before),'map_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'backup':str(backup),'static_lightmass_bake_performed':False}
(out/'V5_Lighting_Repair.json').write_text(json.dumps(report,indent=2)+'\n')
u.SystemLibrary.execute_console_command(world,'EnableAllScreenMessages')
u.SystemLibrary.execute_console_command(world,'DumpUnbuiltLightInteractions')
u.SystemLibrary.execute_console_command(world,'MAP CHECK DONTDISPLAYDIALOG')
print('PENANCE_V5_LIGHTING_REPAIRED',json.dumps(report))
