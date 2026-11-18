"""Authoritative V5 placements. Meters, east +X / north +Y / up +Z; Unreal = meters * 100.
Founded at a mill crossing; civic infill follows the historic commercial road.
Orchard workers' cottages predate the eastern postwar ridge subdivision.
Church land and the Foster estate share the old north-bank carriage road.
The disappearance was six months ago: intact buildings, interrupted routines.
"""
import math,json
from pathlib import Path
WIDTH,HEIGHT=480,440
MAP='/Game/Maps/V5/Penance_Town_V5'
GENERATED='/Game/Environment/V5'
FOLDERS=['V5/00_Geography','V5/01_Roads','V5/02_Creek','V5/03_Residential','V5/04_Commercial','V5/05_Civic','V5/06_Ridge','V5/07_Forest','V5/08_Props','V5/09_Story','V5/10_Validation']
def uu(x,y,z=0):return(x*100,y*100,z*100)
def mix(a,b,t):return a+(b-a)*t
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def creek_y(x):return 268+.12*(x-240)+15*math.sin(x/64)
def project(x,y,a,b):
 dx,dy=b[0]-a[0],b[1]-a[1];t=max(0,min(1,((x-a[0])*dx+(y-a[1])*dy)/(dx*dx+dy*dy)))
 return math.hypot(x-a[0]-t*dx,y-a[1]-t*dy),t
def raw(x,y):
 d=y-creek_y(x)
 town=4.6+10*math.exp(-((x-30)/48)**2-((y-224)/60)**2)+4*math.exp(-((x-390)/90)**2-((y-136)/100)**2)+.45*math.sin(x/50)*math.sin(y/40)
 ridge=8.5+max(0,y-290)*.024+3.0*math.exp(-((x-373)/80)**2-((y-375)/65)**2)
 edge=8*smooth((max(abs(x-240)/240,abs(y-220)/220)-.87)/.13)
 base=town if d<0 else ridge
 channel=smooth((abs(d)-4)/20)
 return mix(-1.8,base,channel)+edge
ROADS={}
def road(k,kind,width,p):ROADS[k]={'kind':kind,'width':width,'points':p}
road('Mill Road','main',7,[(55,22,5),(75,55,4.8),(94,87,4.7),(130,115,4.6),(176,145,4.7),(230,171,4.7),(290,186,5),(305,220,4.3),(305,235,4.2),(305,291,4.2),(305,310,4.7)])
road('Main Street','main',7,[(109,153,4.6),(154,161,4.6),(200,170,4.6),(230,171,4.7),(285,169,4.9)])
road('Orchard Loop','residential',5.6,[(94,87,4.7),(60,120,4.8),(65,164,5.3),(105,194,5.2),(133,182,4.8),(154,161,4.6),(130,115,4.6)])
road('Briar Rise','residential',5.8,[(202,158,4.7),(241,131,5.3),(285,116,6),(328,106,6.4),(367,125,7.5),(387,155,8)])
road('Foundry Cut','residential',5.8,[(387,155,8),(358,181,6.9),(320,190,5.5),(290,186,5)])
road('School Lane','residential',5.6,[(105,194,5.2),(125,213,5.3),(174,220,5.2),(208,211,4.9),(230,171,4.7)])
road('Grave Lane','service',4,[(320,190,5.5),(349,209,5.8),(382,214,5.5),(409,214,5.5)])
road('Ridge Road','main',6.5,[(305,310,4.7),(280,320,5.6),(239,322,6.2),(210,338,8.1),(185,344,9.3),(169,348,10)])
road('Estate Drive','service',4,[(305,310,4.7),(324,329,6.1),(351,337,7.8),(382,350,10.0),(404,365,11.5),(404,396,13),(380,401,13),(365,395,13)])
road('Tower Service','service',4,[(65,164,5.3),(38,173,6.8),(15,192,8.8),(14,217,10.8),(14,238,12.7),(44,242,14.4),(44,224,14.4),(30,224,14.4)])
PATHS={
 'Park shortcut':[(101,190),(103,215),(126,227),(150,221)],
 'Creek trail':[(125,232),(166,239),(213,236),(259,227),(290,222),(331,226),(367,243),(407,251)],
 'Bridge approach':[(208,211),(254,212),(290,222),(305,235)],
 'Old footbridge access':[(144,240),(155,254),(166,278),(180,307),(210,338)],
 'Estate back path':[(185,401),(223,394),(267,386),(308,378),(332,373),(336,360),(336,350),(349,350),(365,354)],
 'School yard':[(125,213),(125,204),(162,197)],
}
BUILDINGS=[]
def building(k,name,x,y,w,d,h,z,cat,yaw=0,roof=2,**kw):
 BUILDINGS.append(dict(id=k,name=name,x=x,y=y,w=w,d=d,h=h,z=z,category=cat,yaw=yaw,roof=roof,**kw))
