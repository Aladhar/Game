"""Penance animation experiments: centimeter-space IK, dense samples, weight trials.
Run: Blender -b Penance_Animated.blend --python author_experiments.py
"""
import bpy, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix
from math import sin,cos,pi,sqrt,radians
R=Path(__file__).resolve().parents[1]
scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1
rig=next(o for o in scene.objects if o.type=='ARMATURE')
mesh=next(o for o in scene.objects if o.type=='MESH')
rig.animation_data_clear();rig.animation_data_create()
B=[b.name for b in rig.data.bones];rest={b.name:b.matrix_local.copy() for b in rig.data.bones}
H={b.name:b.head_local.copy() for b in rig.data.bones};T={b.name:b.tail_local.copy() for b in rig.data.bones}
X,Y,Z=Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1));tau=2*pi
P=np.array([v.co[:] for v in mesh.data.vertices]);N=len(P)
W=np.zeros((N,len(B)),np.float32)
for v in mesh.data.vertices:
 for g in v.groups:W[v.index,B.index(mesh.vertex_groups[g.group].name)]=g.weight
oldW=W.copy();E=np.array([e.vertices[:] for e in mesh.data.edges]);L=np.linalg.norm(P[E[:,0]]-P[E[:,1]],axis=1)
valid=L>.35
parts=np.empty(len(mesh.data.polygons),np.int32);mesh.data.attributes['penance_part_owner'].data.foreach_get('value',parts)
vpart=np.full(N,-1,np.int32)
for face,part in zip(mesh.data.polygons,parts):vpart[list(face.vertices)]=part
sole={}
for side,sign in [('l',1),('r',-1)]:
 mass=sum(W[:,B.index(n+'_'+side)] for n in ['thigh','calf','foot','ball'])
 sole[side]=np.flatnonzero((P[:,0]*sign>5)&(P[:,2]<24)&(mass>.9)&(vpart==0))
assert all(len(a)>20 for a in sole.values())
CLIPS={
 'AN_EXP_Stalk':dict(frames=84,loop=True,speed=30.,stance=(.72,.75),lift=(7.,6.),drop=7.,lean=2.,sway=2.,arms=6.),
 'AN_EXP_Limp':dict(frames=72,loop=True,speed=34.,stance=(.59,.80),lift=(8.,2.3),drop=8.,lean=4.,sway=3.8,arms=8.),
 'AN_EXP_Heavy':dict(frames=60,loop=True,speed=52.,stance=(.70,.70),lift=(8.,8.),drop=8.,lean=3.8,sway=3.,arms=9.),
 'AN_EXP_Chase':dict(frames=30,loop=True,speed=115.,stance=(.59,.62),lift=(16.,14.),drop=12.,lean=13.,sway=3.5,arms=23.),
 'AN_EXP_Lunge':dict(frames=54,loop=False,speed=0.,impact=19,anticipation=10,recovery=32),
 'AN_EXP_Overhead':dict(frames=78,loop=False,speed=0.,impact=34,anticipation=25,recovery=49),
 'AN_EXP_Sweep':dict(frames=66,loop=False,speed=0.,impact=25,anticipation=16,recovery=40),
}
def smooth(t):
 t=max(0.,min(1.,t));return t*t*t*(t*(6*t-15)+10)
def curve(t,keys):
 for (a,x),(b,y) in zip(keys,keys[1:]):
  if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
 return keys[-1][1]
def reset():
 for b in rig.pose.bones:
  b.rotation_mode='QUATERNION';b.location=(0,0,0);b.rotation_quaternion=(1,0,0,0);b.scale=(1,1,1)
def rot(n,axis,deg):
 b=rig.pose.bones[n];b.rotation_quaternion=Quaternion(rest[n].to_quaternion().inverted()@axis,radians(deg))@b.rotation_quaternion

def pelvis(delta):rig.pose.bones['pelvis'].location=rest['pelvis'].to_quaternion().inverted()@Vector(delta)
def aim(n,target):
 b=rig.pose.bones[n];m=b.matrix.copy();d=m.to_3x3()@Y;q=d.rotation_difference(Vector(target)-m.translation)
 result=(q.to_matrix()@m.to_3x3()).to_4x4();result.translation=m.translation;b.matrix=result;bpy.context.view_layer.update()
