"""Read-only collision fit for a straight, single-transform shrine.
Tests rigid translations only; never warps geometry or edits gait keyframes.
"""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');source=np.load(R/'Reports/SourceMesh.npz');P=q['points'].copy();part=q['part'];P[part==1]=source['points'][part==1];W=q['weights'];B=list(q['names']);rest=q['rest'];inv=np.linalg.inv(rest);mount=B.index('shrine_mount')
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in mesh.data.loop_triangles]);poly=np.array([t.polygon_index for t in mesh.data.loop_triangles]);owner=np.empty(len(mesh.data.polygons),np.int32);mesh.data.attributes['penance_part_owner'].data.foreach_get('value',owner);owner=owner[poly]
legmass=sum(W[:,i] for i,n in enumerate(B) if n.startswith(('thigh','calf','foot','ball')) or n=='pelvis');bodytri=tri[(owner==0)&np.all(((legmass>.65)&(P[:,2]>20)&(P[:,2]<125))[tri],axis=1)];shrine_tri=tri[(owner==1)&np.all(((P[:,2]>20)&(P[:,2]<145))[tri],axis=1)];bodyids=np.unique(bodytri);shrineids=np.unique(shrine_tri);bf=np.searchsorted(bodyids,bodytri).tolist();sf=np.searchsorted(shrineids,shrine_tri).tolist()
top=np.argsort(W[bodyids],axis=1)[:,-4:];weights=np.take_along_axis(W[bodyids],top,axis=1);hom=np.column_stack((P[bodyids],np.ones(len(bodyids))));shrhom=np.column_stack((P[shrineids],np.ones(len(shrineids))))
# Read CURRENT Actions so later chase/attack work cannot fit against stale
# diagnostic snapshots. This evaluation does not insert or alter any keyframes.
poses=[];pose_skins={};scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');manifest=json.loads((R/'Reports/ClipManifest.json').read_text())
for action in bpy.data.actions:
 if not action.name.startswith(('AN_EXP_','AN_Penance_')):continue
 name=action.name;rig.animation_data.action=action;start,end=map(round,action.frame_range);frames=set(int(x) for x in np.rint(np.linspace(start,end,17)))
 if name in manifest and 'impact' in manifest[name]:frames.update(manifest[name][key] for key in ['impact','anticipation','recovery'])
 for f in sorted(frames):
  scene.frame_set(f);bpy.context.view_layer.update();m=np.array([np.array(rig.pose.bones[n].matrix) for n in B]);skin=np.einsum('bij,bjk->bik',m,inv,optimize=True);points=np.einsum('nk,nkij,nj->ni',weights,skin[top][:,:,:3,:],hom,optimize=True);body=BVHTree.FromPolygons([Vector(x) for x in points],bf,all_triangles=True);shr=shrhom@skin[mount,:3,:].T;direction=skin[mount,:3,1];poses.append((name,f,body,shr,direction));pose_skins[(name,f)]=skin[mount]
trials=[];best=None
pivot=rest[mount,:3,3];mask=part==1;source_points=source['points'];upper=mask&(source_points[:,2]>=162)
# Preserve the visual position of the upper shrine while fitting the lower
# frame through a SINGLE rigid placement transform. Every candidate is straight.
candidates=[(a,d) for a in [8,12,16,20] for d in [8,12,16,20,24]]
placements=[]
for angle,offset in candidates:
 rad=np.deg2rad(angle);c,s=np.cos(rad),np.sin(rad);rot=np.array([[1,0,0],[0,c,-s],[0,s,c]]);trans=pivot-rot@pivot+np.array([0.,offset,0.]);placed=source_points[mask]@rot.T+trans;trans[2]+=230.-placed[:,2].max();K=np.eye(4);K[:3,:3]=rot;K[:3,3]=trans;shift=source_points[upper]@rot.T+trans-source_points[upper];score=float(np.sqrt(np.mean(np.sum(shift**2,axis=1)))+.1*angle);placements.append((score,angle,offset,K))
placements.sort(key=lambda x:x[0])
for score,angle,offset,K in placements:
 counts={};max_count=0;placed=shrhom@K[:3,:].T
 for name,f,body,p,direction in poses:
  # The old p is original shrine geometry transformed by the mount. Rebuild
  # from the cached skin transform to apply the same rigid placement everywhere.
  entry=pose_skins[(name,f)];points=np.column_stack((placed,np.ones(len(placed))))@entry[:3,:].T
  shrine=BVHTree.FromPolygons([Vector(x) for x in points],sf,all_triangles=True);pairs=body.overlap(shrine);counts.setdefault(name,[]).append(len(pairs));max_count=max(max_count,len(pairs))
 result={'rigid_backward_offset_cm':offset,'rigid_pitch_degrees':angle,'canonical_placement_matrix':K.tolist(),'upper_shrine_placement_cost_cm':score,'maximum_contacts':max_count,'total_contacts':sum(sum(v) for v in counts.values()),'worst_by_clip':{n:max(v) for n,v in counts.items()}};trials.append(result);print('RIGID_ANGLE_MOUNT_TRIAL',result,flush=True)
 if best is None or result['total_contacts']<best['total_contacts']:best=result
 if max_count==0:break
(R/'Reports/RigidShrineMountTrials.json').write_text(json.dumps({'sampled_poses':len(poses),'trials':trials,'selected':best,'method':'Canonical straight shrine with ONE rigid mounting transform. Sorted by upper-shrine placement change; no shape warping or motion edits.'},indent=2)+'\n');print('RIGID_MOUNT_FIT_COMPLETE',best,flush=True)