# Lots deliberately differ in age, setbacks, orientation, and access.
for args in [
 ('H01','A Light in the Window',109,118,14,12,6,4.8,-90,3),
 ('H02','Orchard bungalow',71,87,11,9,3.2,4.9,35,2),
 ('H03','Mill worker duplex',45,132,13,10,5.6,5.5,-8,2.8),
 ('H04','Corner saltbox',83,151,10,13,5.2,5.7,-100,3),
 ('H05','Orchard cottage',88,206,10,9,3.2,5.6,30,2.3),
 ('H06','Garden house',146,101,11,10,3.5,4.9,25,2.5),
 ('H07','Stationmaster house',165,110,12,12,6,5.1,15,3.2),
 ('H08','Briar ranch',231,109,16,9,3.1,5.8,-30,2),
 ('H09','Split-level',279,96,13,10,4.4,6.7,-10,2.2),
 ('H10','Ridge gable',332,88,11,12,5.8,7.1,10,3),
 ('H11','Uphill family home',366,102,14,11,5.7,8,35,2.8),
 ('H12','Briar dead-end',410,149,13,12,6,8.7,-95,3.2),
 ('H13','Foundry cottage',353,165,11,9,3.4,7.3,0,2),
 ('H14','Creek keeper home',423,218,10,12,5.4,5.5,75,2.6),
]:
 k,n,x,y,w,d,h,z,yaw,roof=args;building(k,n,x,y,w,d,h,z,'Residential',yaw,roof,chapter=2 if k=='H01' else 3)
building('GAS','Last Stop Gas',91,48,14,10,3.7,5,'Commerce',-25,1,chapter=1)
building('DINER','Mill Road Diner',168,179,22,10,4.2,4.9,'Commerce',10,1,chapter=5)
building('POST','Post Office',205,187,13,10,5,4.9,'Civic',4,2,chapter=5)
building('BARBER','Barber / Hardware',184,130,16,10,5.8,5,'Commerce',180,1.3,chapter=5)
building('LIBRARY','Public Library',246,151,22,13,6,5.1,'Civic',0,2.4,chapter=6)
building('HALL','Town Hall',255,196,21,15,7,5.3,'Civic',0,3,chapter=6)
building('SHERIFF','Sheriff Annex',280,208,12,11,4,5.3,'Civic',-20,1.4,chapter=6)
building('SCHOOL','Schoolhouse',161,200,27,13,5,5.5,'Civic',-6,3,chapter=4)
building('FIRE','Fire Station',319,165,22,16,5.2,5.9,'Utility',0,1.6,chapter=5)
building('CARE','Graveyard caretaker',374,226,8,8,3.2,5.5,'Stone',20,2,chapter=7)
building('PUMP','Creek Pump Station',346,240,10,8,4,2.3,'Utility',-20,1,chapter=8)
building('CHURCH','Grand Church',185,370,24,36,10,10,'Estate',0,5,chapter=10)
building('FOSTER','Foster House',364,369,34,25,11,13,'Estate',12,4.5,chapter=12)
building('LODGE','Estate gate lodge',365,328,9,8,4,10,'Estate',20,2.5,chapter=12)
building('UTILITY','Substation / maintenance',434,326,18,13,4.5,9.5,'Utility',10,1,chapter=8)
BUILDING_BY_ID={b['id']:b for b in BUILDINGS}
DRIVES={
 'H01':[(94,104),(101,115)],'H02':[(79,75),(75,86)],'H03':[(61,131),(54,132)],'H04':[(64,151),(74,151)],
 'H05':[(104,193),(94,201)],'H06':[(143,124),(146,109)],'H07':[(152,129),(164,119)],
 'H08':[(236,135),(232,117)],'H09':[(280,118),(280,104)],'H10':[(330,107),(332,98)],
 'H11':[(366,125),(366,111)],'H12':[(387,155),(401,150)],'H13':[(355,181),(353,172)],'H14':[(409,214),(415,218)],
 'GAS':[(75,55),(85,48)],'DINER':[(167,164),(168,172)],'BARBER':[(187,150),(184,138)],'POST':[(205,170),(205,180)],
 'LIBRARY':[(248,171),(248,161)],'HALL':[(255,178),(255,187)],'SHERIFF':[(290,210),(288,209)],
 'SCHOOL':[(155,218),(159,210)],'FIRE':[(319,190),(319,176)],'CARE':[(375,218),(374,220)],
 'PUMP':[(349,235),(346,246)],'CHURCH':[(185,344),(185,350)],'FOSTER':[(404,371),(394,367)],
 'LODGE':[(377,347),(366,334)],'UTILITY':[(404,390),(427,360),(434,335)]}