def leg(side,target,angle=0.,toe=0.):
 a,b,c=[s+'_'+side for s in ['thigh','calf','foot']];hip=rig.pose.bones[a].matrix.translation.copy();d=Vector(target)-hip
 u=(T[a]-H[a]).length;v=(T[b]-H[b]).length;dist=min(d.length,u+v-.08);f=d.normalized()
 pole=(rig.pose.bones['pelvis'].matrix@rest['pelvis'].inverted()).to_3x3()@Vector((0,-1,0));bend=(pole-f*pole.dot(f)).normalized()
 along=(u*u-v*v+dist*dist)/(2*dist);knee=hip+f*along+bend*sqrt(max(0,u*u-along*along))
 aim(a,knee);aim(b,hip+f*dist)
 for n,deg in [(c,angle),('ball_'+side,angle+toe)]:
  mat=(Quaternion(X,radians(deg)).to_matrix()@rest[n].to_3x3()).to_4x4();mat.translation=rig.pose.bones[n].matrix.translation;rig.pose.bones[n].matrix=mat;bpy.context.view_layer.update()
 return (rig.pose.bones[c].matrix.translation-Vector(target)).length

def points():
 bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());p=np.empty(N*3,np.float32);ev.data.vertices.foreach_get('co',p);return p.reshape(-1,3)

def gait(s,t,side):
 dur=s['frames']/30.;idx=0 if side=='l' else 1
 offset=0 if idx==0 else (.56 if 'limp'==s.get('style') else .51)
 phase=(t/dur+offset)%1.;stance=s['stance'][idx];travel=s['speed']*dur*stance
 target=H['foot_'+side].copy()
 if phase<=stance:
  target.y+=-.5*travel+s['speed']*dur*phase;lift=0
  angle=-3*(1-smooth(phase/.10))+7*smooth((phase-stance+.10)/.10)
  toe=-angle*.85;planted=True
 else:
  u=(phase-stance)/(1-stance);vel=s['speed']*dur*(1-stance)
  target.y+=.5*travel+vel*u+(-travel-vel)*smooth(u)
  lift=s['lift'][idx]*sin(pi*u)**2;angle=7-10*smooth(u);toe=-5.95*(1-smooth(u));planted=False
 target.z+=lift
 return target,planted,angle,toe,lift

