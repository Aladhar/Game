"""Render real Blender motion at authored speed, consistent full-body cameras.
Modes after --: review | videos. Optional action name limits the job.
"""
import bpy,sys,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['review']
mode=args[0];manifest=json.loads((R/'Reports/ClipManifest.json').read_text());scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE')
scene.render.engine='BLENDER_WORKBENCH';scene.render.fps=30;scene.render.fps_base=1
s=scene.display.shading;s.light='STUDIO';s.color_type='TEXTURE';s.show_cavity=True;s.cavity_type='BOTH';s.show_shadows=True;s.show_specular_highlight=True;s.background_type='WORLD'
scene.world.color=(.075,.085,.10);scene.view_settings.view_transform='Standard';scene.render.resolution_x=600;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
scene.display.render_aa='16'
cam=bpy.data.objects.new('Review_Camera',bpy.data.cameras.new('Review_Lens'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=390
bpy.ops.mesh.primitive_plane_add(size=3000,location=(0,0,-.15));floor=bpy.context.object;floor.name='Review_Floor';floor.color=(.20,.23,.27,1)
# A sparse floor grid provides foot-contact and scale cues without hiding soles.
for x in range(-150,151,50):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,0,-.10));o=bpy.context.object;o.scale=(.20,300,.04);o.color=(.29,.32,.36,1)
for y in range(-200,201,50):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,y,-.10));o=bpy.context.object;o.scale=(300,.20,.04);o.color=(.29,.32,.36,1)
setup=json.loads((R/'Reports/RenderCameras.json').read_text())
views=setup['views'];cam.data.ortho_scale=setup['ortho_scale'];target=Vector(setup['target'])
clips=dict(manifest)
if mode=='originals':
 clips={}
 for n,frames in [('AN_Penance_StalkWalk',60),('AN_Penance_Chase',30),('AN_Penance_Attack',45)]:clips[n]={'frames':frames,'loop':n!='AN_Penance_Attack'}
if len(args)>1:clips={args[1]:clips[args[1]]}
for name,spec in clips.items():
 rig.animation_data.action=bpy.data.actions[name]
 cache_root=R/'Previews'/('Review' if mode=='review' else 'Frames')/name
 fingerprint={'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'camera_sha256':hashlib.sha256(json.dumps(setup,sort_keys=True).encode()).hexdigest()}
 stamp=cache_root/'.render_source.json'
 if not stamp.exists() or json.loads(stamp.read_text())!=fingerprint:
  if cache_root.exists():shutil.rmtree(cache_root)
  cache_root.mkdir(parents=True,exist_ok=True);stamp.write_text(json.dumps(fingerprint,indent=2)+'\n')
 for view,location in views.items():
  if name.startswith('AN_Penance_') and view=='Front':continue
  cam.location=location;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
  directory=R/'Previews'/('Review' if mode=='review' else 'Frames')/name/view;directory.mkdir(parents=True,exist_ok=True)
  if mode=='review':
   selected=[1,round(spec['frames']*.25)+1,round(spec['frames']*.5)+1,round(spec['frames']*.75)+1] if spec['loop'] else [1,spec['anticipation'],spec['impact'],spec['recovery']]
  else:selected=range(1,spec['frames']+1)
  for f in selected:
   dest=directory/f'{f:04}.png'
   if dest.exists():continue
   scene.frame_set(f);scene.render.filepath=str(dest);bpy.ops.render.render(write_still=True)
  print('RENDERED',name,view,len(selected),flush=True)
(R/'Reports'/('RenderProvenance_'+mode+'.json')).write_text(json.dumps({'source':bpy.data.filepath,'source_sha256':hashlib.sha256(Path(bpy.data.filepath).read_bytes()).hexdigest(),'cameras':setup,'rendered_actions':list(clips)},indent=2)+'\n')
print('PREVIEWS_COMPLETE',mode,flush=True)
