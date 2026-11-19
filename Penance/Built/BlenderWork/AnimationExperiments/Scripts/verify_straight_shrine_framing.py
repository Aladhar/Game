import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];setup=json.loads((R/'Reports/RenderCameras.json').read_text());manifest=json.loads((R/'Reports/ClipManifest.json').read_text());scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH');target=Vector(setup['target']);basis={}
for name,location in setup['views'].items():
 q=(target-Vector(location)).to_track_quat('-Z','Y');basis[name]=(q@Vector((1,0,0)),q@Vector((0,1,0)))
maximum={n:[0,0] for n in basis}
for n,s in manifest.items():
 rig.animation_data.action=bpy.data.actions[n]
 for f in range(1,s['frames']+2):
  scene.frame_set(f);bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());p=np.empty(len(ev.data.vertices)*3,np.float32);ev.data.vertices.foreach_get('co',p);p=p.reshape(-1,3)-np.array(target)
  for view,(right,up) in basis.items():maximum[view][0]=max(maximum[view][0],float(abs(p@np.array(right)).max()));maximum[view][1]=max(maximum[view][1],float(abs(p@np.array(up)).max()))
limitx=setup['ortho_scale']*.5*setup['width']/setup['height'];limity=setup['ortho_scale']*.5
assert max(a[0] for a in maximum.values())<limitx and max(a[1] for a in maximum.values())<limity,(maximum,limitx,limity)
(R/'Reports/StraightShrineRenderFraming.json').write_text(json.dumps({'projected_half_extents':maximum,'horizontal_limit':limitx,'vertical_limit':limity,'all_frames_fit_original_cameras':True},indent=2)+'\n');print('STRAIGHT_SHRINE_ALL_RENDER_FRAMES_FIT',maximum,limitx,limity)