class Terrain:
 def road_candidate(self,x,y):
  best=(1e9,None,None)
  for r in ROADS.values():
   for a,b in zip(r['points'],r['points'][1:]):
    d,t=project(x,y,a,b)
    if d<best[0]:best=(d,mix(a[2],b[2],t),r['width'])
  return best
 def surface(self,x,y):
  z=raw(x,y);d,rz,w=self.road_candidate(x,y)
  if abs(y-creek_y(x))>15 and d < w/2+5:z=mix(z,rz,1-smooth((d-w/2)/5))
  # Flatten graded yards, smoothly tie them into the existing terrain.
  for b in BUILDINGS:
   dx,dy=x-b['x'],y-b['y'];c,s=math.cos(math.radians(b['yaw'])),math.sin(math.radians(b['yaw']))
   X,Y=abs(dx*c+dy*s),abs(-dx*s+dy*c)
   dist=max(X-b['w']/2-2,Y-b['d']/2-2)
   if dist<4:z=mix(z,b['z']-.08,1-smooth(dist/4))
  yard=max(abs(x-185)-13,abs(y-399)-11)
  if yard<4:z=mix(z,9.92,1-smooth(yard/4))
  for key,points in DRIVES.items():
   b=BUILDING_BY_ID[key];startz=self.road_candidate(*points[0])[1];length=sum(math.dist(a,q) for a,q in zip(points,points[1:]));run=0
   for a,q in zip(points,points[1:]):
    dist,t=project(x,y,a,q);seg=math.dist(a,q)
    if dist<3.2:
     dz=mix(startz,b['z']-.08,(run+seg*t)/max(length,.01));z=mix(z,dz,1-smooth((dist-1.6)/1.6))
    run+=seg
  # Keep the triangulated ground below the travel surface even at junctions
  # and sharp service-road bends. The road mesh defines the finished grade.
  d,rz,w=self.road_candidate(x,y)
  if d<w/2+.8 and abs(y-creek_y(x))>15:z=min(z,rz-.20)
  return z
 def road_z(self,x,y):return self.road_candidate(x,y)[1]+.045

def samples(points,step=2):
 for a,b in zip(points,points[1:]):
  n=max(1,math.ceil(math.dist(a[:2],b[:2])/step))
  for i in range(n):yield tuple(mix(a[j],b[j],i/n) for j in range(len(a)))
 yield points[-1]
# Condensed preview, not a claim that chapters 5–9 or 12–14 encounters are finished.
CHECKPOINTS=[(55,22,6),(2000,0,1),(65,161,6.3),(126,221,6.3),(185,349,11),(193,374,6.32),(177,403,11),(365,354,14)]
OBJECTIVES=[
 'The road has fallen away behind you. Follow the warm light up Mill Road. [E: house door]',
 'Someone is standing in the hall. Find the front door and leave.',
 'The door returned you to the side yard. Follow the orchard street toward the school bell.',
 'The park gate is open. Cross the playground; the ridge is visible from there.',
 'The bridge is clear. Follow the old road to the church on the far bank.',
 'The nave is empty. Take the east service stair beneath the church.',
 'Keep moving. The west service stair leads outside. [Scripted preview: no damage]',
 'The estate gate is open. Follow the garden path to Foster House.']
# name / eyeXY / aimXYZ. Eye Z is terrain + 1.65 m in the renderer.
VIEWS=[('Arrival',(61,32),(109,118,9)),('Residential',(65,152),(97,185,8)),('Park',(117,218),(161,200,9)),
 ('MainStreet',(186,166),(259,190,12)),('Graveyard',(365,215),(397,236,7)),('CreekCrossing',(305,235),(305,290,5)),
 ('ChurchApproach',(185,330),(185,370,25)),('FosterApproach',(365,335),(364,369,22))]
CHAPTERS=[]
def chapter(n,title,start,obj,path,encounter,optional,obstacle,unlock,exit,shortcut,beats):
 CHAPTERS.append(dict(chapter=n,title=title,start=start,objective=obj,path=path,encounter=encounter,optional=optional,obstacle=obstacle,unlock=unlock,exit=exit,shortcut=shortcut,beats=beats,implemented='site + routes; encounters planned'))
