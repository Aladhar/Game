"""Quantify shape changes in shrine space, excluding ordinary body lean.
Uses saved source buffers and freshly evaluated matrices. Writes diagnostics only.
"""
from pathlib import Path
import numpy as np,json
O=Path(__file__).resolve().parent;R=O.parents[1]
a=np.load(R/'Checkpoints/BeforeStraightShrine/ExperimentalMesh.npz');s=np.load(R/'Reports/SourceMesh.npz');P=a['points'];P0=s['points'];W=a['weights'];B=list(a['names']);part=a['part'];rest=a['rest'];inv=np.linalg.inv(rest)
W0=np.zeros_like(W)
for i,n in enumerate(s['names']):W0[:,B.index(str(n))]=s['weights'][:,i]
ids=np.flatnonzero(part==1);p=P[ids];p0=P0[ids];wf=W[ids];w0=W0[ids];mount=B.index('shrine_mount');bones=np.flatnonzero(np.max(wf,axis=0)>.000001);oldbones=np.flatnonzero(np.max(w0,axis=0)>.000001)
h=np.column_stack((p,np.ones(len(p))));h0=np.column_stack((p0,np.ones(len(p0))))
delta=p-p0;bands={}
for label,low,high in [('lower_20_80cm',20,80),('bend_80_142cm',80,142),('attachment_142_162cm',142,162),('upper_162_231cm',162,231)]:
 mask=(p0[:,2]>=low)&(p0[:,2]<high)
 bands[label]={'vertices':int(mask.sum()),'max_back_shift_cm':float(delta[mask,1].max()),'max_displacement_cm':float(np.linalg.norm(delta[mask],axis=1).max())}
def evaluate(weights,positions,local,boneids):
 out=np.zeros((len(positions),3))
 for j in boneids:out+=(positions@local[j,:3,:].T)*weights[:,j,None]
 return out
clips={};matrices={};max_reset=0;uppermask=p0[:,2]>=162
for file in sorted(O.glob('AN_*_Evaluated.npz')):
 q=np.load(file);name=file.name.removesuffix('_Evaluated.npz');m=q['matrices'];names=list(q['names']);m=m[:,[names.index(n) for n in B]];finalmax=[];originalmax=[];upper=[];rms=[];oldrms=[]
 for f,pose in enumerate(m):
  skin=np.einsum('bij,bjk->bik',pose,inv,optimize=True);mount_inv=np.linalg.inv(skin[mount]);local=np.einsum('ij,bjk->bik',mount_inv,skin,optimize=True)
  d=evaluate(wf,h,local,bones)-p;d0=evaluate(w0,h0,local,oldbones)-p0
  distance=np.linalg.norm(d,axis=1);distance0=np.linalg.norm(d0,axis=1);finalmax.append(float(distance.max()));originalmax.append(float(distance0.max()));upper.append(float(distance[uppermask].max()));rms.append(float(np.sqrt(np.mean(distance**2))));oldrms.append(float(np.sqrt(np.mean(distance0**2))))
  if f==0:
   neutral=local.copy()
   for j in bones:neutral[j]=np.eye(4)
   err=np.linalg.norm(evaluate(wf,h,neutral,bones)-p,axis=1).max();max_reset=max(max_reset,float(err))
 peak=int(np.argmax(finalmax));clips[name]={'frames':len(m),'current_extra_bend_in_shrine_space_max_cm':max(finalmax),'current_extra_bend_rms_at_peak_cm':rms[peak],'peak_frame':peak+1,'source_mesh_source_weights_extra_bend_max_cm':max(originalmax),'source_extra_bend_rms_at_peak_cm':oldrms[int(np.argmax(originalmax))],'upper_shrine_extra_bend_max_cm':max(upper),'current_extra_bend_per_frame_cm':finalmax}
 print('SHRINE_CAUSE',name,{k:v for k,v in clips[name].items() if not isinstance(v,list)},flush=True)
report={'method':'Linear skinning in the moving shrine_mount coordinate frame; ordinary whole-body translation/rotation removed. Every shrine vertex and every animation frame evaluated.','shrine_vertices':len(ids),'static_rest_shape_changed_vertices':int(np.sum(np.linalg.norm(delta,axis=1)>1e-6)),'static_max_backward_shift_cm':float(delta[:,1].max()),'static_max_lateral_shift_cm':float(abs(delta[:,0]).max()),'rest_displacement_bands':bands,'bone_influences_current':[B[j] for j in bones],'bone_influences_source':[B[j] for j in oldbones],'ornament_motion_removed_dynamic_shape_error_cm':max_reset,'clips':clips}
(O/'RootCauseMetrics.json').write_text(json.dumps(report,indent=2)+'\n')
