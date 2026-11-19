"""Encode completed render folders. Safe to rerun as later clips finish."""
from pathlib import Path
import subprocess,json,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];out=R/'Previews';delivery=Path('/Users/amritladhar/Documents/ChatGPT/Penance/Advanced_Enemy_Animations');delivery.mkdir(parents=True,exist_ok=True)
manifest=json.loads((R/'Reports/ClipManifest.json').read_text());views=['Front','Side','ThreeQuarter'];font='/System/Library/Fonts/Supplemental/Arial.ttf'
labels={'Stalk':'Unsettling Stalk Walk','Limp':'Limping Walk','Heavy':'Heavy Walk','Chase':'Aggressive Chase','Lunge':'Forward Lunge','Overhead':'Heavy Overhead Strike','Sweep':'Wide Sweeping Attack'}
def run(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y']+list(map(str,args)),check=True)
results={}
for index,(name,s) in enumerate(manifest.items(),1):
 short=name.removeprefix('AN_EXP_');title=labels[short];ready=all((out/'Frames'/name/v/f'{s["frames"]:04}.png').exists() for v in views)
 if not ready:print('WAITING_FOR_RENDER',name,flush=True);continue
 files=[]
 for view in views:
  dest=out/f'{name}_{view}.mp4';files.append(dest)
  if not dest.exists():run(['-framerate',30,'-start_number',1,'-i',out/'Frames'/name/view/'%04d.png','-frames:v',s['frames'],'-c:v','libx264','-crf',18,'-preset','fast','-pix_fmt','yuv420p','-movflags','+faststart',dest])
 final=out/f'{index:02}_{short}.mp4'
 if not final.exists():
  label=Image.new('RGBA',(1800,900),(0,0,0,0));d=ImageDraw.Draw(label);d.rectangle((0,0,1800,60),fill='#121920');d.rectangle((0,860,1800,900),fill='#121920')
  for i,v in enumerate(['FRONT','SIDE','THREE-QUARTER']):d.text((i*600+22,17),v,font=ImageFont.truetype(font,23),fill='#cbd5df')
  status=f'{title}   |   30 FPS   |   {s["frames"]/30:.2f} s cycle'
  status+=f'   |   In place: {s["speed"]:.0f} cm/s' if s['loop'] else f'   |   Impact: {(s["impact"]-1)/30:.2f} s   |   Recovery shown'
  d.text((22,870),status,font=ImageFont.truetype(font,21),fill='#e3e9ef');header=out/(name+'_Labels.png');label.save(header)
  cycle=out/(name+'_Cycle.mp4');cmd=[]
  for f in files:cmd+=['-i',f]
  cmd+=['-loop',1,'-i',header]
  graph='[0:v][1:v][2:v]hstack=inputs=3,pad=1800:900:0:60:color=0x121920[base];[base][3:v]overlay=0:0:shortest=1'
  if not s['loop']:graph+=',tpad=stop_mode=clone:stop_duration=0.8'
  cmd+=['-filter_complex',graph,'-an','-c:v','libx264','-preset','fast','-crf',18,'-pix_fmt','yuv420p','-r',30,'-movflags','+faststart',cycle];run(cmd)
  repeats=5 if short=='Chase' else 2
  run(['-stream_loop',repeats,'-i',cycle,'-c','copy','-movflags','+faststart',final])
  cycle.unlink()
 for f in files+[final]:shutil.copy2(f,delivery/f.name)
 results[name]={'mp4':str(final),'delivery':str(delivery/final.name),'views':[str(f) for f in files]};print('MP4_READY',str(delivery/final.name),flush=True)
(out/'VideoDeliverables.json').write_text(json.dumps(results,indent=2)+'\n')
