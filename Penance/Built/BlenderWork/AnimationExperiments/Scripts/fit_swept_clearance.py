"""Apply optimized skinning and fit the rear drape against old/new swept poses.
No hierarchy or reference changes. Tests actual triangle intersections and uses
one smooth rest-space flare, rather than concealing limb deformation with poses.
"""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');P=q['points'];B=list(q['names']);W=np.load(R/'Reports/OptimizedWeights.npz')['weights'];E=q['edges'];part=q['part'];rest=q['rest'];N=len(P);inv=np.linalg.inv(rest)
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');scene=bpy.context.scene
mesh.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in mesh.data.loop_triangles]);poly=np.array([t.polygon_index for t in mesh.data.loop_triangles]);owner=np.empty(len(mesh.data.polygons),np.int32);mesh.data.attributes['penance_part_owner'].data.foreach_get('value',owner);owner=owner[poly]
legmass=sum(W[:,i] for i,n in enumerate(B) if n.startswith(('thigh','calf','foot','ball')) or n=='pelvis');bodytri=tri[(owner==0)&np.all(((legmass>.65)&(P[:,2]>20)&(P[:,2]<125))[tri],axis=1)];trimtri=tri[(owner==1)&np.all(((P[:,2]>20)&(P[:,2]<145))[tri],axis=1)]
bodyids=np.unique(bodytri);trimids=np.unique(trimtri);bf=np.searchsorted(bodyids,bodytri);tf=np.searchsorted(trimids,trimtri);bfaces=bf.tolist();tfaces=tf.tolist()
def ease(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
flare=(part==1)*(1-ease(80,142,P[:,2]));delta=np.zeros_like(P);delta[:,1]=flare

def skin(points,m,ids):
 top=np.argsort(W[ids],axis=1)[:,-4:];values=np.take_along_axis(W[ids],top,axis=1);hom=np.column_stack((points[ids],np.ones(len(ids))));transform=np.einsum('bij,bjk->bik',m,inv,optimize=True)
 return np.einsum('nk,nkij,nj->ni',values,transform[top][:,:,:3,:],hom,optimize=True)
manifest=json.loads((R/'Reports/ClipManifest.json').read_text());clips=dict(manifest)
for n,f in [('AN_Penance_Idle',150),('AN_Penance_StalkWalk',60),('AN_Penance_Chase',30),('AN_Penance_Attack',45)]:clips[n]={'frames':f}
oldcheck=json.loads((R/'Reports/DeformationValidation.json').read_text());poses=[]
for name,s in clips.items():
 rig.animation_data.action=bpy.data.actions[name];frames=set(int(x) for x in np.rint(np.linspace(1,s['frames']+1,13)))
 for entry in oldcheck['clips'][name]['contacts_sampled']:
  if entry['body_trim_intersecting_triangle_pairs']>0:frames.add(entry['frame'])
 for f in sorted(frames):
  scene.frame_set(f);m=np.array([np.array(b.matrix) for b in rig.pose.bones]);bp=skin(P,m,bodyids);tp=skin(P,m,trimids);dp=skin(P+delta,m,trimids)-tp
  body=BVHTree.FromPolygons([Vector(v) for v in bp],bfaces,all_triangles=True);poses.append((name,f,body,tp,dp))
trials=[];selected=0;best=None
for extra in [0,6,12,18,24,30]:
 counts={};maxcount=0
 for name,f,body,tp,dp in poses:
  trim=BVHTree.FromPolygons([Vector(v) for v in tp+dp*extra],tfaces,all_triangles=True);count=len(body.overlap(trim));counts.setdefault(name,[]).append(count);maxcount=max(maxcount,count)
 entry={'additional_rear_flare_cm':extra,'max_intersecting_triangle_pairs':maxcount,'total_intersections':sum(sum(a) for a in counts.values()),'max_by_clip':{n:max(a) for n,a in counts.items()}};trials.append(entry);print('SWEPT_CLEARANCE_TRIAL',entry,flush=True)
 if best is None or entry['total_intersections']<best['total_intersections']:best=entry;selected=extra
 if maxcount==0:break
P+=delta*selected;mesh.data.vertices.foreach_set('co',P.astype(np.float32).ravel());mesh.data.update()
for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
groups=[mesh.vertex_groups.new(name=n) for n in B];quant=np.rint(W*100000).astype(np.int32);quant[np.arange(N),quant.argmax(axis=1)]+=100000-quant.sum(axis=1);W=quant/100000;unique,index=np.unique(quant,axis=0,return_inverse=True)
for k,row in enumerate(unique):
 vertices=np.flatnonzero(index==k).tolist()
 for j in np.flatnonzero(row):groups[j].add(vertices,float(row[j])/100000,'REPLACE')
np.savez_compressed(R/'Reports/ExperimentalMesh.npz',points=P,weights=W,names=B,edges=E,part=part,rest=rest)
report={'sampled_poses':len(poses),'trials':trials,'selected':best,'method':'Smooth rear flare anchored at Z142cm; actual body/trim triangles tested on original and experimental motions.','hierarchy_reference_body_geometry_UVs_unchanged':True}
(R/'Reports/SweptClearance.json').write_text(json.dumps(report,indent=2)+'\n');rig.animation_data.action=bpy.data.actions['AN_EXP_Stalk'];scene.frame_start=1;scene.frame_end=85;scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'Penance_AnimationExperiments.blend'),compress=True)
# Updated mesh; animation FBX files retain identical 31-bone transforms.
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(R/'FBX/SK_Penance_Experimental.fbx'),object_types={'ARMATURE','MESH'},use_selection=True,add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,path_mode='RELATIVE',bake_anim=False)
print('SWEPT_CLEARANCE_FIT_SAVED',selected,flush=True)
