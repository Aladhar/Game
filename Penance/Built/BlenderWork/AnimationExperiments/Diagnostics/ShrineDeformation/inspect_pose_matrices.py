"""Read-only evaluation; no scene or asset is saved."""
import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');scene=bpy.context.scene
out={};allnames=[b.name for b in rig.data.bones]
for action in bpy.data.actions:
 if not action.name.startswith(('AN_EXP_','AN_Penance_')):continue
 rig.animation_data_create();rig.animation_data.action=action;start,end=map(round,action.frame_range);m=[];angles=[]
 for f in range(start,end+1):
  scene.frame_set(f);bpy.context.view_layer.update();m.append(np.array([np.array(b.matrix) for b in rig.pose.bones]));angles.append({b.name:list(b.rotation_quaternion) for b in rig.pose.bones if b.name.startswith('ornament_')})
 np.savez_compressed(O/(action.name+'_Evaluated.npz'),matrices=np.array(m),names=allnames)
 out[action.name]={'start':start,'end':end,'frames':len(m),'ornament_local_quaternions':angles}
(O/'ActionEvaluation.json').write_text(json.dumps(out,indent=2)+'\n');print('READ_ONLY_POSE_EVALUATION_COMPLETE',list(out),flush=True)
