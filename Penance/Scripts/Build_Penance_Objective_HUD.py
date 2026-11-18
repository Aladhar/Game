"""Create the actual UMG Blueprint/input assets and place V5 objective volumes."""
from pathlib import Path
import json
import unreal as u
A=u.get_editor_subsystem(u.EditorAssetSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.get_editor_subsystem(u.EditorActorSubsystem);T=u.AssetToolsHelpers.get_asset_tools()
report={'assets':[],'maps':{},'spawn_fixes':[]}
path='/Game/UI/WBP_ObjectiveTracker'
if not A.does_asset_exist(path):
 factory=u.WidgetBlueprintFactory();factory.set_editor_property('parent_class',u.PenanceObjectiveTrackerWidget.static_class())
 widget=T.create_asset('WBP_ObjectiveTracker','/Game/UI',u.WidgetBlueprint,factory)
 assert widget and u.PenanceObjectiveEditorLibrary.build_tracker_blueprint(widget),'Could not construct the UMG designer tree'
else:widget=A.load_asset(path)
u.BlueprintEditorLibrary.compile_blueprint(widget);assert A.save_loaded_asset(widget,False);report['assets'].append(widget.get_path_name())
def data(name,cls):
 path='/Game/UI/Input/'+name
 if A.does_asset_exist(path):return A.load_asset(path)
 fac=u.DataAssetFactory();fac.set_editor_property('data_asset_class',cls);return T.create_asset(name,'/Game/UI/Input',cls,fac)
action=data('IA_ToggleObjectives',u.InputAction);action.set_editor_property('value_type',u.InputActionValueType.BOOLEAN)
context=data('IMC_Objectives',u.InputMappingContext)
if not context.get_editor_property('default_key_mappings').get_editor_property('mappings'):
 key=u.Key();key.set_editor_property('key_name',u.Name('O'));context.map_key(action,key)
for obj in(action,context):assert A.save_loaded_asset(obj,False);report['assets'].append(obj.get_path_name())
assert u.PenanceObjectiveEditorLibrary.configure_player_play_settings()
for map in('/Game/Maps/Penance_Persistent','/Game/Maps/V5/Penance_Town_V5'):
 assert L.load_level(map)
 world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world();ws=world.get_world_settings();mode=ws.get_editor_property('default_game_mode') or u.load_class(None,'/Script/PenanceDemoUE.PenanceDemoGameMode')
 report['maps'][map]={'game_mode':mode.get_path_name(),'default_pawn':u.get_default_object(mode).get_editor_property('default_pawn_class').get_path_name(),'player_starts':sum(isinstance(a,u.PlayerStart) for a in E.get_all_level_actors()),'camera_auto_activation':{a.get_actor_label():str(a.get_auto_activate_player_index()) for a in E.get_all_level_actors() if isinstance(a,u.CameraActor)}}
 if map.endswith('Penance_Town_V5'):
  ws.set_editor_property('default_game_mode',u.load_class(None,'/Script/PenanceDemoUE.PenanceDemoGameMode'))
  names={a.get_actor_label() for a in E.get_all_level_actors()}
  for name,id,optional,xyz,extent in[
   ('V5_Objective_HousePorch','Ch01.House.Porch',False,(10100,11800,580),(170,240,180)),
   ('V5_Objective_GasForecourt','Ch01.Gas.Search',True,(10000,6400,560),(650,650,200))]:
   if name not in names:
    actor=E.spawn_actor_from_class(u.PenanceObjectiveTrigger,u.Vector(*xyz));actor.set_actor_label(name);actor.set_folder_path(u.Name('V5/09_Story/Objectives'));actor.set_editor_properties({'objective_id':u.Name(id),'optional':optional});actor.get_editor_property('bounds').set_box_extent(u.Vector(*extent),True)
  assert u.EditorLoadingAndSavingUtils.save_map(world,map)
root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()));(root/'Docs/ObjectiveHUD/Asset_Setup.json').write_text(json.dumps(report,indent=2)+'\n');print('PENANCE_OBJECTIVE_HUD_SAVED',json.dumps(report))
