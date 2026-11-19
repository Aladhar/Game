"""Optimize four-influence skinning against measured edge strain in real poses.
Projected Adam preserves normalized nonnegative weights on fixed local supports.
UV duplicate vertices are solved as one node. Bone transforms and geometry stay.
"""
from pathlib import Path
import numpy as np,json
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');P=q['points'];W=q['weights'];E=q['edges'];part=q['part'];B=list(q['names']);rest=q['rest']
keys,inv=np.unique(np.column_stack((np.rint(P*10000).astype(np.int64),part)),axis=0,return_inverse=True);count=np.bincount(inv);M=len(count);p=np.zeros((M,3));w=np.zeros((M,len(B)));np.add.at(p,inv,P);np.add.at(w,inv,W);p/=count[:,None];w/=count[:,None];owner=np.zeros(M,np.int32);owner[inv]=part
edges=np.unique(np.sort(inv[E],axis=1),axis=0);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);mask=(length>.35)&(owner[edges[:,0]]==0)&(owner[edges[:,1]]==0);edges=edges[mask];length=length[mask];ids=np.unique(edges);pp=p[ids];ww=w[ids];edge=np.searchsorted(ids,edges)
# Candidate supports come from local topology, excluding every accessory bone.
near=w.copy();deg=np.bincount(edges.ravel(),minlength=M)
for i in range(8):
 total=np.zeros_like(near);np.add.at(total,edges[:,0],near[edges[:,1]]);np.add.at(total,edges[:,1],near[edges[:,0]]);mask=deg>0;near[mask]=.5*near[mask]+.5*total[mask]/deg[mask,None]
allowed=np.array([not n.startswith(('ornament','veil','bell','shrine','root')) for n in B]);candidate=(ww+near[ids]*.15)*allowed[None,:];support=np.argsort(candidate,axis=1)[:,-4:];base=np.take_along_axis(ww,support,axis=1);zero=np.take_along_axis(candidate,support,axis=1)<1e-6;support[zero]=np.broadcast_to(ww.argmax(axis=1)[:,None],support.shape)[zero];base[zero]=0;base/=base.sum(axis=1,keepdims=True)
matrices=[];pose_names=[]
for name in ['AN_EXP_Stalk','AN_EXP_Limp','AN_EXP_Heavy','AN_EXP_Chase','AN_EXP_Lunge','AN_EXP_Overhead','AN_EXP_Sweep']:
 arr=np.load(R/'Reports'/(name+'_poses.npz'))['matrices'];selected=np.unique(np.rint(np.linspace(0,len(arr)-1,6)).astype(int))
 if name=='AN_EXP_Overhead':selected=np.unique(np.r_[selected,24,33])
 for f in selected:matrices.append(arr[f]);pose_names.append(name+':'+str(f+1))
h=np.column_stack((pp,np.ones(len(pp))));skin=np.einsum('fbij,bjk->fbik',np.array(matrices),np.linalg.inv(rest),optimize=True)
S=np.einsum('fnkij,nj->fnki',skin[:,support,:3,:],h,optimize=True).astype(np.float32)
# Remove common translation from the gradient; partition of unity makes this
# algebraically equivalent and substantially improves numerical conditioning.
S-=S[:,:,0:1,:];reference=np.einsum('nk,fnki->fni',base,S,optimize=True)
active=((pp[:,2]>35)&(pp[:,2]<168)).astype(float)
def project(v):
 u=np.sort(v,axis=1)[:,::-1];css=np.cumsum(u,axis=1)-1;condition=u-css/np.arange(1,5)>0;rho=condition.sum(axis=1)-1;theta=css[np.arange(len(v)),rho]/(rho+1);return np.maximum(v-theta[:,None],0)
def evaluate(v,gradient=False):
 posed=np.einsum('nk,fnki->fni',v,S,optimize=True);delta=posed[:,edge[:,0]]-posed[:,edge[:,1]]
 # Common translation was removed per vertex; restore its differential.
 if not hasattr(evaluate,'offset'):
  T=skin[:,support[:,0],:3,:];evaluate.offset=np.einsum('fnij,nj->fni',T,h,optimize=True)
 delta+=evaluate.offset[:,edge[:,0]]-evaluate.offset[:,edge[:,1]]
 dist=np.linalg.norm(delta,axis=-1);ratio=dist/length[None,:];high=np.maximum(ratio-1.45,0);low=np.minimum(ratio-.55,0)
 loss=float(np.mean(high**2+.15*low**2)+.00008*np.mean((posed-reference)**2)+.006*np.mean((v-base)**2))
 metrics={'loss':loss,'p99':float(np.quantile(ratio,.99)),'max':float(ratio.max()),'fraction_over_2':float(np.mean(ratio>2))}
 if not gradient:return metrics
 d=(2*high+.3*low)/(length[None,:]*np.maximum(dist,1e-6));gd=delta*d[:,:,None];gp=np.zeros_like(posed)
 for f in range(len(S)):
  np.add.at(gp[f],edge[:,0],gd[f]);np.add.at(gp[f],edge[:,1],-gd[f])
 gp+=.00016*(posed-reference)
 grad=np.einsum('fni,fnki->nk',gp,S,optimize=True)/len(S)+.012*(v-base)
 return metrics,grad
current=base.copy();moment=np.zeros_like(current);variance=np.zeros_like(current);best=base.copy();best_metrics=evaluate(current);trace=[{'iteration':0,**best_metrics}];print('SKIN_OPT_INITIAL',best_metrics,flush=True)
for iteration in range(1,101):
 stats,g=evaluate(current,True);g-=g.mean(axis=1,keepdims=True);g*=active[:,None];moment=.9*moment+.1*g;variance=.999*variance+.001*g*g;step=(moment/(1-.9**iteration))/(np.sqrt(variance/(1-.999**iteration))+1e-8)
 current=project(current-.008*step*active[:,None])
 # Keep the limb attachment recognizable while allowing local redistribution.
 current=project(np.clip(current,base-.38,base+.38))
 if iteration%10==0:
  stats=evaluate(current);trace.append({'iteration':iteration,**stats});print('SKIN_OPT',iteration,stats,flush=True)
  if stats['loss']<best_metrics['loss']:best=current.copy();best_metrics=stats
out=w.copy();out[ids]=0
for j in range(4):np.add.at(out,(ids,support[:,j]),best[:,j])
result=out[inv];quant=np.rint(result*100000).astype(np.int32);quant[np.arange(len(P)),quant.argmax(axis=1)]+=100000-quant.sum(axis=1);result=quant/100000
np.savez_compressed(R/'Reports/OptimizedWeights.npz',weights=result)
report={'method':'Projected gradient optimization on welded anatomical skin; four local influences, strain and compression penalties, pose and source-weight regularization.','pose_samples':pose_names,'trace':trace,'selected':best_metrics,'changed_vertices':int(np.sum(np.max(abs(result-W),axis=1)>1e-5)),'max_influences':int(np.max(np.sum(result>0,axis=1)))}
(R/'Reports/WeightOptimization.json').write_text(json.dumps(report,indent=2)+'\n');print('SKIN_OPT_COMPLETE',report['selected'],flush=True)