def pose(name,f,correction=None):
 reset();s=CLIPS[name];t=f/30;dur=s['frames']/30;cycle=t/dur;w=sin(tau*cycle);shift=sin(tau*cycle-.25)
 targets={};planted={};ang={};toes={};lifts={}
 if s['loop']:
  limp='Limp' in name;heavy='Heavy' in name;chase='Chase' in name;stalk='Stalk' in name
  s['style']='limp' if limp else 'normal'
  # Body leads the support shift; no root translation is baked into the clip.
  extra=(1.5*sin(tau*cycle+.9)+.7*sin(2*tau*cycle)) if limp else 0
  bob=(.65 if heavy else 1.0 if chase else .45)*cos(2*tau*cycle-.1)
  pelvis((s['sway']*shift+extra,-2.3 if chase else -.4,-s['drop']+bob+(-1.3*max(0,-w) if limp else 0)))
  rot('pelvis',Y,1.5*shift if limp else .8*shift);rot('pelvis',Z,2*w if chase else 1.3*w)
  for n,k in [('spine_01',.43),('spine_02',.37),('spine_03',.20)]:rot(n,X,s['lean']*k+.22*cos(2*tau*cycle-.3))
  rot('spine_02',Y,-1.2*shift if limp else -.4*shift);rot('spine_02',Z,-2.2*w if chase else -.8*w)
  rot('neck_01',X,-s['lean']*.35)
  # One brief look per slow cycle; not continuous twitching.
  look=curve(cycle,[(0,0),(.17,0),(.24,3.5),(.46,3.5),(.64,0),(1,0)]) if stalk else .8*sin(tau*cycle-.5)
  rot('head',Z,look);rot('head',Y,.5*sin(tau*cycle+.7))
  for side,sign in [('l',1),('r',-1)]:
   phase=tau*cycle+(0 if side=='l' else pi+.13)
   rot('upperarm_'+side,X,s['arms']*sin(phase-.17)+(-2 if side=='r' else 0))
   rot('upperarm_'+side,Y,sign*(2.5 if chase else 1.))
   rot('lowerarm_'+side,X,(-21 if chase else -7)+(6 if chase else 2)*sin(phase-.55))
   rot('clavicle_'+side,Z,sign*(1.2 if chase else .7)*w)
   rot('hand_'+side,Z,sign*1.4*sin(phase-.7))
   target,plant,a,toe,lift=gait(s,t,side);targets[side]=target;planted[side]=plant;ang[side]=a;toes[side]=toe;lifts[side]=lift
   lag=tau*cycle-.65-(.12 if side=='r' else 0)
   rot('ornament_01_'+side,X,(17 if chase else 10)+2*sin(lag)+.4*sin(2*lag))
   rot('ornament_01_'+side,Y,sign*-3.2)
   rot('ornament_02_'+side,X,-2+1.1*sin(lag-.45))
  rot('bell_r',X,(15 if chase else 7)*sin(tau*cycle-.8)+(8 if chase else 3))
  rot('bell_r',Y,2*sin(tau*cycle-1));rot('veil_01',X,(5 if chase else 1.5)+sin(tau*cycle-.4));rot('veil_02',X,-.7+.5*sin(tau*cycle-.8))
 else:
  impact=(s['impact']-1)/30;wind=(s['anticipation']-1)/30;recover=(s['recovery']-1)/30
  anticip=curve(t,[(0,0),(wind,1),(impact,0),(dur,0)])
  hit=curve(t,[(0,0),(wind,0),(impact,1),(impact+.10,.96),(recover,.56),(dur,0)])
  follow=curve(t,[(0,0),(impact,0),(impact+.17,1),(recover+.15,.5),(dur,0)])
  if 'Lunge' in name:
   pelvis((-2.5*anticip+3.5*hit,-10*hit,-4-2.8*anticip-1.5*hit))
   lean=-5*anticip+19*hit;twist=-5*anticip+9*hit
   arm_l=15*anticip-78*hit+8*follow;arm_r=10*anticip-55*hit
   elbow_l=-34*anticip-9*hit;elbow_r=-18*anticip-20*hit
   spread_l=5*hit;spread_r=-4*hit
  elif 'Overhead' in name:
   pelvis((-3*anticip+4*hit,-4*hit,-5-1.5*anticip-4*hit))
   lean=-8*anticip+23*hit;twist=-8*anticip+10*hit
   arm_l=-156*anticip-42*hit+12*follow;arm_r=-50*anticip-27*hit
   elbow_l=-32*anticip-10*hit;elbow_r=-36*anticip-22*hit
   spread_l=11*anticip;spread_r=-8*anticip
  else:
   pelvis((-5*anticip+5*hit,-3*hit,-5-1*anticip-1*hit))
   lean=1*anticip+10*hit;twist=-24*anticip+29*hit-5*follow
   arm_l=-30*anticip-69*hit;arm_r=10*anticip-34*hit
   elbow_l=-22*anticip-13*hit;elbow_r=-22*anticip-20*hit
   spread_l=55*anticip-40*hit;spread_r=-8*hit
  rot('pelvis',Z,twist*.2)
  for n,k in [('spine_01',.44),('spine_02',.36),('spine_03',.20)]:rot(n,X,lean*k);rot(n,Z,twist*k*.8)
  rot('neck_01',X,-lean*.30);rot('head',Z,-twist*.25)
  for side,arm,elbow,spread in [('l',arm_l,elbow_l,spread_l),('r',arm_r,elbow_r,spread_r)]:
   rot('clavicle_'+side,X,-8*anticip if side=='l' and 'Overhead' in name else -2*hit)
   rot('upperarm_'+side,X,arm);rot('upperarm_'+side,Y,spread);rot('lowerarm_'+side,X,elbow)
   rot('hand_'+side,X,-5*anticip+6*hit);rot('hand_'+side,Z,(-5 if side=='l' else 3)*hit)
   targets[side]=H['foot_'+side].copy();planted[side]=True;ang[side]=0;toes[side]=0;lifts[side]=0
   lag=curve(max(0,t-.10),[(0,0),(wind,.3),(impact,1),(recover,.6),(dur,0)])
   rot('ornament_01_'+side,X,8+17*lag);rot('ornament_01_'+side,Y,-3.5 if side=='l' else 3.5);rot('ornament_02_'+side,X,-3*lag)
  rot('bell_r',X,-12*anticip+43*hit-10*follow)
  rot('veil_01',X,-2*anticip+8*hit);rot('veil_02',X,-1*anticip+3*follow)
 bpy.context.view_layer.update();err=0
 for side in ['l','r']:
  target=targets[side].copy();target.z+=(correction or {}).get(side,0)
  err=max(err,leg(side,target,ang[side],toes[side]))
 return planted,lifts,err

