"""V6 authoritative layout, meters; +X east, +Y north. No building scaling.
Shared V5 gameplay remains unchanged; only its placed actor properties move.
"""
import math,json
from pathlib import Path
import Penance_Town_V5_Design as v5
WIDTH,HEIGHT=400,350
MAP='/Game/Maps/V6/Penance_Town_V6';GENERATED='/Game/Environment/V6'
FOLDERS=[f'V6/{x.split("/",1)[1]}' for x in v5.FOLDERS]
uu=v5.uu;mix=v5.mix;smooth=v5.smooth;project=v5.project
def rect_center(r):return(r[0]+r[2]/2,r[1]+r[3]/2)
BUILDINGS=[dict(b) for b in v5.BUILDINGS]
positions={
'H01':(100,106,4.8,-90),'H02':(55,73,4.9,180),'H03':(19,117,5.5,90),'H04':(54,121,5.7,-90),'H05':(55,173,5.6,0),'H06':(107,88,4.9,-90),'H07':(119,106,5.1,90),'H08':(153,86,5.8,180),'H09':(187,80,6.2,180),'H10':(225,78,6.5,180),'H11':(260,84,6.8,190),'H12':(316,123,7,-95),'H13':(277,143,6.4,180),'H14':(380,183,5.5,75),
'GAS':(44,56,5,90),'DINER':(128,152,4.9,0),'BARBER':(149,151,5,0),'POST':(165.5,151,4.9,0),'LIBRARY':(184.5,152.5,5.1,0),'HALL':(214,164,5.3,0),'SHERIFF':(218,189,5.5,0),'SCHOOL':(145,184,5.5,0),'FIRE':(288,183,5.9,0),'CARE':(326,188,5.5,0),'PUMP':(302,202,2.3,-20),'CHURCH':(145,290,11,0),'FOSTER':(324,291,13,12),'LODGE':(318,268,10.5,20),'UTILITY':(377,249,9.5,10)}
for b in BUILDINGS:b.update(zip(('x','y','z','yaw'),positions[b['id']]))
for k,n,x,y,w,d,h,z,yaw,r in [
('H15','Gas lane cottage',89,74,9,8,3.2,4.9,-90,2),('H16','Orchard four square',71,119,9,10,4.5,5.1,90,2.4),('H17','West worker cottage',20,145,9,10,3.2,5.5,90,2.3),('H18','Briar cape',161,119,9,11,5.2,5.6,0,2.5),('H19','Postwar hip ranch',201,113,12,8,3.2,6.1,0,2.4),('H20','Briar cross gable',244,121,10,12,4.5,6.5,-15,2.6)]:
 BUILDINGS.append(dict(id=k,name=n,x=x,y=y,w=w,d=d,h=h,z=z,yaw=yaw,roof=r,category='Residential',chapter=3))
