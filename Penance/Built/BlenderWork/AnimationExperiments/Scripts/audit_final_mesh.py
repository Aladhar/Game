"""Compare source and final asset data independently of the animation authoring."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;rig=next(o for o in scene.objects if o.type=='ARMATURE');mesh=next(o for o in scene.objects if o.type=='MESH');mesh.data.calc_loop_triangles();p=np.array([v.co[:] for v in mesh.data.vertices]);tri=np.array([t.vertices[:] for t in mesh.data.loop_triangles]);names=[g.name for g in mesh.vertex_groups];w=np.zeros((len(p),len(names)))
 for v in mesh.data.vertices:
  for g in v.groups:w[v.index,g.group]=g.weight
 uv={}
 for layer in mesh.data.uv_layers:
  buffer=np.empty(len(mesh.data.loops)*2,np.float32);layer.uv.foreach_get('vector',buffer);uv[layer.name]=hashlib.sha256(buffer.tobytes()).hexdigest()
 images={i.name:hashlib.sha256(i.packed_file.data).hexdigest() for i in bpy.data.images if i.packed_file}
 _,key=np.unique(np.rint(p*10000).astype(np.int64),axis=0,return_inverse=True);edges=np.sort(key[tri[:,[0,1,1,2,2,0]]].reshape(-1,2),axis=1);unique,counts=np.unique(edges,axis=0,return_counts=True);cross=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]);area=np.linalg.norm(cross,axis=1)*.5
 return {'points':p,'triangles':tri,'uv_hashes':uv,'packed_images':images,'bones':{b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local)) for b in rig.data.bones},'scales':[list(mesh.scale),list(rig.scale)],'topology':{'vertices':len(p),'triangles':len(tri),'boundary_edges':int(np.sum(counts==1)),'nonmanifold_edges':int(np.sum(counts>2)),'near_zero_area_faces':int(np.sum(area<1e-8))},'names':names,'weights':w}
source=read(R.parent/'Penance_Animated.blend');final=read(R/'Penance_AnimationExperiments.blend');part=np.load(R/'Reports/ExperimentalMesh.npz')['part'];assert np.array_equal(source['triangles'],final['triangles']);assert source['uv_hashes']==final['uv_hashes'];assert source['packed_images']==final['packed_images'];assert source['bones'].keys()==final['bones'].keys()
for n in source['bones']:
 a,b=source['bones'][n],final['bones'][n];assert a[0]==b[0] and np.max(abs(a[1]-b[1]))<1e-7,(n,'Reference changed')
assert max(abs(x-1) for a in final['scales'] for x in a)<1e-6
assert abs(np.ptp(final['points'][:,2])-230)<.001
assert np.max(abs(source['points'][part!=1]-final['points'][part!=1]))<1e-6
assert final['topology']['boundary_edges']==0
assert final['topology']['near_zero_area_faces']<=source['topology']['near_zero_area_faces']
assert max(np.count_nonzero(final['weights'],axis=1))<=4
assert np.max(abs(final['weights'].sum(axis=1)-1))<1e-6
report={'geometric_weld_grid_cm':0.0001,'zero_area_threshold_cm2':1e-8,'source_topology':source['topology'],'final_topology':final['topology'],'triangles_and_vertex_order_unchanged':True,'UVs_and_packed_textures_unchanged':True,'skeleton_hierarchy_and_reference_unchanged':True,'non_drape_geometry_unchanged':True,'height_cm':float(np.ptp(final['points'][:,2])),'object_scales':final['scales'],'maximum_weight_sum_error':float(np.max(abs(final['weights'].sum(axis=1)-1))),'root_weight_max':float(final['weights'][:,final['names'].index('root')].max()),'max_influences':int(np.max(np.count_nonzero(final['weights'],axis=1))),'changed_weight_vertices':int(np.sum(np.max(abs(final['weights']-source['weights']),axis=1)>1e-5)),'changed_geometry_vertices':int(np.sum(np.linalg.norm(final['points']-source['points'],axis=1)>1e-6)),'maximum_geometry_adjustment_cm':float(np.linalg.norm(final['points']-source['points'],axis=1).max())}
(R/'Reports/FinalMeshAudit.json').write_text(json.dumps(report,indent=2)+'\n');print('FINAL_MESH_AUDIT_PASSED',json.dumps(report),flush=True)