# Store full dense samples first. The weight trial then uses identical poses.
poses={};checks={}
for name,s in CLIPS.items():
 a=bpy.data.actions.new(name);a.use_fake_user=True;rig.animation_data.action=a;previous={};mats=[];stats=[]
 for f in range(s['frames']+1):
  scene.frame_set(f+1);planted,lift,err=pose(name,f);p=points();correction={side:lift[side]-float(p[ids,2].min()) for side,ids in sole.items()}
  for j in range(2):
   planted,lift,err=pose(name,f,correction);p=points()
   for side,ids in sole.items():correction[side]+=lift[side]-float(p[ids,2].min())
  planted,lift,err=pose(name,f,correction);p=points()
  mats.append(np.array([np.array(b.matrix) for b in rig.pose.bones]))
  stats.append({'frame':f+1,'sole_z':{side:float(p[ids,2].min()) for side,ids in sole.items()},'planted':planted,'ik_error_cm':err})
  for b in rig.pose.bones:
   q=b.rotation_quaternion
   if b.name in previous and q.dot(previous[b.name])<0:q.negate()
   previous[b.name]=q.copy();b.keyframe_insert('rotation_quaternion',frame=f+1,group=b.name)
   if b.name=='pelvis':b.keyframe_insert('location',frame=f+1,group=b.name)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 a.use_frame_range=True;a.frame_start=1;a.frame_end=s['frames']+1
 a['loop']=s['loop'];a['speed_cm_s']=s['speed']
 if not s['loop']:
  for label,key in [('WindupPeak','anticipation'),('Impact','impact'),('Recovery','recovery')]:a.pose_markers.new(label).frame=s[key]
  a['impact_seconds']=(s['impact']-1)/30
 poses[name]=np.array(mats);checks[name]=stats
 print('AUTHORED',name,s['frames']+1,'samples',flush=True)

# Trial local weight diffusion on actual anatomical surfaces; preserve rigid
# accessories, sole, fingers, and coincident UV samples. No skeleton edits.
# Compare candidates on old and new animation poses before selecting.
body=(vpart==0);region=np.zeros(N)
for side in ['l','r']:
 for joint,width in [('upperarm',15),('lowerarm',11),('hand',6),('thigh',15),('calf',12),('foot',8)]:
  n=joint+'_'+side;c=np.array(H[n]);dist=np.linalg.norm(P-c,axis=1)
  own=sum(W[:,B.index(k+'_'+side)] for k in (['clavicle','upperarm','lowerarm','hand'] if joint in ['upperarm','lowerarm','hand'] else ['thigh','calf','foot','ball']))
  region=np.maximum(region,np.clip(1-dist/width,0,1)*np.clip((own-.3)/.5,0,1))
region*=body
# Weld by position AND semantic owner, so UV seams share weights while hanging
# trim is never diffused into skin.
_,inverse=np.unique(np.column_stack((np.rint(P*10000).astype(np.int64),vpart)),axis=0,return_inverse=True)
count=np.bincount(inverse);M=len(count);gw=np.zeros((M,len(B)));np.add.at(gw,inverse,W);gw/=count[:,None]
ge=np.unique(np.sort(inverse[E],axis=1),axis=0);ge=ge[(ge[:,0]!=ge[:,1])&(vpart[E[:0,0]].size==0)] if False else ge[ge[:,0]!=ge[:,1]]
# Only connect nodes whose endpoint vertices belong to the same surface owner.
keyowner=np.zeros(M,np.int32);keyowner[inverse]=vpart;ge=ge[keyowner[ge[:,0]]==keyowner[ge[:,1]]]
degree=np.bincount(ge.ravel(),minlength=M);sm=gw.copy()
for iteration in range(12):
 total=np.zeros_like(sm);np.add.at(total,ge[:,0],sm[ge[:,1]]);np.add.at(total,ge[:,1],sm[ge[:,0]])
 average=total/np.maximum(degree[:,None],1);sm=.60*sm+.40*average
