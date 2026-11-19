"""Native-speed motion comparisons and a same-motion rig before/after."""
from pathlib import Path
import subprocess,json,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'Previews';D=Path('/Users/amritladhar/Documents/ChatGPT/Penance/Advanced_Enemy_Animations');font='/System/Library/Fonts/Supplemental/Arial.ttf'
def run(args):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y']+list(map(str,args)),check=True)
def encode_original(name,frames,view='Side'):
 target=O/(name+'_'+view+'.mp4')
 if not target.exists():run(['-framerate',30,'-i',O/'Frames'/name/view/'%04d.png','-frames:v',frames,'-c:v','libx264','-preset','fast','-crf',18,'-pix_fmt','yuv420p','-movflags','+faststart',target])
 return target
walk=[encode_original('AN_Penance_StalkWalk',60)]+[O/(n+'_Side.mp4') for n in ['AN_EXP_Stalk','AN_EXP_Limp','AN_EXP_Heavy','AN_EXP_Chase']]
attacks=[encode_original('AN_Penance_Attack',45)]+[O/(n+'_Side.mp4') for n in ['AN_EXP_Lunge','AN_EXP_Overhead','AN_EXP_Sweep']]
def comparison(dest,files,titles,footer,width,height,duration=12,hold=False):
 if dest.exists():shutil.copy2(dest,D/dest.name);return
 n=len(files);W=n*width;H=height+100;label=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(label);d.rectangle((0,0,W,60),fill='#121920');d.rectangle((0,H-40,W,H),fill='#121920')
 for i,t in enumerate(titles):d.text((i*width+14,17),t,font=ImageFont.truetype(font,20),fill='#e0e6ec')
 d.text((14,H-29),footer,font=ImageFont.truetype(font,17),fill='#cbd5df');labels=dest.with_suffix('.png');label.save(labels);cmd=[]
 for f in files:
  if not hold:cmd+=['-stream_loop',-1]
  cmd+=['-i',f]
 cmd+=['-loop',1,'-i',labels];parts=[]
 for i in range(n):
  parts.append(f'[{i}:v]scale={width}:{height},setsar=1'+(',tpad=stop_mode=clone:stop_duration=4,trim=duration=4' if hold else '')+f'[v{i}]')
 parts.append(''.join(f'[v{i}]' for i in range(n))+f'hstack=inputs={n},pad={W}:{H}:0:60:color=0x121920[base]');parts.append(f'[base][{n}:v]overlay=0:0:shortest=1[out]')
 cycle=dest.with_name(dest.stem+'_Cycle.mp4') if hold else dest
 run(cmd+['-filter_complex',';'.join(parts),'-map','[out]','-t',4 if hold else duration,'-an','-c:v','libx264','-preset','fast','-crf',18,'-pix_fmt','yuv420p','-r',30,'-movflags','+faststart',cycle])
 if hold:run(['-stream_loop',2,'-i',cycle,'-c','copy','-movflags','+faststart',dest]);cycle.unlink()
 shutil.copy2(dest,D/dest.name);print('COMPARISON_READY',dest.name,flush=True)
comparison(O/'Comparison_Walking.mp4',walk,['Original | 35 cm/s','Stalk | 30 cm/s','Limp | 34 cm/s','Heavy | 52 cm/s','Chase | 115 cm/s'],'Original mesh and motion at left; revised mesh and new motions at right. All native speed, 30 FPS, in place.',360,480)
comparison(O/'Comparison_Attacks.mp4',attacks,['Original | hit 0.70 s','Lunge | hit 0.60 s','Overhead | hit 1.10 s','Sweep | hit 0.80 s'],'Anticipation starts together. Clips play at native speed, then hold their recovery pose before repeating.',450,600,hold=True)
before=O/'BeforeWeights/AN_EXP_Overhead/ThreeQuarter';beforemp4=O/'OriginalSkin_Overhead.mp4'
if not beforemp4.exists():run(['-framerate',30,'-i',before/'%04d.png','-frames:v',78,'-c:v','libx264','-preset','fast','-crf',18,'-pix_fmt','yuv420p','-movflags','+faststart',beforemp4])
comparison(O/'Comparison_Rig_Deformation.mp4',[beforemp4,O/'AN_EXP_Overhead_ThreeQuarter.mp4'],['Original mesh + skin weights','Refined mesh + skin weights'],'Identical overhead Action, camera, scale and 30 FPS playback. Only mesh fit and skinning differ.',600,800,duration=10.4)
