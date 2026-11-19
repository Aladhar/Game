"""Evaluate the actual skinned mesh for all 740 old/new animation samples.
A rigid shrine must remain the canonical straight shape in shrine_mount space.
Also confirms all original poses, approved Limp gait, body geometry and weights.
"""
import bpy,json,numpy as np,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');src=np.load(R/'Reports/SourceMesh.npz');previous=np.load(R/'Checkpoints/BeforeStraightShrine/ExperimentalMesh.npz');P=q['points'];W=q['weights'];part=q['part'];names=list(q['names']);region=part==1;offset=json.loads((R/'Reports/StraightShrineRepair.json').read_text())['rigid_backward_mount_placement_cm'];placement=np.array(json.loads((R/'Reports/StraightShrineRepair.json').read_text())['canonical_placement_matrix']);target=np.column_stack((src['points'][region],np.ones(region.sum())))@placement[:3,:].T;mount=names.index('shrine_mount');rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');scene=bpy.context.scene
assert np.max(abs(P[region]-target))<.00005
assert np.array_equal(P[~region],previous['points'][~region]),'Non-shrine geometry changed'
assert np.array_equal(W[~region],previous['weights'][~region]),'Body skinning changed'
assert np.all(W[region,mount]==1.) and np.count_nonzero(W[region])==region.sum(),'Shrine has non-rigid influences'
assert np.max(abs(W.sum(axis=1)-1))<1e-6
reference=rig.data.bones['shrine_mount'].matrix_local.copy();ref=np.array(reference);invref=np.linalg.inv(ref);report={'canonical_straight_shape':True,'rigid_vertices':int(region.sum()),'rigid_backward_mount_placement_cm':offset,'canonical_placement_matrix':placement.tolist(),'body_geometry_weights_unchanged':True,'clips':{}}
for action in bpy.data.actions:
 if not action.name.startswith(('AN_EXP_','AN_Penance_')):continue
 old=np.load(R/'Diagnostics/ShrineDeformation'/(action.name+'_Evaluated.npz'));oldnames=list(old['names']);oldmat=old['matrices'][:,[oldnames.index(n) for n in names]];rig.animation_data.action=action;start,end=map(round,action.frame_range);maximum=0.;pose_error=0.;edgeerror=0.;samples=[]
 for i,f in enumerate(range(start,end+1)):
  scene.frame_set(f);bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());points=np.empty(P.size,np.float32);ev.data.vertices.foreach_get('co',points);points=points.reshape(-1,3);skin=np.array(rig.pose.bones['shrine_mount'].matrix)@invref;back=np.linalg.inv(skin);hom=np.column_stack((points[region],np.ones(region.sum())));local=hom@back[:3,:].T;error=float(np.linalg.norm(local-target,axis=1).max());maximum=max(maximum,error)
  current=np.array([np.array(rig.pose.bones[n].matrix) for n in names]);pose_error=max(pose_error,float(np.max(abs(current-oldmat[i]))));samples.append(error)
 assert maximum<.001,(action.name,'Shrine deforms',maximum)
 assert pose_error<.0001,(action.name,'Animation pose changed',pose_error)
 report['clips'][action.name]={'frames_evaluated':end-start+1,'max_shrine_shape_error_cm':maximum,'max_bone_matrix_difference_from_approved_actions':pose_error,'per_frame_shape_error_cm':samples}
 print('RIGID_SHRINE_CLIP_PASSED',action.name,report['clips'][action.name]['frames_evaluated'],maximum,pose_error,flush=True)
report['total_samples']=sum(v['frames_evaluated'] for v in report['clips'].values());report['maximum_shrine_shape_error_cm']=max(v['max_shrine_shape_error_cm'] for v in report['clips'].values());assert report['total_samples']==740
manifest=json.loads((R/'Checkpoints/BeforeStraightShrine/Manifest.json').read_text());project=R.parents[2]
for f,h in manifest['unchanged_animation_files'].items():assert hashlib.sha256((project/f).read_bytes()).hexdigest()==h,(f,'Saved animation changed')
report['all_14_animation_fbx_and_unreal_files_byte_unchanged']=True
(R/'Reports/StraightShrineRigidityValidation.json').write_text(json.dumps(report,indent=2)+'\n');print('STRAIGHT_SHRINE_ALL_CLIPS_PASSED',report['total_samples'],report['maximum_shrine_shape_error_cm'],flush=True)