BUILDING_BY_ID={b['id']:b for b in BUILDINGS}
ROADS={}
def road(n,k,w,p):ROADS[n]=dict(kind=k,width=w,points=p)
road('Mill Road','main',7,[(30,20,4.6),(40,37,4.6),(66,42,4.6),(78,56,4.6),(78,80,4.8),(78,101,4.8),(86,123,4.9),(112,137,5),(141,137,5),(217,137,5),(229,137,5),(248,155,5.2),(250,180,4.8),(250,189,4.6),(250,226,4.6),(250,239,5.4)])
road('Main Street','main',7,[(112,137,5),(141,137,5),(217,137,5),(229,137,5)])
road('Orchard Loop','residential',5.6,[(78,88,4.8),(54,91,4.9),(34,109,5.1),(34,136,5.3),(53,154,5.3),(78,157,5.1),(96,143,5),(86,123,4.9)])
road('Briar Rise','residential',5.8,[(139,137,5),(139,114,5.3),(168,101,5.8),(210,95,6),(249,100,6.3),(275,118,6.5),(302,135,6.8)])
road('Foundry Cut','residential',5.8,[(302,135,6.8),(285,160,6.2),(263,166,5.6),(248,155,5.2)])
road('School Lane','residential',5.6,[(78,157,5.1),(102,166,5.2),(126,169,5.3),(165,169,5.3),(193,175,5.4),(213,176,5.5)])
road('Grave Lane','service',4,[(285,160,6.2),(314,169,5.2),(340,164,5),(367,163,5),(384,171,5.1)])
road('Ridge Road','main',6.5,[(250,239,5.4),(218,246,7),(181,251,8.5),(154,258,10.5),(135,261,11)])
road('Estate Drive','service',4,[(250,239,5.4),(280,247,7),(313,249,9),(344,260,11),(365,280,13),(365,311,13),(341,320,13),(325,317,13)])
road('Tower Service','service',4,[(34,136,5.3),(29,136,5.3),(28,156,7),(30,179,9),(8,195,12),(38,195,14.4),(38,183,14.4),(25,183,14.4)])
# Quadratic corner rounding keeps junctions tied to their surveyed endpoints.
def rounded(points,radius=3,fraction=.18):
 out=[points[0]]
 for a,b,c in zip(points,points[1:],points[2:]):
  L1=math.dist(a[:2],b[:2]);L2=math.dist(b[:2],c[:2]);t1=min(fraction,radius/L1);t2=min(fraction,radius/L2)
  p=tuple(mix(b[k],a[k],t1) for k in range(3));q=tuple(mix(b[k],c[k],t2) for k in range(3));out.append(p)
  for i in range(1,5):
   t=i/4;out.append(tuple((1-t)**2*p[k]+2*t*(1-t)*b[k]+t*t*q[k] for k in range(3)))
 out.append(points[-1]);return out
# Do not round the shared Main Street intersections or bridge abutments.
for n,r in ROADS.items():
 if n not in ('Mill Road','Main Street'):r['points']=rounded(r['points'],8,.3) if n=='Tower Service' else rounded(r['points'])
PATHS={
 'Park shortcut':[(34,136),(53,154),(78,157),(91,170),(100,187),(119,188)],
 'Creek trail':[(94,204),(133,209),(177,201),(222,186),(250,189),(284,190),(323,207),(365,218)],
 'Bridge approach':[(100,187),(124,202),(160,199),(190,181),(225,181),(250,189)],
 'Church approach':[(135,261),(145,265),(145,271)],
 'Estate back path':[(137,325),(165,323),(203,317),(239,310),(269,303),(287,286),(291,271),(309,271),(325,276)],
 'School yard':[(126,169),(126,177),(131,181)],
}
def creek_y(x):return 213+.08*(x-200)+10*math.sin(x/50)
def raw(x,y):
 d=y-creek_y(x);town=4.8+2*math.exp(-((x-275)/90)**2-((y-100)/70)**2)+.25*math.sin(x/40)*math.sin(y/33)
 ridge=9+max(0,y-245)*.026+2.4*math.exp(-((x-335)/70)**2-((y-290)/60)**2)
 margin=min(x,WIDTH-x,y,HEIGHT-y);edge=12*(1-smooth(margin/12))
 return mix(-1.8,town if d<0 else ridge,smooth((abs(d)-4)/18))+edge
