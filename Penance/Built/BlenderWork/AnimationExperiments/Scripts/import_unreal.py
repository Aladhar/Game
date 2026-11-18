"""Import only isolated experiments; verify native animation data in UE 5.7.4."""
import unreal as u,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];F='/Game/Enemies/Penance/Experimental'
A=u.get_editor_subsystem(u.EditorAssetSubsystem);T=u.AssetToolsHelpers.get_asset_tools();world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(world,'Interchange.FeatureFlags.Import.SyncToBrowser 0')
assert '5.7.4' in u.SystemLibrary.get_engine_version(),u.SystemLibrary.get_engine_version()
skel=A.load_asset('/Game/Enemies/Penance/SKEL_Penance');physics=A.load_asset('/Game/Enemies/Penance/PHYS_Penance');mat=A.load_asset('/Game/Enemies/Penance/Materials/M_Penance')
def reference():
 p=u.AnimPoseExtensions.get_reference_pose(skel)
 def serial(t):return list(t.translation.to_tuple())+list(t.rotation.to_tuple())+list(t.scale3d.to_tuple())
 return {str(n):serial(u.AnimPoseExtensions.get_bone_pose(p,n,u.AnimPoseSpaces.LOCAL)) for n in u.AnimPoseExtensions.get_bone_names(p)}
before=reference();assert len(before)==31

def options(is_mesh):
 op=u.FbxImportUI();op.set_editor_properties({'automated_import_should_detect_type':False,'mesh_type_to_import':u.FBXImportType.FBXIT_SKELETAL_MESH if is_mesh else u.FBXImportType.FBXIT_ANIMATION,'import_mesh':is_mesh,'import_animations':not is_mesh,'import_as_skeletal':True,'import_materials':False,'import_textures':False,'skeleton':skel,'create_physics_asset':False})
 data=op.get_editor_property('skeletal_mesh_import_data' if is_mesh else 'anim_sequence_import_data')
 props={'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':True,'import_uniform_scale':1.,'import_rotation':u.Rotator() if is_mesh else u.Rotator(pitch=0,yaw=-90,roll=0)}
 if is_mesh:props.update({'update_skeleton_reference_pose':False,'use_t0_as_ref_pose':False,'normal_import_method':u.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS})
 else:props.update({'use_default_sample_rate':False,'custom_sample_rate':30})
 data.set_editor_properties(props);return op

def import_one(name,folder,is_mesh):
 task=u.AssetImportTask();task.set_editor_properties({'filename':str(R/'FBX'/(name+'.fbx')),'destination_path':folder,'destination_name':name,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':False,'options':options(is_mesh),'factory':u.FbxFactory()});T.import_asset_tasks([task]);obj=A.load_asset(folder+'/'+name);assert obj,(name,'Import missing');return obj
mesh=import_one('SK_Penance_Experimental',F,True)
assert mesh.get_editor_property('skeleton')==skel
mesh.set_editor_property('physics_asset',physics)
assert u.PenancePlayerAssetLibrary.assign_skeletal_mesh_material(mesh,0,mat)
assert abs(mesh.get_imported_bounds().box_extent.z*2-230)<.01
assert u.SkeletalMeshEditorSubsystem.is_physics_asset_compatible(mesh,physics)
assert A.save_loaded_asset(mesh,False)
manifest=json.loads((R/'Reports/ClipManifest.json').read_text());report={'engine':u.SystemLibrary.get_engine_version(),'mesh_height_cm':mesh.get_imported_bounds().box_extent.z*2,'mesh':mesh.get_path_name(),'clips':{}}
for name,s in manifest.items():
 clip=import_one(name,F+'/Animations',False);assert isinstance(clip,u.AnimSequence);assert clip.get_editor_property('skeleton')==skel
 clip.set_editor_property('enable_root_motion',False);clip.set_editor_property('compression_error_threshold_scale',.1)
 assert abs(clip.get_play_length()-s['frames']/30)<.001
 A.set_metadata_tag(clip,'Penance.Experimental','true');A.set_metadata_tag(clip,'Penance.IntendedSpeedCmS',str(s['speed']));A.set_metadata_tag(clip,'Penance.Loop',str(s['loop']))
 if 'impact' in s:
  A.set_metadata_tag(clip,'Penance.ImpactSeconds',str((s['impact']-1)/30));A.set_metadata_tag(clip,'Penance.BlenderImpactFrame',str(s['impact']))
 samples=[];names=None;opt=u.AnimPoseEvaluationOptions()
 for frame in range(s['frames']+1):
  p=u.AnimPoseExtensions.get_anim_pose_at_time(clip,frame/30,opt);names=list(map(str,u.AnimPoseExtensions.get_bone_names(p)));values=[]
  for n in names:
   t=u.AnimPoseExtensions.get_bone_pose(p,n,u.AnimPoseSpaces.LOCAL);values.append(list(t.translation.to_tuple())+list(t.rotation.to_tuple())+list(t.scale3d.to_tuple()))
  samples.append(values)
 i=names.index('root');rootdev=max(abs(a-b) for row in samples for a,b in zip(row[i],before['root']));looperr=max(abs(a-b) for first,last in zip(samples[0],samples[-1]) for a,b in zip(first,last))
 assert len(names)==31 and rootdev<.001,(name,'Bad skeleton/root',len(names),rootdev)
 if s['loop']:assert looperr<.002,(name,'Loop seam',looperr)
 assert max(abs(a-b) for row in samples for first,last in zip(samples[0],row) for a,b in zip(first,last))>.001
 assert A.save_loaded_asset(clip,False)
 report['clips'][name]={'duration_seconds':clip.get_play_length(),'samples_evaluated':len(samples),'bone_count':len(names),'root_deviation':rootdev,'endpoint_error':looperr,'root_motion':False,'import_sample_rate':30,'skeleton':skel.get_path_name()}
 print('EXPERIMENT_UNREAL_IMPORTED',name,report['clips'][name])
after=reference();assert set(before)==set(after) and max(abs(a-b) for n in before for a,b in zip(before[n],after[n]))<.0001
report['skeleton_reference_unchanged']=True
(R/'Reports/UnrealImportValidation.json').write_text(json.dumps(report,indent=2)+'\n')
print('EXPERIMENT_UNREAL_IMPORT_COMPLETE')
