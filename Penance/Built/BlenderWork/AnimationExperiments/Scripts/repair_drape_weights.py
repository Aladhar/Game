"""Repair the original sharp left/right ornament split and use both chain segments."""
import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');P=q['points'];W=q['weights'];B=list(q['names']);part=q['part'];old=W.copy();N=len(P)
def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
left=smooth(-14,14,P[:,0]);lower=1-smooth(69,97,P[:,2]);amount=(part==1).astype(float);attach=1-smooth(112,162,P[:,2]);model=np.zeros_like(W)
model[:,B.index('shrine_mount')]=1-attach
for side,mass in [('l',left),('r',1-left)]:
 model[:,B.index('ornament_01_'+side)]=attach*mass*(1-lower);model[:,B.index('ornament_02_'+side)]=attach*mass*lower
W=W*(1-amount[:,None])+model*amount[:,None];top=np.argsort(W,axis=1)[:,-4:];out=np.zeros_like(W);np.put_along_axis(out,top,np.take_along_axis(W,top,axis=1),axis=1);out[out<.00001]=0;out/=out.sum(axis=1,keepdims=True);quant=np.rint(out*100000).astype(np.int32);quant[np.arange(N),quant.argmax(axis=1)]+=100000-quant.sum(axis=1);W=quant/100000
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
groups=[mesh.vertex_groups.new(name=n) for n in B];unique,index=np.unique(quant,axis=0,return_inverse=True)
for k,row in enumerate(unique):
 ids=np.flatnonzero(index==k).tolist()
 for j in np.flatnonzero(row):groups[j].add(ids,float(row[j])/100000,'REPLACE')
np.savez_compressed(R/'Reports/ExperimentalMesh.npz',points=P,weights=W,names=B,edges=q['edges'],part=part,rest=q['rest'])
report={'changed_vertices':int(np.sum(np.max(abs(W-old),axis=1)>1e-5)),'left_right_blend_width_cm':28,'lower_segment_blend_z_cm':[69,97],'shrine_attachment_blend_z_cm':[112,162],'maximum_influences':int(np.max(np.sum(W>0,axis=1))),'geometry_changed':False,'reason':'Connected drape triangles were assigned rigidly to opposing chains at X=0, producing 27x edge stretch. Continuous cross-panel and two-segment weights remove the discontinuity.'}
(R/'Reports/DrapeWeightRepair.json').write_text(json.dumps(report,indent=2)+'\n');rig.animation_data.action=bpy.data.actions['AN_EXP_Stalk'];bpy.context.scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'Penance_AnimationExperiments.blend'),compress=True)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(R/'FBX/SK_Penance_Experimental.fbx'),object_types={'ARMATURE','MESH'},use_selection=True,add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,path_mode='RELATIVE',bake_anim=False)
print('DRAPE_WEIGHT_REPAIR_COMPLETE',json.dumps(report),flush=True)
