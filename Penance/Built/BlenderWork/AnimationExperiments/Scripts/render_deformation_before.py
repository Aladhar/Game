"""Same new overhead motion, original mesh/weights: isolate rig refinements."""
import bpy,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1];q=np.load(R/'Reports/SourceMesh.npz');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh.data.vertices.foreach_set('co',q['points'].astype(np.float32).ravel());mesh.data.update();W=q['weights'];names=list(q['names'])
for g in list(mesh.vertex_groups):mesh.vertex_groups.remove(g)
groups=[mesh.vertex_groups.new(name=n) for n in names];quant=np.rint(W*100000).astype(np.int32);quant[np.arange(len(W)),quant.argmax(axis=1)]+=100000-quant.sum(axis=1);unique,index=np.unique(quant,axis=0,return_inverse=True)
for k,row in enumerate(unique):
 ids=np.flatnonzero(index==k).tolist()
 for j in np.flatnonzero(row):groups[j].add(ids,float(row[j])/100000,'REPLACE')
p=R/'Scripts/render_previews.py';s=p.read_text().replace("views=setup['views'];","views={'ThreeQuarter':setup['views']['ThreeQuarter']};").replace("directory=R/'Previews'/('Review' if mode=='review' else 'Frames')/name/view","directory=R/'Previews'/'BeforeWeights'/name/view").replace("'RenderProvenance_'+mode", "'BeforeWeights_RenderProvenance_'+mode")
exec(compile(s,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