chapter(1,'The Return','Arrival','Reach the lit house',['GAS','H01'],'No clear enemy sighting',['Gas register','Bus shelter'],'Visible road washout','Reach the house','H01','Gas forecourt',['Arrival','Interrupted refueling','Road washout','Warm window reveal'])
chapter(2,'A Light in the Window','H01','Escape the changed house',['H01'],'Brief stationary Penance in the hall',['Childhood room'],'Changed exit','Enter then leave House01','Orchard Loop','Side yard',['Familiar doorway','Childhood echo space','Silhouette','Changed side-yard exit'])
chapter(3,'The Forgotten Neighborhood','Orchard Loop','Find the school route',['H03','H05','SCHOOL'],'Dead-end escape reserved',['H04 yard','H12 dead-end'],'Park shortcut fence','Orchard memory checkpoint','School Lane','Park service path',['Repeat street','Changed parked car','Dead-end reserve','Shortcut opens'])
chapter(4,'Innocence','SCHOOL','Reach the park overlook',['SCHOOL','PARK'],'Threat-free relief, later memory echo',['School playground'],'School rear access','Park checkpoint','Main Street','Creek trail',['Empty classroom reserve','Playground','Sister memory reserve','Church glimpse'])
chapter(5,'The Last Ordinary Day','DINER','Restore one block of power',['DINER','BARBER','POST'],'Dark kitchen escape reserved',['Hardware store'],'Unpowered service door','Power restoration puzzle planned','LIBRARY','Commercial rear alley',['Interrupted meal','Breaker route','Power returns','Last-night reconstruction'])
chapter(6,'The Missing Records','LIBRARY','Reach the municipal records wing',['LIBRARY','HALL','SHERIFF'],'Archive evasion reserved',['Postal sorting','Town Hall balcony'],'Annex evidence cabinet','Core record scene planned','CARE','Civic courtyard',['Library reference','Town Hall denial','Sheriff annex','Graveyard direction'])
chapter(7,'The Unmarked','CARE','Reach the creek maintenance gate',['CARE','GRAVEYARD'],'Wall-and-grave sightline escape reserved',['Unmarked plots'],'Caretaker gate','Burial-record scene planned','PUMP','Grave Lane',['Caretaker room','Missing names','Terraced graves','Creek path opens'])
chapter(8,'Beneath the Water','PUMP','Make the crossing approach safe',['PUMP','BRIDGE'],'Pump hazard/evasion reserved',['Utility yard','Old mill footing'],'Sluice machinery','Pump environmental puzzle planned','BRIDGE','Creek maintenance trail',['Bank descent','Pump chamber reserve','Flood bypass','Bridge approach'])
chapter(9,'The Crossing','BRIDGE','Reach the old church road',['BRIDGE','CHURCH'],'Exposed crossing, no early patrol',['Old footbridge'],'Creek and steep banks','Crossing event planned','CHURCH','Return bridge',['Bridge exposure','Forest compression','Ridge road cut','Church threshold'])
chapter(10,'Confession','CHURCH','Find the basement stair',['CHURCH'],'Door-opening set piece planned; open entry in preview',['Church office reserve'],'Office/archive doors planned','Nave checkpoint','BASEMENT','Rear church path',['Grand entrance','Empty pews','Archive reserve','Service stair'])
chapter(11,'The First Descent','BASEMENT','Escape to the grounds',['BASEMENT','FOSTER'],'Scripted no-damage chase preview',['Maintenance alcove'],'Estate gate until escape','Reach west escape stair','FOSTER','Garden back path',['Descent','Penance appears','Two-route cover space','Escape stair','Estate reveal'])
chapter(12,'The Grounds','FOSTER','Reach the estate entry',['LODGE','FOSTER'],'Garden stealth routes reserved',['Greenhouse','Carriage house'],'Estate threshold','Grounds sequence planned','FOSTER interior','Garden service loop',['Gate lodge','Garden approach','Outbuildings','Main threshold'])
chapter(13,'The Erased','FOSTER interior','Recover the sister’s fuller story',['FOSTER'],'Interior survival reserved',['Personal belongings'],'Interior locked wing planned','Core revelation scene planned','Return town','Estate service exit',['Sister’s room reserve','Evidence of child','Institutional link','Return route'])
chapter(14,'Penance','Return town','Confront what the town concealed',['CHURCH','HALL','H01'],'Final confrontation reserved',['Optional ending discoveries'],'Narrative resolution undecided','Future chapter implementation','Ending undecided','Established return routes',['Altered church','Changed square','Disappearance reconstruction','Confrontation'])
for c in CHAPTERS:
 if c['chapter'] in [1,2,3,4,9,10,11,12]:c['implemented']='geography built; condensed opening preview only (see validation report)'
def export(path):
 t=Terrain();data=dict(map=MAP,units='meters; multiply every coordinate/dimension by 100 for Unreal UU',site=[WIDTH,HEIGHT],north='+Y',history=__doc__,buildings=BUILDINGS,roads=ROADS,paths=PATHS,driveways=DRIVES,checkpoints=CHECKPOINTS,objectives=OBJECTIVES,chapters=CHAPTERS,views=VIEWS,creek=[(x,creek_y(x),0) for x in range(0,WIDTH+1,4)])
 for b in data['buildings']:b['unreal_position']=uu(b['x'],b['y'],b['z']);b['unreal_yaw']=b['yaw']
 Path(path).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':export(Path(__file__).resolve().parents[1]/'Docs/V5/Penance_V5_Implementation.json')