class Terrain:
 def road_candidate(self,x,y):
  best=(1e9,0,0)
  for r in ROADS.values():
   for a,b in zip(r['points'],r['points'][1:]):
    d,t=project(x,y,a,b)
    if d<best[0]:best=(d,mix(a[2],b[2],t),r['width'])
  return best
 def surface(self,x,y):
  z=raw(x,y)
  for b in BUILDINGS:
   dx,dy=x-b['x'],y-b['y'];c,s=math.cos(math.radians(b['yaw'])),math.sin(math.radians(b['yaw']))
   X,Y=abs(dx*c+dy*s),abs(-dx*s+dy*c);dist=max(X-b['w']/2-2,Y-b['d']/2-2)
   if dist<5:z=mix(z,b['z']-.08,1-smooth(dist/5))
  parkdist=max(abs(x-100)-20,abs(y-187)-18)
  if parkdist<6:z=mix(z,5.12,1-smooth(parkdist/6))
  # Church rear service exit is flush with the preserved 2nd staircase.
  dist=max(abs(x-145)-13,abs(y-319)-11)
  if dist<4:z=mix(z,10.92,1-smooth(dist/4))
  # Gentle estate footpath grading overrides local hill noise.
  for n in ('Estate back path','Church approach'):
   for a,b in zip(PATHS[n],PATHS[n][1:]):
    d,t=project(x,y,a,b)
    if d<3:
     zz=10.92 if n=='Church approach' else mix(10.92,12.92,max(0,min(1,(mix(a[0],b[0],t)-137)/188)))
     z=mix(z,zz,1-smooth((d-1.7)/1.3))
  for drive in DRIVES.values():
   for a,b in zip(drive,drive[1:]):
    dd,tt=project(x,y,a,b)
    if dd<4:z=mix(z,mix(a[2],b[2],tt)-.18,1-smooth((dd-2.0)/2))
  d,rz,w=self.road_candidate(x,y)
  # Preserve creek under bridge; grade the public road at both abutments.
  bridge=abs(x-250)<7 and 188<=y<=228
  if not bridge and d<w/2+4:z=mix(z,rz-.2,1-smooth((d-w/2)/4))
  if d<w/2+2.2 and not bridge:z=min(z,rz-.35)
  if bridge:z=min(z,3.9)
  return z
 def road_z(self,x,y):return self.road_candidate(x,y)[1]+.045
CHECKPOINTS=[(30,20,5.6),v5.CHECKPOINTS[1],(34,136,6.3),(100,187,6),(145,269,12),(153,294,7.32),(137,323,12),(325,276,14)]
OBJECTIVES=v5.OBJECTIVES
VIEWS=[('Arrival',(30,20),(47,49,6)),('Orchard',(34,107),(54,121,7)),('Briar',(209,96),(252,110,8)),('MainStreet',(113,137),(187,153,8)),('Park',(100,187),(145,286,20)),('Bridge',(250,184),(226,256,12)),('Church',(145,255),(145,290,22)),('Foster',(330,266),(324,291,21))]
DRIVES={}
for b in BUILDINGS:
 c,s=math.cos(math.radians(b['yaw'])),math.sin(math.radians(b['yaw']));front=(b['x']+s*(b['d']/2+1),b['y']-c*(b['d']/2+1))
 best=(1e9,None)
 for n,r in ROADS.items():
  for a,q in zip(r['points'],r['points'][1:]):
   d,t=project(*front,a,q)
   if d<best[0]:best=(d,(mix(a[0],q[0],t),mix(a[1],q[1],t),mix(a[2],q[2],t)))
 DRIVES[b['id']]=[best[1],(*front,b['z']-.08)]
DRIVES['CHURCH']=[(135,261,11),(145,265,11),(145,271,11)]
DRIVES['FOSTER']=[(365,294,13),(353,294,13)]
DRIVES['UTILITY']=[(355,270,12),(371,265,10),(377,256,9.5)]
def samples(points,step=2):
 for a,b in zip(points,points[1:]):
  n=max(1,math.ceil(math.dist(a,b)/step))
  for i in range(n):yield tuple(mix(a[k],b[k],(i+.37)/n) for k in range(len(a)))
def export(path):
 data=dict(map=MAP,units='meters; Unreal UU = meters * 100',site=[WIDTH,HEIGHT],north='+Y',buildings=BUILDINGS,roads=ROADS,paths=PATHS,driveways=DRIVES,checkpoints=CHECKPOINTS,objectives=OBJECTIVES,chapters=v5.CHAPTERS,views=VIEWS,creek=[(x,creek_y(x),0) for x in range(0,401,4)])
 Path(path).write_text(json.dumps(data,indent=2)+'\n');return data
