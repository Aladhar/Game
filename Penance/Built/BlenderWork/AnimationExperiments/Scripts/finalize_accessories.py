"""Fit secondary chains to limb clearance, bake recovery endpoints and export."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
from math import radians
R=Path(__file__).resolve().parents[1];scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH');q=np.load(R/'Reports/ExperimentalMesh.npz');P=q['points'];W=q['weights'];B=list(q['names']);rest=q['rest'];N=len(P)
manifest=json.loads((R/'Reports/ClipManifest.json').read_text());mesh.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in mesh.data.loop_triangles]);poly=np.array([t.polygon_index for t in mesh.data.loop_triangles]);owner=np.empty(len(mesh.data.polygons),np.int32);mesh.data.attributes['penance_part_owner'].data.foreach_get('value',owner);owner=owner[poly]
legmass=sum(W[:,i] for i,n in enumerate(B) if n.startswith(('thigh','calf','foot','ball')) or n=='pelvis');bodytri=tri[(owner==0)&np.all(((legmass>.65)&(P[:,2]>20)&(P[:,2]<125))[tri],axis=1)];trimtri=tri[(owner==1)&np.all(((P[:,2]>20)&(P[:,2]<145))[tri],axis=1)]
_,geo=np.unique(np.rint(P*10000).astype(np.int64),axis=0,return_inverse=True)
def points():
 bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());p=np.empty(P.size,np.float32);ev.data.vertices.foreach_get('co',p);return p.reshape(-1,3)
def contacts(p):
 v=[Vector(x) for x in p];a=BVHTree.FromPolygons(v,bodytri.tolist(),all_triangles=True);b=BVHTree.FromPolygons(v,trimtri.tolist(),all_triangles=True);count=0
 for i,j in a.overlap(b):
  aa,bb=bodytri[i],trimtri[j];common=set(geo[aa])&set(geo[bb]);touch=False
  for k in common:
   x=aa[geo[aa]==k];y=bb[geo[bb]==k]
   if np.min(np.linalg.norm(p[x,None,:]-p[y][None,:,:],axis=-1))<.05:touch=True
  if not touch:count+=1
 return count
report={}
for name in ['AN_EXP_Stalk','AN_EXP_Heavy']:
 spec=manifest[name];rig.animation_data.action=bpy.data.actions[name];base={}
 for f in range(1,spec['frames']+2):
  scene.frame_set(f);base[f]={n:rig.pose.bones[n].rotation_quaternion.copy() for n in ['ornament_01_l','ornament_01_r']}
 frames=sorted(set(np.rint(np.linspace(1,spec['frames']+1,17)).astype(int)));trials=[]
 for extra in [0,3,6,9,12]:
  counts=[]
  for f in frames:
   scene.frame_set(int(f))
   for side,sign in [('l',-1),('r',1)]:
    n='ornament_01_'+side;axis=rig.data.bones[n].matrix_local.to_quaternion().inverted()@Vector((0,1,0));rig.pose.bones[n].rotation_quaternion=Quaternion(axis,radians(sign*extra))@base[f][n]
   counts.append(contacts(points()))
  trial={'additional_outward_degrees':extra,'maximum_contacts':max(counts),'total_contacts':sum(counts)};trials.append(trial);print('ACCESSORY_TRIAL',name,trial,flush=True)
  if max(counts)==0:break
 best=min(trials,key=lambda t:(t['total_contacts'],t['additional_outward_degrees']));extra=best['additional_outward_degrees']
 for f in range(1,spec['frames']+2):
  scene.frame_set(f)
  for side,sign in [('l',-1),('r',1)]:
   n='ornament_01_'+side;b=rig.pose.bones[n];axis=rig.data.bones[n].matrix_local.to_quaternion().inverted()@Vector((0,1,0));b.rotation_quaternion=Quaternion(axis,radians(sign*extra))@base[f][n];b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 report[name]={'trials':trials,'selected':best,'collision_test_frames':[int(f) for f in frames]}
# Make the final recovery pose exactly match the first ready pose, retaining
# the authored anticipation, impact and follow-through throughout each attack.
for name,s in manifest.items():
 if s['loop']:continue
 rig.animation_data.action=bpy.data.actions[name];scene.frame_set(1);first={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in rig.pose.bones}
 scene.frame_set(s['frames']+1)
 for b in rig.pose.bones:
  b.rotation_quaternion=first[b.name][0];b.keyframe_insert('rotation_quaternion',frame=s['frames']+1,group=b.name)
  if b.name=='pelvis':b.location=first[b.name][1];b.keyframe_insert('location',frame=s['frames']+1,group=b.name)
for name,s in manifest.items():
 rig.animation_data.action=bpy.data.actions[name];m=[]
 for f in range(1,s['frames']+2):scene.frame_set(f);m.append(np.array([np.array(b.matrix) for b in rig.pose.bones]))
 np.savez_compressed(R/'Reports'/(name+'_poses.npz'),matrices=np.array(m),names=B)
rig.animation_data.action=bpy.data.actions['AN_EXP_Stalk'];scene.frame_start=1;scene.frame_end=85;scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'Penance_AnimationExperiments.blend'),compress=True)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
opts=dict(use_selection=True,add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,path_mode='RELATIVE')
bpy.ops.export_scene.fbx(filepath=str(R/'FBX/SK_Penance_Experimental.fbx'),object_types={'ARMATURE','MESH'},bake_anim=False,**opts);mesh.select_set(False)
for name,s in manifest.items():
 rig.animation_data.action=bpy.data.actions[name];scene.frame_start=1;scene.frame_end=s['frames']+1;scene.frame_set(1)
 bpy.ops.export_scene.fbx(filepath=str(R/'FBX'/(name+'.fbx')),object_types={'ARMATURE'},bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0.,**opts)
(R/'Reports/AccessoryRefinement.json').write_text(json.dumps(report,indent=2)+'\n');print('ACCESSORY_FINALIZATION_COMPLETE',flush=True)
