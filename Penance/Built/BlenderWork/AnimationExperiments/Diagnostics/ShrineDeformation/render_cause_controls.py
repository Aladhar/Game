"""Controlled diagnostic renders. Mesh/Actions are never saved or exported."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;R=O.parents[1];bpy.ops.wm.open_mainfile(filepath=str(R/'Checkpoints/BeforeStraightShrine/Penance_AnimationExperiments.blend'));q=np.load(R/'Checkpoints/BeforeStraightShrine/ExperimentalMesh.npz');source=np.load(R/'Reports/SourceMesh.npz');P=q['points'];P0=source['points'];W=q['weights'];B=list(q['names']);rest=q['rest'];inv=np.linalg.inv(rest);region=q['part']==1;mount=B.index('shrine_mount');orn=[i for i,n in enumerate(B) if n.startswith('ornament_')]
scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH');rig.animation_data.action=bpy.data.actions['AN_EXP_Chase'];scene.frame_set(9);bpy.context.view_layer.update();e=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());actual=np.empty(P.size,np.float32);e.data.vertices.foreach_get('co',actual);actual=actual.reshape(-1,3)
matrices=np.load(O/'AN_EXP_Chase_Evaluated.npz')['matrices'][8];skin=np.einsum('bij,bjk->bik',matrices,inv,optimize=True)
top=np.argsort(W,axis=1)[:,-4:];values=np.take_along_axis(W,top,axis=1)
def deform(points,transforms):
 h=np.column_stack((points,np.ones(len(points))));return np.einsum('nk,nkij,nj->ni',values,transforms[top][:,:,:3,:],h,optimize=True)
current=deform(P,skin);error=float(np.max(np.linalg.norm(current-actual,axis=1)));assert error<.002,error
allidentity=np.broadcast_to(np.eye(4),skin.shape);restored=P.copy();restored[region]=P0[region];neutral=skin.copy();neutral[orn]=skin[mount];rigid=deform(restored,skin);rigid[region]=np.column_stack((P0[region],np.ones(region.sum())))@skin[mount,:3,:].T
cases={'01_OriginalNeutral':P0,'02_CurrentNeutral':P,'03_CurrentChase':current,'04_OriginalGeometryCurrentWeights':deform(restored,skin),'05_CurrentGeometryNoOrnamentMotion':deform(P,neutral),'06_OriginalGeometryRigidShrine':rigid}
for mod in list(mesh.modifiers):
 if mod.type=='ARMATURE':mesh.modifiers.remove(mod)
rig.hide_render=True;mesh.parent=None
scene.render.engine='BLENDER_WORKBENCH';s=scene.display.shading;s.light='STUDIO';s.color_type='TEXTURE';s.show_cavity=True;s.cavity_type='BOTH';s.show_shadows=True;s.background_type='WORLD';scene.world.color=(.075,.085,.10);scene.view_settings.view_transform='Standard';scene.render.resolution_x=600;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.display.render_aa='16'
cam=bpy.data.objects.new('Diagnostic_Camera',bpy.data.cameras.new('Diagnostic_Lens'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=400;cam.location=(650,-15,145);cam.rotation_euler=(Vector((0,-15,115))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.ops.mesh.primitive_plane_add(size=3000,location=(0,0,-.15));bpy.context.object.color=(.20,.23,.27,1)
for name,points in cases.items():
 mesh.data.vertices.foreach_set('co',points.astype(np.float32).ravel());mesh.data.update();bpy.context.view_layer.update();scene.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
metrics=json.loads((O/'RootCauseMetrics.json').read_text())
for name,spec in metrics['clips'].items():
 if not name.startswith('AN_EXP_'):continue
 m=np.load(O/(name+'_Evaluated.npz'))['matrices'][spec['peak_frame']-1];transforms=np.einsum('bij,bjk->bik',m,inv,optimize=True);points=deform(P,transforms);mesh.data.vertices.foreach_set('co',points.astype(np.float32).ravel());mesh.data.update();bpy.context.view_layer.update();scene.render.filepath=str(O/(name+'_Peak.png'));bpy.ops.render.render(write_still=True)
(O/'DiagnosticRenderVerification.json').write_text(json.dumps({'maximum_cpu_skinning_vs_blender_error_cm':error,'control_pose':'AN_EXP_Chase frame 9','no_asset_saved':True,'cases':list(cases)},indent=2)+'\n');print('CAUSE_CONTROLS_RENDERED',error,flush=True)
