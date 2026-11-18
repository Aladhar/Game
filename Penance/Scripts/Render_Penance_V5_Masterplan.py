import sys,math,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,'Scripts');import Penance_Town_V5_Design as p
from shapely.geometry import Polygon,LineString
out=Path('Docs/V5');out.mkdir(exist_ok=True)
S=3.7;ox=75;oy=190;W=1926;H=1970
im=Image.new('RGB',(W,H),'#101d1d');d=ImageDraw.Draw(im)
font='/System/Library/Fonts/Supplemental/Arial.ttf';bold='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
f=lambda n:ImageFont.truetype(font,n);bf=lambda n:ImageFont.truetype(bold,n)
def xy(x,y):return(ox+x*S,oy+(440-y)*S)
def line(points,color,width):d.line([xy(*q[:2]) for q in points],fill=color,width=max(1,round(width*S)),joint='curve')
def label(x,y,s,size=17,col='#f0ead6'):
 X,Y=xy(x,y);d.text((X,Y),s,font=bf(size),anchor='mm',fill=col,stroke_width=2,stroke_fill='#24322c')
d.text((75,45),'PENANCE  /  WORLD BLOCKOUT V5',font=bf(24),fill='#aabfb1')
d.text((75,82),'The crossing that built the town',font=bf(45),fill='#e9e8df')
d.text((75,143),'480 × 440 m • North ↑ • Actual saved layout • 14 houses + civic, commercial and ridge districts',font=f(23),fill='#c0c9b9')
t=p.Terrain()
for y in range(0,440,4):
 for x in range(0,480,4):
  z=t.surface(x+2,y+2);c=tuple(round(q+z*v) for q,v in [(64,.8),(85,.7),(64,.3)]);X,Y=xy(x,y+4);d.rectangle((X,Y,X+4*S+1,Y+4*S+1),fill=c)
creek=[(x,p.creek_y(x)) for x in range(481)];line(creek,'#335c63',16);line(creek,'#5597a3',7)
for name,points in p.PATHS.items():line(points,'#a4ab8e',2.5)
for name,points in p.DRIVES.items():line(points,'#a7a493',3.2)
for name,r in p.ROADS.items():line(r['points'],'#879187',r['width']+2);line(r['points'],'#b6baba' if r['kind']!='service' else '#91a799',r['width'])
line([(305,235),(305,291)],'#eed6a5',7)
# Park and burial ground are separate and distinct from the civic square.
d.polygon([xy(x,y) for x,y in[(106,205),(148,205),(148,235),(106,235)]],fill='#65835e')
for i in range(6):
 for j in range(5):
  X,Y=xy(386+i*4,225+j*4);d.rectangle((X-3,Y-4,X+3,Y+4),fill='#b7b7a1')
colors={'Residential':'#c5b08b','Commerce':'#ceaa79','Civic':'#94b5b1','Estate':'#b6a4c4','Utility':'#a0aab0','Stone':'#9ea78c'}
for b in p.BUILDINGS:
 c,s=math.cos(math.radians(b['yaw'])),math.sin(math.radians(b['yaw']))
 pts=[xy(b['x']+x*c-y*s,b['y']+x*s+y*c) for x,y in[(-b['w']/2,-b['d']/2),(b['w']/2,-b['d']/2),(b['w']/2,b['d']/2),(-b['w']/2,b['d']/2)]]
 d.polygon(pts,fill=colors[b['category']],outline='#e5dab9',width=2)
 label(b['x'],b['y'],b['id'],17)
 if not b['id'].startswith('H') or b['id']=='HALL':label(b['x'],b['y']+b['d']/2+5,b['name'],18)
label(28,224,'WATER TOWER',17);label(126,238,'PARK / PLAYGROUND',18);label(399,260,'OLD GRAVEYARD',17);label(55,18,'ARRIVAL',20)
label(302,262,'BRIDGE',17);label(200,310,'RIDGE ROAD',16);label(153,168,'MAIN STREET',16)
label(268,105,'BRIAR RISE',17);label(60,183,'ORCHARD LOOP',15);label(370,405,'ESTATE GARDENS',16)
# Condensed prototype route is amber, future chapter geography shown with numbered hubs.
route=[(55,22),(75,55),(94,87),(103,118),(109,108),(65,161),(105,194),(126,221),(208,211),(290,222),(305,291),(305,310),(239,322),(185,344),(193,370),(177,403),(267,386),(344,371),(344,351),(365,351)]
for a,b in zip(route,route[1:]):
 n=max(1,round(math.dist(a,b)/2))
 for i in range(n):
  if i%3==0:line([tuple(p.mix(a[k],b[k],i/n) for k in range(2)),tuple(p.mix(a[k],b[k],min(1,(i+1)/n)) for k in range(2))],'#efd48a',.65)
label(23,418,'N ↑',24)
d.text((75,1863),'BUILT: terrain, roads, landmarks, paths, House01 streaming, condensed opening encounters.',font=bf(22),fill='#e1d3a8')
d.text((75,1901),'PLANNED: later chapter interiors and encounters, AI navigation / balancing, final art and atmospheric pass.',font=f(22),fill='#b7c3b5')
im.save(out/'Penance_V5_Masterplan.png')
# Footprint review is independent from UE physics. Include garage footprints.
issues=[]
for b in p.BUILDINGS:
 for name,x,y,w,depth in [('main',0,0,b['w'],b['d'])]+([('garage',-b['w']/2-3.8,b['d']*.16,4.2,5.2)] if b['category']=='Residential' else []):
  c,s=math.cos(math.radians(b['yaw'])),math.sin(math.radians(b['yaw']))
  poly=Polygon([(b['x']+c*(X+x)-s*(Y+y),b['y']+s*(X+x)+c*(Y+y)) for X,Y in[(-w/2,-depth/2),(w/2,-depth/2),(w/2,depth/2),(-w/2,depth/2)]])
  for rn,r in p.ROADS.items():
   area=poly.intersection(LineString([q[:2] for q in r['points']]).buffer(r['width']/2+.6)).area
   if area>.05:issues.append([b['id'],name,rn,round(area,2)])
(out/'Placement_Review.json').write_text(json.dumps({'road_footprint_overlaps':issues,'houses':14,'building_count':len(p.BUILDINGS)},indent=2))
print('Masterplan saved; footprint issues:',issues)
