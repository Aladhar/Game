"""Second-pass skinning and accessory fit from measured deformation failures.
Uses graph diffusion across anatomical skin, with welded UV samples and protected
hands/soles/rigid parts. Selects strength against original and experimental poses.
"""
import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/ExperimentalMesh.npz');P=q['points'];W=q['weights'];B=list(q['names']);E=q['edges'];part=q['part'];rest=q['rest'];N=len(P)
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');scene=bpy.context.scene
beforeW=W.copy();beforeP=P.copy();inv=np.linalg.inv(rest);hom=np.column_stack((P,np.ones(N)))
def ease(a,b,v):
 t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
_,ids=np.unique(np.column_stack((np.rint(P*10000).astype(np.int64),part)),axis=0,return_inverse=True);M=ids.max()+1;count=np.bincount(ids);gw=np.zeros((M,len(B)));np.add.at(gw,ids,W);gw/=count[:,None]
owner=np.zeros(M,np.int32);owner[ids]=part;edges=np.unique(np.sort(ids[E],axis=1),axis=0);edges=edges[(edges[:,0]!=edges[:,1])&(owner[edges[:,0]]==0)&(owner[edges[:,1]]==0)];degree=np.bincount(edges.ravel(),minlength=M)
sm=gw.copy()
for i in range(120):
 total=np.zeros_like(sm);np.add.at(total,edges[:,0],sm[edges[:,1]]);np.add.at(total,edges[:,1],sm[edges[:,0]])
 avg=total/np.maximum(degree[:,None],1);active=degree>0;sm[active]=sm[active]*.45+avg[active]*.55
smooth=sm[ids];alpha=(part==0)*ease(27,45,P[:,2])*(1-ease(157,171,P[:,2]))
# The source contains a low bridge across the inner thighs. Anchor its center
# to pelvis with a broad continuous blend, instead of a left/right discontinuity.
center=(part==0)*(1-ease(2,12,abs(P[:,0]-.5)))*ease(59,78,P[:,2])*(1-ease(97,112,P[:,2]))
matrices=[]
for name in json.loads((R/'Reports/ClipManifest.json').read_text()):
 arr=np.load(R/'Reports'/(name+'_poses.npz'))['matrices'];matrices.extend(arr[::max(1,len(arr)//7)])
for name in ['AN_Penance_Idle','AN_Penance_StalkWalk','AN_Penance_Chase','AN_Penance_Attack']:
 rig.animation_data.action=bpy.data.actions[name]
 for f in np.linspace(*bpy.data.actions[name].frame_range,7):
  scene.frame_set(round(f));matrices.append(np.array([np.array(b.matrix) for b in rig.pose.bones]))
length=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1);measure=(length>.35)&np.all(part[E]==0,axis=1);local=np.unique(E[measure]);ed=np.searchsorted(local,E[measure]);rl=length[measure]
def clean(w):
 top=np.argsort(w,axis=1)[:,-4:];out=np.zeros_like(w);np.put_along_axis(out,top,np.take_along_axis(w,top,axis=1),axis=1);out[out<1e-4]=0;out/=out.sum(axis=1,keepdims=True);return out

def skin(w,m,vertices,points=P):
 top=np.argsort(w[vertices],axis=1)[:,-4:];v=np.take_along_axis(w[vertices],top,axis=1);h=np.column_stack((points[vertices],np.ones(len(vertices))))
 return np.einsum('nk,nkij,nj->ni',v,(m@inv)[top][:,:,:3,:],h,optimize=True)
trials=[];candidates=[]
for strength in [0,.35,.65,1.]:
 w=W*(1-strength*alpha[:,None])+smooth*(strength*alpha[:,None])
 c=center*(strength*.70);w*=1-c[:,None];w[:,B.index('pelvis')]+=c;w=clean(w)
 ratios=[]
 for m in matrices:
  p=skin(w,m,local);ratios.append(np.linalg.norm(p[ed[:,0]]-p[ed[:,1]],axis=1)/rl)
 ratios=np.array(ratios);score=float(np.mean(np.maximum(ratios-1.5,0)**2)+.3*np.mean(np.maximum(.5-ratios,0)**2))
 result={'strength':strength,'score':score,'p99':float(np.quantile(ratios,.99)),'max':float(ratios.max()),'over_2_fraction':float(np.mean(ratios>2))};trials.append(result);candidates.append(w);print('BROAD_WEIGHT_TRIAL',result,flush=True)
best=int(np.argmin([t['score'] for t in trials]));W=candidates[best]
# Refit lower rear drape in rest space, leaving shrine/shoulder attachment fixed.
# A continuous 12 cm rear flare plus 5 cm lateral flare gives limbs room without
# changing height, upper shrine, bone rest transforms or body shape.
flare=(part==1)*(1-ease(80,142,P[:,2]));P[:,1]+=12*flare;P[:,0]+=5*flare*np.tanh(P[:,0]/12)
mesh.data.vertices.foreach_set('co',P.astype(np.float32).ravel());mesh.data.update()
for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
groups=[mesh.vertex_groups.new(name=n) for n in B];quant=np.rint(W*100000).astype(np.int32);quant[np.arange(N),quant.argmax(axis=1)]+=100000-quant.sum(axis=1)
unique,index=np.unique(quant,axis=0,return_inverse=True)
for k,row in enumerate(unique):
 vertices=np.flatnonzero(index==k).tolist()
 for j in np.flatnonzero(row):groups[j].add(vertices,float(row[j])/100000,'REPLACE')
W=quant/100000.
# Save the exact modified buffers; validation uses these, not the trial arrays.
np.savez_compressed(R/'Reports/ExperimentalMesh.npz',points=P,weights=W,names=B,edges=E,part=part,rest=rest)
report={'trials':trials,'selected':trials[best],'sampled_poses':len(matrices),'changed_vertices_from_first_pass':int(np.sum(np.max(abs(W-beforeW),axis=1)>1e-5)),'drape_vertices_refit':int(np.sum(flare>0)),'drape_max_displacement_cm':float(np.linalg.norm(P-beforeP,axis=1).max()),'rest_skeleton_changed':False,'body_geometry_changed':False,'UVs_changed':False,'max_influences':int(np.max(np.sum(W>0,axis=1)))}
(R/'Reports/RefinementPass2.json').write_text(json.dumps(report,indent=2)+'\n')
rig.animation_data.action=bpy.data.actions['AN_EXP_Stalk'];scene.frame_start=1;scene.frame_end=85;scene.frame_set(1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(R/'Penance_AnimationExperiments.blend'),compress=True)
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.fbx(filepath=str(R/'FBX/SK_Penance_Experimental.fbx'),object_types={'ARMATURE','MESH'},use_selection=True,add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,path_mode='RELATIVE',bake_anim=False)
print('SECOND_REFINEMENT_SAVED',json.dumps(report),flush=True)
