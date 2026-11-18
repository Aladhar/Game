"""Evaluate actual deformed mesh, loops, sole contact and separate surface contact.
Samples every native frame for all old and new Actions. BVH checks at 9 poses
per clip cover independent body / trim surfaces, excluding original seam touch.
"""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[1];scene=bpy.context.scene
rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH')
q=np.load(R/'Reports/ExperimentalMesh.npz');P=q['points'];W=q['weights'];B=list(q['names']);E=q['edges'];part=q['part'];L=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)
valid=L>.35;mesh.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in mesh.data.loop_triangles]);poly=np.array([t.polygon_index for t in mesh.data.loop_triangles]);owner=np.empty(len(mesh.data.polygons),np.int32);mesh.data.attributes['penance_part_owner'].data.foreach_get('value',owner);owner=owner[poly]
# Body and hanging trim below shoulder; keep BVH indexes compact.
legmass=sum(W[:,i] for i,n in enumerate(B) if n.startswith(('thigh','calf','foot','ball')) or n=='pelvis')
body_tri=tri[(owner==0)&np.all(((legmass>.65)&(P[:,2]>20)&(P[:,2]<125))[tri],axis=1)]
trim_tri=tri[(owner==1)&np.all(((P[:,2]>20)&(P[:,2]<145))[tri],axis=1)]
_,geokey=np.unique(np.rint(P*10000).astype(np.int64),axis=0,return_inverse=True)
sole={};regions={}
for side,sign in [('l',1),('r',-1)]:
 mass=sum(W[:,B.index(n+'_'+side)] for n in ['thigh','calf','foot','ball'])
 sole[side]=np.flatnonzero((P[:,0]*sign>5)&(P[:,2]<24)&(mass>.9)&(part==0))
for name,prefix,zrange in [('shoulders',('clavicle','upperarm','spine'),(115,165)),('elbows',('upperarm','lowerarm'),(78,135)),('wrists',('lowerarm','hand'),(60,110)),('hips',('pelvis','thigh'),(75,125)),('knees',('thigh','calf'),(35,80)),('ankles',('calf','foot','ball'),(0,35)),('spine',('spine','pelvis'),(100,165)),('accessories',('ornament','veil','bell','shrine'),(0,240))]:
 mass=sum(W[:,i] for i,n in enumerate(B) if n.startswith(prefix));mask=(mass>.7)&(P[:,2]>zrange[0])&(P[:,2]<zrange[1]);regions[name]=valid&np.all(mask[E],axis=1)
manifest=json.loads((R/'Reports/ClipManifest.json').read_text());allclips=dict(manifest)
for name,frames in [('AN_Penance_Idle',150),('AN_Penance_StalkWalk',60),('AN_Penance_Chase',30),('AN_Penance_Attack',45)]:allclips[name]={'frames':frames,'loop':name!='AN_Penance_Attack'}
report={'mesh_height_cm':float(np.ptp(P[:,2])),'bone_count':len(B),'max_influences':int(np.max(np.sum(W>.00001,axis=1))),'weight_sum_max_error':float(np.max(abs(W.sum(axis=1)-1))),'clips':{}}
for name,spec in allclips.items():
 rig.animation_data.action=bpy.data.actions[name];matrices=[];stats=[];regmax={n:0 for n in regions};contact=[]
 tests=set(np.rint(np.linspace(1,spec['frames']+1,9)).astype(int))
 if 'impact' in spec:tests.update([spec['impact'],spec['anticipation'],spec['recovery']])
 feet=[]
 for f in range(1,spec['frames']+2):
  scene.frame_set(f);bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());p=np.empty(P.size,np.float32);ev.data.vertices.foreach_get('co',p);p=p.reshape(-1,3)
  assert np.isfinite(p).all(),(name,f,'Nonfinite mesh')
  ratio=np.linalg.norm(p[E[:,0]]-p[E[:,1]],axis=1)/np.maximum(L,1e-6)
  matrices.append(np.array([np.array(b.matrix) for b in rig.pose.bones]))
  for n,mask in regions.items():
   if np.any(mask):regmax[n]=max(regmax[n],float(np.quantile(ratio[mask],.99)))
  stats.append({'frame':f,'sole_min_z_cm':{s:float(p[ids,2].min()) for s,ids in sole.items()},'edge_stretch_p99':float(np.quantile(ratio[valid],.99)),'edge_stretch_max':float(ratio[valid].max()),'edges_over_2':int(np.sum(ratio[valid]>2))})
  feet.append({s:np.median(p[ids],axis=0).tolist() for s,ids in sole.items()})
  if f in tests:
   verts=[Vector(v) for v in p];a=BVHTree.FromPolygons(verts,body_tri.tolist(),all_triangles=True);b=BVHTree.FromPolygons(verts,trim_tri.tolist(),all_triangles=True);pairs=a.overlap(b);count=0
   for i,j in pairs:
    skin,trim=body_tri[i],trim_tri[j];common=set(geokey[skin])&set(geokey[trim]);touch=False
    for key in common:
     x=skin[geokey[skin]==key];y=trim[geokey[trim]==key]
     if np.min(np.linalg.norm(p[x,None,:]-p[y][None,:,:],axis=-1))<.05:touch=True
    if not touch:count+=1
   contact.append({'frame':f,'body_trim_intersecting_triangle_pairs':count})
 m=np.array(matrices);rootdev=float(abs(m[:,B.index('root')]-q['rest'][B.index('root')]).max());looperr=float(abs(m[0]-m[-1]).max())
 # Drift measured during flat-foot stance, compensated by intended actor travel.
 drift=[]
 if spec.get('loop') and 'speed' in spec:
  for side,offset,stance in [('l',0,spec['stance'][0]),('r',.56 if 'Limp' in name else .51,spec['stance'][1])]:
   for i in range(spec['frames']):
    phase=((i/30)/(spec['frames']/30)+offset)%1.;nextphase=(((i+1)/30)/(spec['frames']/30)+offset)%1.
    if .12<phase<stance-.12 and .12<nextphase<stance-.12:
     delta=np.array(feet[i+1][side])-np.array(feet[i][side]);delta[1]-=spec['speed']/30;drift.append(float(np.linalg.norm(delta[:2])))
 report['clips'][name]={'frames_evaluated':len(stats),'duration_seconds':spec['frames']/30,'root_max_error':rootdev,'endpoint_matrix_error':looperr,'maximum_p99_by_region':regmax,'contacts_sampled':contact,'per_frame':stats,'flat_stance_world_drift_cm_per_frame_max':max(drift) if drift else None,'flat_stance_world_drift_cm_per_frame_mean':float(np.mean(drift)) if drift else None}
 assert rootdev<.001,(name,'Root moved',rootdev)
 if spec['loop']:assert looperr<.001,(name,'Loop endpoint mismatch',looperr)
 print('DEFORMATION',name,'loop',looperr,'contact max',max(x['body_trim_intersecting_triangle_pairs'] for x in contact),'regions',regmax,flush=True)
(R/'Reports/DeformationValidation.json').write_text(json.dumps(report,indent=2)+'\n')
print('DEFORMATION_VALIDATION_COMPLETE',flush=True)
