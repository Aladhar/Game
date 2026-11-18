"""Read-only source audit. Run with Blender --background --python this_file."""
import bpy, json, hashlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent
report = {}
for name in ['Penance_Animated.blend', 'Penance_Rigged_Repaired.blend', 'Penance_Rigged_Final.blend']:
    path = SOURCE / name
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rig = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    mesh = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    p = np.array([v.co[:] for v in mesh.data.vertices])
    names = [g.name for g in mesh.vertex_groups]
    w = np.zeros((len(p), len(names)))
    for v in mesh.data.vertices:
        for g in v.groups: w[v.index,g.group] = g.weight
    entry = {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'vertices':len(p),'faces':len(mesh.data.polygons),'height_cm':float(np.ptp(p[:,2])),
      'weight_sum_max_error':float(np.max(abs(w.sum(axis=1)-1))),
      'unweighted_vertices':int(np.sum(w.sum(axis=1)<.001)),
      'max_influences':int(np.max(np.sum(w>1e-6,axis=1))),
      'bones':{b.name:{'parent':b.parent.name if b.parent else None,'head':list(b.head_local),'tail':list(b.tail_local),'matrix':np.array(b.matrix_local).tolist()} for b in rig.data.bones},
      'actions':{a.name:{'range':list(a.frame_range)} for a in bpy.data.actions},
      'attributes':[a.name for a in mesh.data.attributes],
      'modifiers':[{'name':m.name,'type':m.type} for m in mesh.modifiers],
      'constraints':{b.name:[c.type for c in b.constraints] for b in rig.pose.bones if b.constraints},
      'materials':[m.name for m in mesh.data.materials]}
    report[name]=entry
    if name=='Penance_Animated.blend':
        np.savez_compressed(ROOT/'Reports/SourceMesh.npz',points=p,weights=w,names=names,
                            edges=np.array([e.vertices[:] for e in mesh.data.edges]))
    print('SOURCE_AUDIT',name,json.dumps({k:v for k,v in entry.items() if k not in ['bones']}),flush=True)
(ROOT/'Reports/SourceInspection.json').write_text(json.dumps(report,indent=2)+'\n')