smoothW=sm[inverse];trials=[];sample=[]
for name,arr in poses.items():sample.extend(arr[::max(1,len(arr)//6)])
for name in ['AN_Penance_Idle','AN_Penance_StalkWalk','AN_Penance_Chase','AN_Penance_Attack']:
 rig.animation_data.action=bpy.data.actions[name]
 for f in np.linspace(*bpy.data.actions[name].frame_range,6):scene.frame_set(round(f));sample.append(np.array([np.array(b.matrix) for b in rig.pose.bones]))
invrest=np.linalg.inv(np.array([np.array(rest[n]) for n in B]));hom=np.column_stack((P,np.ones(N)))
measured=valid&np.all(body[E],axis=1)&np.any((region>.05)[E],axis=1)
# Evaluate only vertices incident to measured edges, making selection reproducible.
ids=np.unique(E[measured]);edge_local=np.searchsorted(ids,E[measured]);rlen=L[measured]
def skin(w,mat,ids):
 top=np.argsort(w[ids],axis=1)[:,-4:];weights=np.take_along_axis(w[ids],top,axis=1)
 return np.einsum('nk,nkij,nj->ni',weights,(mat@invrest)[top,:,:][:,:,:3,:],hom[ids],optimize=True)
candidates=[]
for alpha in [0.,.25,.5,.75]:
 w=W*(1-alpha*region[:,None])+smoothW*(alpha*region[:,None]);top=np.argsort(w,axis=1)[:,-4:];q=np.zeros_like(w);np.put_along_axis(q,top,np.take_along_axis(w,top,axis=1),axis=1);q[q<.0001]=0;q/=q.sum(axis=1,keepdims=True)
 ratios=[]
 for mat in sample:
  p=skin(q,mat,ids);ratios.append(np.linalg.norm(p[edge_local[:,0]]-p[edge_local[:,1]],axis=1)/rlen)
 ratios=np.array(ratios);score=float(np.mean(np.maximum(ratios-1.5,0)**2)+.25*np.mean(np.maximum(.5-ratios,0)**2))
 trial={'alpha':alpha,'score':score,'p99_stretch':float(np.quantile(ratios,.99)),'max_stretch':float(ratios.max()),'fraction_over_2':float(np.mean(ratios>2))};trials.append(trial);candidates.append(q);print('WEIGHT_TRIAL',trial,flush=True)
best=int(np.argmin([x['score'] for x in trials]));W=candidates[best];changed=np.max(abs(W-oldW),axis=1)>1e-5
# Apply selected candidates in batches grouped by identical weight vectors.
for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
groups=[mesh.vertex_groups.new(name=n) for n in B]
quant=np.rint(W*100000).astype(np.int32);quant[np.arange(N),quant.argmax(axis=1)]+=100000-quant.sum(axis=1)
unique,index=np.unique(quant,axis=0,return_inverse=True)
for k,row in enumerate(unique):
 verts=np.flatnonzero(index==k).tolist()
 for j in np.flatnonzero(row):groups[j].add(verts,float(row[j])/100000,'REPLACE')
print('WEIGHTS_APPLIED',int(changed.sum()),'vertices',flush=True)
(R/'Reports/WeightTrials.json').write_text(json.dumps({'trials':trials,'selected':trials[best],'changed_vertices':int(changed.sum()),'test_pose_count':len(sample),'measured_edges':int(measured.sum()),'method':'Joint-local topology diffusion, max 4 influences, selected by stretch/compression score across original and new poses.','skeleton_changed':False,'geometry_changed':False},indent=2)+'\n')
np.savez_compressed(R/'Reports/ExperimentalMesh.npz',points=P,weights=W,names=B,edges=E,part=vpart,rest=np.array([np.array(rest[n]) for n in B]))
# Save all original and experimental Actions in one editable file.
rig.animation_data.action=bpy.data.actions['AN_EXP_Stalk'];scene.frame_start=1;scene.frame_end=85;scene.frame_set(1)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Penance_AnimationExperiments.blend'),compress=True)
(R/'Reports/ClipManifest.json').write_text(json.dumps(CLIPS,indent=2)+'\n')
for name,arr in poses.items():np.savez_compressed(R/'Reports'/(name+'_poses.npz'),matrices=arr,names=B)
# Export experimental mesh separately on the existing reference skeleton.
rig.animation_data.action=None;reset();bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);mesh.select_set(True);bpy.context.view_layer.objects.active=rig
opts=dict(use_selection=True,add_leaf_bones=False,use_armature_deform_only=False,axis_forward='-Y',axis_up='Z',apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',bake_space_transform=False,path_mode='RELATIVE')
bpy.ops.export_scene.fbx(filepath=str(R/'FBX/SK_Penance_Experimental.fbx'),object_types={'ARMATURE','MESH'},bake_anim=False,**opts)
mesh.select_set(False)
for name,s in CLIPS.items():
 rig.animation_data.action=bpy.data.actions[name];scene.frame_start=1;scene.frame_end=s['frames']+1;scene.frame_set(1)
 bpy.ops.export_scene.fbx(filepath=str(R/'FBX'/(name+'.fbx')),object_types={'ARMATURE'},bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_simplify_factor=0.,**opts)
print('EXPERIMENTS_SAVED',flush=True)
