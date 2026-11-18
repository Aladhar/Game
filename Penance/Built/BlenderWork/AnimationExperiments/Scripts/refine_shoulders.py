"""Anatomical shoulder/arm weight trials addressing the source's chest-to-arm jumps."""
import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');P=q['points'];W=q['weights'];B=list(q['names']);E=q['edges'];part=q['part'];rest=q['rest'];N=len(P);inv=np.linalg.inv(rest)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');scene=bpy.context.scene

def ease(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
proposal=W.copy();affected=np.zeros(N)
for side,sign in [('l',1),('r',-1)]:
 shoulder,elbow,wrist=[rest[B.index(n+'_'+side),:3,3] for n in ['upperarm','lowerarm','hand']]
 upper=(elbow-shoulder);upper/=np.linalg.norm(upper);lower=wrist-elbow;lower/=np.linalg.norm(lower)
 along=(P-shoulder)@upper;elbowalong=(P-elbow)@((upper+lower)/np.linalg.norm(upper+lower))
 handalong=(P-wrist)@lower
 influence=(part==0)*ease(12,34,P[:,0]*sign)*ease(91,108,P[:,2])*(1-ease(153,170,P[:,2]))
 # Hard shrine, veil and bell ownership is excluded by part labels.
 uppermass=ease(-10,12,along);lowermass=ease(-11,11,elbowalong);handmass=ease(-5,6,handalong)
 field=np.zeros_like(W);field[:,B.index('clavicle_'+side)]=1-uppermass;field[:,B.index('upperarm_'+side)]=uppermass*(1-lowermass);field[:,B.index('lowerarm_'+side)]=uppermass*lowermass*(1-handmass);field[:,B.index('hand_'+side)]=uppermass*lowermass*handmass
 proposal=proposal*(1-influence[:,None])+field*influence[:,None];affected=np.maximum(affected,influence)
length=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1);mask=(length>.35)&np.all(part[E]==0,axis=1)&np.all((P[:,2]>90)[E],axis=1);ids=np.unique(E[mask]);ed=np.searchsorted(ids,E[mask]);rl=length[mask];hom=np.column_stack((P[ids],np.ones(len(ids))))
matrices=[]
for name in ['AN_EXP_Stalk','AN_EXP_Chase','AN_EXP_Lunge','AN_EXP_Overhead','AN_EXP_Sweep']:
 arr=np.load(R/'Reports'/(name+'_poses.npz'))['matrices'];matrices.extend(arr[::max(1,len(arr)//9)])
trials=[];candidates=[]
for strength in [0,.35,.65,1]:
 w=W*(1-strength)+proposal*strength;top=np.argsort(w,axis=1)[:,-4:];out=np.zeros_like(w);np.put_along_axis(out,top,np.take_along_axis(w,top,axis=1),axis=1);out[out<1e-4]=0;out/=out.sum(axis=1,keepdims=True)
 top=np.argsort(out[ids],axis=1)[:,-4:];values=np.take_along_axis(out[ids],top,axis=1);ratios=[]
 for m in matrices:
  p=np.einsum('nk,nkij,nj->ni',values,(m@inv)[top][:,:,:3,:],hom,optimize=True);ratios.append(np.linalg.norm(p[ed[:,0]]-p[ed[:,1]],axis=1)/rl)
 ratios=np.array(ratios);score=float(np.mean(np.maximum(ratios-1.5,0)**2)+.3*np.mean(np.maximum(.5-ratios,0)**2));entry={'strength':strength,'score':score,'p99':float(np.quantile(ratios,.99)),'max':float(ratios.max())};trials.append(entry);candidates.append(out);print('SHOULDER_TRIAL',entry,flush=True)
best=int(np.argmin([t['score'] for t in trials]));out=candidates[best];changed=int(np.sum(np.max(abs(out-W),axis=1)>1e-5));W=out
quant=np.rint(W*100000).astype(np.int32);quant[np.arange(N),quant.argmax(axis=1)]+=100000-quant.sum(axis=1);W=quant/100000
for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
groups=[mesh.vertex_groups.new(name=n) for n in B];unique,index=np.unique(quant,axis=0,return_inverse=True)
for k,row in enumerate(unique):
 vertices=np.flatnonzero(index==k).tolist()
 for j in np.flatnonzero(row):groups[j].add(vertices,float(row[j])/100000,'REPLACE')
np.savez_compressed(R/'Reports/ExperimentalMesh.npz',points=P,weights=W,names=B,edges=E,part=part,rest=rest)
(R/'Reports/ShoulderRefinement.json').write_text(json.dumps({'trials':trials,'selected':trials[best],'changed_vertices':changed,'purpose':'Replace inappropriate spinal influences on lateral upper-arm skin with continuous shoulder/elbow fields.'},indent=2)+'\n')
rig.animation_data.action=bpy.data.actions['AN_EXP_Stalk'];scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'Penance_AnimationExperiments.blend'),compress=True)
print('SHOULDER_REFINEMENT_SAVED',flush=True)
