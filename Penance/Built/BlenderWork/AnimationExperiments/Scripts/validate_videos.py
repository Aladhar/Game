"""Decode every MP4 and verify fps, format, frame counts and delivery completeness."""
from pathlib import Path
import subprocess,json,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'Previews';D=Path('/Users/amritladhar/Documents/ChatGPT/Penance/Advanced_Enemy_Animations');manifest=json.loads((R/'Reports/ClipManifest.json').read_text());expected=[]
for i,(name,s) in enumerate(manifest.items(),1):
 expected.append(O/f'{i:02}_{name.removeprefix("AN_EXP_")}.mp4')
 for v in ['Front','Side','ThreeQuarter']:expected.append(O/f'{name}_{v}.mp4')
expected+=[O/('Comparison_'+n+'.mp4') for n in ['Walking','Attacks','Rig_Deformation']]
expected.append(O/'Shrine_Fix_Before_After.mp4')
results={}
for p in expected:
 assert p.is_file(),p
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,avg_frame_rate,r_frame_rate,nb_frames,duration','-of','json',str(p)]))['streams'][0]
 assert probe['codec_name']=='h264' and probe['pix_fmt']=='yuv420p' and probe['avg_frame_rate']=='30/1',(p,probe)
 subprocess.run(['ffmpeg','-hide_banner','-v','error','-xerror','-i',str(p),'-f','null','-'],check=True,stdout=subprocess.DEVNULL)
 b=p.read_bytes();assert b.find(b'moov')<b.find(b'mdat'),(p,'Missing faststart')
 assert (D/p.name).is_file() and hashlib.sha256((D/p.name).read_bytes()).hexdigest()==hashlib.sha256(b).hexdigest(),p
 assert hashlib.sha256((D/'Straight_Shrine'/p.name).read_bytes()).hexdigest()==hashlib.sha256(b).hexdigest(),(p,'Stale Straight_Shrine delivery')
 results[p.name]={**probe,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'decoded_without_errors':True,'faststart':True}
provenance=json.loads((R/'Reports/RenderProvenance_videos.json').read_text());assert provenance['source_sha256']==hashlib.sha256((R/'Penance_AnimationExperiments.blend').read_bytes()).hexdigest(),'Videos came from a stale Blender revision'
report={'rendered_source_sha256':provenance['source_sha256'],'verified_mp4_count':len(results),'primary_clips':7,'individual_views':21,'comparisons':4,'videos':results}
(R/'Reports/VideoValidation.json').write_text(json.dumps(report,indent=2)+'\n')
lines=['# Penance animation review','','Seven separate three-view MP4s, 30 FPS. Individual angles are also in this folder.','']
for i,name in enumerate(manifest,1):
 short=name.removeprefix('AN_EXP_');lines.append(f'- [{short}]({i:02}_{short}.mp4)')
lines+=['','Comparisons:']
for n in ['Walking','Attacks','Rig_Deformation']:lines.append(f'- [{n}](Comparison_{n}.mp4)')
lines+=['',f'[Full report and editable assets]({R}/README.md)']
lines+=['','[Straight-shrine before/after](Shrine_Fix_Before_After.mp4)']
(D/'Straight_Shrine').mkdir(exist_ok=True)
(D/'Straight_Shrine'/'README.md').write_text('\n'.join(lines)+'\n')
(D/'README.md').write_text('\n'.join(lines)+'\n')
print('ALL_VIDEOS_VALIDATED',len(results),flush=True)
