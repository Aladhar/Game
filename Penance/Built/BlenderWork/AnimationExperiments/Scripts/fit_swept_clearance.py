"""Compatibility pipeline: fit one rigid shrine mount, never warp architecture.
The old vertex-dependent flare has been removed to prevent the diagnosed bend.
"""
from pathlib import Path
import runpy,json,numpy as np,bpy
R=Path(__file__).resolve().parents[1]
# Preserve the earlier pose-based BODY skin optimization in a full rebuild.
q=np.load(R/'Reports/ExperimentalMesh.npz');W=q['weights'].copy();part=q['part'];names=list(q['names']);opt=R/'Reports/OptimizedWeights.npz'
if opt.exists():
 candidate=np.load(opt)['weights'];W[part!=1]=candidate[part!=1];mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');ids=np.flatnonzero(part!=1).tolist()
 for g in mesh.vertex_groups:g.remove(ids)
 quant=np.rint(W[part!=1]*100000).astype(np.int32);quant[np.arange(len(quant)),quant.argmax(axis=1)]+=100000-quant.sum(axis=1);unique,index=np.unique(quant,axis=0,return_inverse=True);vertices=np.flatnonzero(part!=1)
 for k,row in enumerate(unique):
  use=vertices[index==k].tolist()
  for j in np.flatnonzero(row):mesh.vertex_groups[names[j]].add(use,float(row[j])/100000,'REPLACE')
 np.savez_compressed(R/'Reports/ExperimentalMesh.npz',points=q['points'],weights=W,names=names,edges=q['edges'],part=part,rest=q['rest'])
runpy.run_path(str(Path(__file__).with_name('fit_rigid_shrine_mount.py')),run_name='__main__')
runpy.run_path(str(Path(__file__).with_name('repair_shrine_rigidity.py')),run_name='__main__')
