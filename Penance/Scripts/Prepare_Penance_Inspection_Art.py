"""Deterministic source art for a real two-sided enamel board; no screenshot UI."""
from pathlib import Path
import random,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont,ImageFilter
root=Path(__file__).resolve().parents[1];out=root/'SourceArt/Inspection';out.mkdir(exist_ok=True)
rng=np.random.default_rng(1958);random.seed(1958);W,H=1640,1200
font='/Users/Shared/Epic Games/UE_5.7/Engine/Content/Slate/Fonts/Roboto-BoldCondensed.ttf'
def paint(back=False):
 y,x=np.mgrid[:H,:W];small=Image.fromarray(rng.integers(0,255,(40,55),dtype=np.uint8)).resize((W,H),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(12));noise=np.asarray(small)/255
 edge=np.minimum.reduce([x/W,(W-1-x)/W,y/H,(H-1-y)/H]);wear=np.clip((.055-edge)/.055,0,1)
 rgb=np.array([83,80,70] if back else[208,195,159])[None,None,:]+(noise[...,None]-.5)*25+rng.normal(0,1.6,(H,W,1))
 rgb=rgb*(1-wear[...,None]*.3);im=Image.fromarray(np.uint8(np.clip(rgb,0,255)),'RGB');d=ImageDraw.Draw(im)
 if not back:
  d.rounded_rectangle((46,42,W-46,H-42),30,outline='#6c2921',width=9);d.rectangle((70,70,W-70,320),fill='#702b22')
  def txt(v,xy,size,fill,anchor='mm'):d.text(xy,v,font=ImageFont.truetype(font,size),fill=fill,anchor=anchor)
  txt('LAST STOP',(W/2,165),140,'#dfcda2');txt('G A S O L I N E',(W/2,270),50,'#cdbd98')
  for row,(name,price) in enumerate([('REGULAR','3.29'),('PLUS','3.49'),('PREMIUM','3.59')]):
   Y=420+row*228;txt(name,(305,Y+20),62,'#502c24');d.rectangle((600,Y-65,1510,Y+112),fill='#292b26',outline='#8d8268',width=3);txt(price,(1010,Y+23),167,'#d7bd7c');txt('9',(1432,Y-10),60,'#d7bd7c');d.line((1408,Y+28,1465,Y+28),fill='#d7bd7c',width=2);txt('10',(1434,Y+57),34,'#c5b184')
  txt('CASH  /  PER GALLON',(820,1110),33,'#685c46')
 else:
  for i in range(130):
   Y=random.randrange(30,H-30);d.line((25,Y,W-25,Y),fill=tuple(random.randrange(65,95) for _ in range(3)),width=1)
  d.rectangle((520,455,1120,765),fill='#b7ac89',outline='#4a473d',width=5)
  for v,Y,size in [('LAST STOP GAS',510,48),('PRICE BOARD  /  SERVICE PANEL',575,30),('ENAMELLED STEEL',630,26),('FASTEN SECURELY BEFORE DISPLAY',705,22)]:d.text((820,Y),v,font=ImageFont.truetype(font,size),fill='#393d33',anchor='mm')
  for X in(325,1315):d.rectangle((X-25,50,X+25,H-50),fill='#5e5d52',outline='#757467',width=4)
 # Chipped perimeter enamel and fine wear, held to restrained intact six-month abandonment.
 for i in range(2100):
  X=random.randrange(W);Y=random.randrange(H);e=min(X,W-1-X,Y,H-1-Y)
  if e>55 and random.random()>.025:continue
  r=random.choice([1,1,2,3,5,7]);d.ellipse((X-r,Y-r,X+r,Y+r),fill=random.choice(['#80613c','#66513a','#9d8050','#453f34']))
 for i in range(70):
  X=random.randrange(80,W-80);Y=random.randrange(60,H-60);d.line((X,Y,X+random.randrange(4,80),Y+random.randrange(-15,15)),fill='#a5987a' if not back else '#9a9785',width=1)
 im.save(out/('GasBoard_Back.png' if back else 'GasBoard_Front.png'));return im
front=paint();paint(True);front.resize((328,240),Image.Resampling.LANCZOS).save(out/'GasBoard_Thumbnail.png')
noise=rng.integers(0,256,(256,256),dtype=np.uint8);Image.fromarray(noise).save(out/'UI_Grain.png')
print('Inspection artwork saved')
