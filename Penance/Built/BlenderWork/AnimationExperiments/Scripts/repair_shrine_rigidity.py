"""Restore the canonical straight shrine and give it one rigid influence.
Leaves all 11 editable Actions, body skinning, skeleton and reference pose intact.
"""
import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');src=np.load(R/'Reports/SourceMesh.npz');P=q['points'].copy();W=q['weights'].copy();B=list(q['names']);part=q['part'];region=part==1
fit=json.loads((R/'Reports/RigidShrineMountTrials.json').read_text());chosen=fit['selected'];offset=float(chosen['rigid_backward_offset_cm']);placement=np.array(chosen.get('canonical_placement_matrix',np.eye(4)))
if 'canonical_placement_matrix' not in chosen:placement[1,3]=offset
if chosen['maximum_contacts']!=0:raise RuntimeError('No collision-free rigid placement found; review the fit instead of deforming the shrine.')
# Canonical source coordinates are authoritative. A single rigid placement
# transform preserves all internal distances, angles and cross sections.
P[region]=np.column_stack((src['points'][region],np.ones(region.sum())))@placement[:3,:].T;W[region]=0;W[region,B.index('shrine_mount')]=1
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');
mesh.data.vertices.foreach_set('co',P.astype(np.float32).ravel());mesh.data.update()
ids=np.flatnonzero(region).tolist()
for group in mesh.vertex_groups:group.remove(ids)
mesh.vertex_groups['shrine_mount'].add(ids,1.,'REPLACE')
# Mark the rigid architectural region explicitly; future solvers must exclude it.
attr=mesh.data.attributes.get('penance_rigid_shrine') or mesh.data.attributes.new('penance_rigid_shrine','BOOLEAN','POINT');attr.data.foreach_set('value',region)
rig['penance_shrine_contract']='Canonical straight geometry; shrine_mount only; no flexible chain influences.'
mesh['penance_shrine_rigid_offset_cm']=offset
np.savez_compressed(R/'Reports/ExperimentalMesh.npz',points=P,weights=W,names=B,edges=q['edges'],part=part,rest=q['rest'])
report={'rigid_vertices':int(region.sum()),'canonical_source':'Reports/SourceMesh.npz from original Penance_Animated.blend','rigid_backward_mount_placement_cm':offset,'rigid_pitch_degrees':chosen.get('rigid_pitch_degrees',0),'canonical_placement_matrix':placement.tolist(),'vertex_weight':{'shrine_mount':1.},'hierarchy_reference_pose_changed':False,'actions_changed':False,'body_skinning_changed':False,'shape_deformation_allowed':False,'rigid_shape_contract':'Every shrine vertex must equal shrine_mount rigid transform applied to canonical geometry after the single rigid placement transform.'}
(R/'Reports/StraightShrineRepair.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'Penance_AnimationExperiments.blend'),compress=True)
rig.animation_data.action=None
for bone in rig.pose.bones:bone.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(R/'FBX/SK_Penance_Experimental.fbx'),object_types={'ARMATURE','MESH'},use_selection=True,add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,path_mode='RELATIVE',bake_anim=False)
print('STRAIGHT_SHRINE_REPAIR_SAVED',json.dumps(report),flush=True)
