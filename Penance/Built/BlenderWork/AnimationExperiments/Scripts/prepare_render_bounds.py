"""Fit one consistent full-body camera rig across every sample of all seven clips."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];manifest=json.loads((R/'Reports/ClipManifest.json').read_text());scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH')
target=Vector((0,-25,115));views={'Front':(0,-650,145),'Side':(650,-25,145),'ThreeQuarter':(440,-600,230)};basis={}
for n,loc in views.items():
 q=(target-Vector(loc)).to_track_quat('-Z','Y');basis[n]=(q@Vector((1,0,0)),q@Vector((0,1,0)))
extents={n:[0,0] for n in views}
for n,s in manifest.items():
 rig.animation_data.action=bpy.data.actions[n]
 for f in range(1,s['frames']+2):
  scene.frame_set(f);bpy.context.view_layer.update();ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
  for corner in ev.bound_box:
   p=ev.matrix_world@Vector(corner)-target
   for view,(right,up) in basis.items():extents[view][0]=max(extents[view][0],abs(p.dot(right)));extents[view][1]=max(extents[view][1],abs(p.dot(up)))
scale=max(max(x*2/(600/800),y*2) for x,y in extents.values())*1.08
report={'target':list(target),'views':views,'ortho_scale':scale,'projected_half_extents':extents,'width':600,'height':800,'fps':30,'fit':'Every frame of all seven Actions; 8 percent framing margin.'}
(R/'Reports/RenderCameras.json').write_text(json.dumps(report,indent=2)+'\n');print('CAMERAS_FIT',json.dumps(report),flush=True)
