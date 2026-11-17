"""V4 source geometry and grading. Plan-space inputs are meters, Y points south."""
import json
import math
from pathlib import Path

WIDTH, HEIGHT = 480, 600
MAP = '/Game/Maps/Planning/Penance_Town_Masterplan_V4_Blockout'
GENERATED = '/Game/Maps/Planning/V4_Blockout'
SOURCE = json.loads(Path(__file__).with_name('Penance_Town_V4_Layout.json').read_text())
PARCELS = {p['id']: p for p in SOURCE['parcels']}
ROADS = {r['id']: {**r, 'points': [tuple(p) for p in r['points']]} for r in SOURCE['roads']}
FOLDERS = ('00_Terrain', '01_Roads', '02_Bridges_Creek', '03_Residential_Parcels',
           '04_Residential_Foundations', '05_Outbuilding_Reserves', '06_Town_Center',
           '07_Shops', '08_Church_Foster_Estate', '09_Utilities_Outskirts',
           '10_Landmark_Proxies', '11_Labels_Debug', '12_Player_Test')
NAMES = {
    **{p['id']: p['id'] + '_' + p['name'].replace(' ', '_') for p in SOURCE['parcels'][:14]},
    'WATER':'Water_Tower', 'CHURCH':'Church', 'FOSTER':'Foster_House',
    'UTILITY':'Utility_Station', 'MAINT':'Maintenance_Shed', 'PUMP':'Creek_Pump_House',
    'SCHOOL':'Schoolhouse', 'PARK':'Town_Park', 'HALL':'Town_Hall', 'CEM':'Central_Graveyard',
    'POST':'Post_Office', 'LIB':'Public_Library', 'FIRE':'Fire_Station', 'BARBER':'Barber_Shop',
    'TATTOO':'Tattoo_Shop', 'STORE':'General_Store', 'DINER':'Diner', 'HARD':'Hardware_Store',
    'LAUND':'Laundromat', 'GAS':'Gas_Station',
}
ROAD_NAMES = dict(zip(ROADS, ('MainStreet','NorthSwitchback','OrchardLoop','CemeteryEast',
    'EastLower','MarketStreet','BriarLane','WaterTowerAccess','EstateService','UtilitySpur',
    'PumpSpur','ShopAlley','FireApron','CreekTrail','ParkFootbridgeApproach')))


def uu(x, y, z=0):
    """Convert HTML meters to Unreal centimeters, Y north, Z above town datum."""
    return (100*x, 100*(HEIGHT-y), 100*z)


def rect_center(rect):
    x, y, w, d = rect
    return x+w/2, y+d/2


def parcel_rect(p):
    return tuple(p[k] for k in ('x','y','w','h'))


# Resolve source right-of-way conflicts and gaps without moving the source lots.
ROADS['R_WEST']['points'][1:3] = [(24, 320), (24, 405)]
ROADS['R_SHOPS']['points'] = [(252,410),(252,402),(305,402),(316,402),(316,410)]
ROADS['R_WATER']['points'] = [(265,128), *ROADS['R_WATER']['points'], (75,69), (65,68)]
ROADS['R_ESTATES']['points'].extend([(364,65),(347.2,65)])
ROADS['R_UTILITY']['points'][1:] = [(420,109),(429,102),(429,90),(434,71)]
ROADS['R_PUMP']['points'][-1:] = [(429,186.2),(437,186.2)]


def mix(a,b,t):
    return a + (b-a)*t


def clamp(t):
    return min(1.0, max(0.0, t))


def smooth(t):
    t = clamp(t)
    return t*t*(3-2*t)


def profile(value, anchors):
    for (a, za), (b, zb) in zip(anchors, anchors[1:]):
        if value <= b:
            return mix(za, zb, clamp((value-a)/(b-a)))
    return anchors[-1][1]


def length(points):
    return sum(math.dist(a,b) for a,b in zip(points,points[1:]))


def points_with_distance(points):
    total = 0.0
    yield points[0], total
    for a,b in zip(points,points[1:]):
        total += math.dist(a,b)
        yield b,total


def road_heights(key):
    points = ROADS[key]['points']
    total = length(points)
    result = []
    for (x,y), d in points_with_distance(points):
        if key == 'R_MAIN':
            z = profile(y, [(136,3),(163,3),(193,2.35),(255,.40),(320,0),(410,0),(500,.40),(600,1.10)])
        elif key == 'R_NORTH':
            z = 3 if y >= 136 and d < 10 else profile(d, [(4,3),(total-10,11.85),(total,12)])
        elif key == 'R_WEST':
            z = 0 if x == 232 else 1.3
        elif key == 'R_EAST':
            z = 0 if y >= 330 else (330-y)*.012
        elif key in ('R_EAST_SOUTH','R_MARKET','R_SHOPS','R_FIRE'):
            z = 0
        elif key == 'R_DEADEND':
            z = .4 + (x-232)*5.6/226
        elif key == 'R_WATER':
            z = 3.23 + d*(20-3.23)/total
        elif key == 'R_ESTATES':
            z = profile(d, [(0,12),(55,11.4),(total,10)])
        elif key == 'R_UTILITY':
            z = profile(d, [(0,road_heights('R_NORTH')[5][2]),(total,9.7)])
        elif key == 'R_PUMP':
            z = profile(d, [(0,1.608),(total,1.8)])
        else:
            continue
        result.append((x,y,z))
    return result


def creek_y(x):
    # Sample the supplied SVG's three cubic segments (S reflects the previous handle).
    return profile(x, CREEK_SAMPLES)


def sample_creek():
    pieces = [((-8,151),(56,145),(86,148),(125,153)),
              ((125,153),(164,158),(205,154),(265,148)),
              ((265,148),(325,142),(374,143),(490,151))]
    return [tuple((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d
                  for a,b,c,d in zip(*piece))
            for piece in pieces for i in range(61) if i < 60 or piece == pieces[-1]
            for t in (i/60,)]


CREEK_SAMPLES = sample_creek()


def natural(x,y):
    """Low-frequency rolling ground, civic datum, ridge and curved creek valley."""
    ridge = 9.5 * (1-smooth((y-67)/83))
    tower = 10.5 * math.exp(-((x-58)/56)**2-((y-52)/51)**2)
    west = 3.2 * math.exp(-((x-55)/93)**2-((y-415)/102)**2)
    east = 5.6 * math.exp(-((x-445)/90)**2-((y-516)/110)**2)
    rolls = (.55*math.sin(x/38)*math.cos(y/39)+.35*math.cos(y/23))
    civic = smooth(math.hypot((x-238)/153,(y-325)/130)-.25)
    upland = ridge + tower + (west+east+rolls)*civic
    # Town-side banks stay below the bridge deck; grade corridors are added later.
    f = smooth((abs(y-creek_y(x))-4.2)/17)
    return mix(-4.0, upland, f)


def pad_grade(key, rect):
    override = {'WATER':20,'CHURCH':12,'FOSTER':10,'PARK':.45,'HALL':0,'CEM':3,
                'SCHOOL':1.25,'SHERIFF':0,'CARETAKER':3,'PUMP':1.8,'UTILITY':9.7,'MAINT':8.1}
    x,y = rect_center(rect)
    if key in override:
        return override[key]
    if key in ('POST','LIB','FIRE','BARBER','TATTOO','STORE','DINER','HARD','LAUND','GAS'):
        return .16
    if key in ('H01','H02','H03','H04'):
        return 1.55 if x < 90 else 1.12
    if key in ('H05','H06','H07','H08'):
        return max(.4, (330-y)*.012+.45)
    return .6+(x-232)*5.6/226


PADS = {key: ((p['fx'],p['fy'],p['fw'],p['fh']),p['category'])
        for key,p in PARCELS.items() if p['fw'] and p['fh']}
PADS['SHERIFF'] = ((199,260,13,10),'Civic')
PADS['CARETAKER'] = ((368,296,12,9),'Cemetery')
NAMES.update(SHERIFF='Sheriff_Annex', CARETAKER='Caretaker_Shed')

# Additional program called for by the written notes. The HTML markers remain.
EXTRA = {
    'H01':[('Garden_Shed',(64,452,5,5))],
    'H02':[('Attached_Garage',(120.8,439,6,7))],
    'H05':[('Garden_Shed',(440,231,5,5))],
    'H06':[('Two_Car_Garage',(438,262,8,8))],
    'H07':[('Porch',(427,337,7,3))],
    'H08':[('Damaged_Garage',(440,376,8,7))],
    'H09':[('Small_Shed',(292,438,5,5))],
    'H10':[('Rear_Workshop',(348,434,8,7))],
    'H11':[('Detached_Garage',(425,438,8,7))],
    'H12':[('Playhouse',(261,546,5,6)),('Small_Shed',(272,550,5,5))],
    'H13':[('Garden',(353,541,12,10))],
    'H14':[('Old_Garage',(401,542,8,8))],
}
RESERVES = {}
for id_, p in PARCELS.items():
    if not id_.startswith('H') or len(id_) != 3:
        continue
    out = p['outbuilding']
    RESERVES[id_] = [(out['kind'].title().replace(' ','_'), parcel_rect(out)), *EXTRA.get(id_,())]

# Supplemental pedestrian, apparatus and estate connections.
EXTRA_PATHS = {
    'CivicPlazaApproach': (2.5,[(180,320),(180,302),(180,276)]),
    'ParkWalk': (2,[(100,235),(100,267),(119,289),(119,320)]),
    'SchoolSideWalk': (2,[(109,208),(129,222),(129,233)]),
    'GraveyardMainWalk': (2.6,[(350,330),(350,313),(350,247),(325,247)]),
    'GraveyardCrossWalk': (1.8,[(314,275),(373,275),(373,296)]),
    'ChurchEntry': (4,[(258,78),(235,78),(208,78),(187,79)]),
    'ChurchRearService': (4,[(258,29),(229,29),(220,41),(209.5,57)]),
    'ChurchFosterWalk': (2.4,[(209.5,72),(240,72),(273,72),(317,72)]),
    'FosterDrive': (3,[(347.2,65),(345,65)]),
    'PumpPadApproach': (2,[(437,186.2),(437,184)]),
    'FireApparatusApron': (5,[(365,344),(365,352),(365,359)]),
    'GasEntry': (4,[(232,465),(200,465),(190,469)]),
    'WaterPadApproach': (3,[(65,68),(65,65)]),
    'UtilityApron': (3.5,[(434,71),(434,66.5)]),
}
for shop in ('BARBER','TATTOO','STORE','DINER','HARD','LAUND'):
    p = PARCELS[shop]
    x = p['fx']+p['fw']*.5
    road_y = 405 if p['x'] < 232 else 402
    EXTRA_PATHS[shop+'_Delivery'] = (2.4,[(x,p['fy']+p['fh']),(x,road_y)])
EXTRA_PATHS['ShopFrontWest'] = (1.75,[(148,369),(228,369),(232,370)])
EXTRA_PATHS['ShopFrontEast'] = (1.75,[(232,369),(240,370),(319,370)])


PARK_APPROACH = [(100,235),(109,218),(109,188),(97,177),(97,162)]


def route_points(key):
    points = ROADS[key]['points']
    if key == 'R_MAIN':
        return points[:-1]  # The bridge is its own editable actor.
    if key == 'R_NORTH':
        return [(265,136),*points[1:]]
    if key == 'R_PARKBRIDGE':
        return PARK_APPROACH
    return points


def driveway(id_):
    rect, _ = PADS[id_]
    x,y = rect_center(rect)
    n = int(id_[1:])
    if n <= 2:
        return [(x,405),(x,rect[1])]
    if n <= 4:
        return [(x,320),(x,rect[1])]
    if n <= 8:
        return [(398,y),(rect[0],y)]
    if n <= 11:
        return [(x,500),(x,rect[1]+rect[3])]
    return [(x,500),(x,rect[1])]


def project(x,y,a,b):
    ax,ay=a[:2]
    dx,dy=b[0]-ax,b[1]-ay
    t=clamp(((x-ax)*dx+(y-ay)*dy)/max(dx*dx+dy*dy,1e-12))
    return math.hypot(x-ax-t*dx,y-ay-t*dy),t


def rect_distance(x,y,rect):
    a,b,w,d=rect
    return math.hypot(max(a-x,0,x-a-w),max(b-y,0,y-b-d))


class Terrain:
    """A single grading model shared by mesh generation, surfacing and verification."""
    STEP=2
    def __init__(self):
        self.roads = {key: road_heights(key) for key in ROADS if ROADS[key]['kind']!='path'}
        self.grade_segments=[]
        self.plateaus=[(rect,pad_grade(k,rect),12) for k,(rect,_) in PADS.items()]
        for id_, reserves in RESERVES.items():
            for _,rect in reserves:
                self.plateaus.append((rect,pad_grade(id_,PADS[id_][0]),6))
        self.plateaus.extend([(parcel_rect(PARCELS['CEM']),3,20),
                              ((147,223,68,86),0,10),((38,238,92,65),.45,12)])
        for key, pts in self.roads.items():
            for a,b in zip(pts,pts[1:]):
                if key=='R_MAIN' and a[1]==163 and b[1]==140:
                    continue
                self.grade_segments.append((a,b,ROADS[key]['width']/2+.2,12))
        creek_trail = [(x,y,profile(x,[(0,.8),(160,.8),(210,1.4),(265,2.90),(300,1.9),(385,.95),(480,.95)]))
                       for x,y in ROADS['R_CREEKPATH']['points']]
        # Add a height control exactly where the bank path meets the main road.
        creek_trail.insert(4,(265,163.26,2.90))
        south_foot = [(x,y,profile(y,[(162,.8),(177,.85),(218,1.0),(235,1.0)])) for x,y in PARK_APPROACH]
        north_foot = [(97,135,1.55),(91,111,3.0)]
        for points in (creek_trail,south_foot,north_foot):
            self.grade_segments.extend((a,b,1.1,5) for a,b in zip(points,points[1:]))
        for id_ in RESERVES:
            a,b=driveway(id_)
            z=self.road_height(*a)
            self.grade_segments.append(((*a,z),(*b,pad_grade(id_,PADS[id_][0])),1.6,4.0))
        # Index localized grading features so a terrain vertex only checks nearby features.
        self.index={}
        for rect,z,reach in self.plateaus:
            x,y,w,d=rect
            self.add_index((x-reach,y-reach,x+w+reach,y+d+reach), ('pad',rect,z,reach))
        for a,b,hw,reach in self.grade_segments:
            r=hw+reach
            self.add_index((min(a[0],b[0])-r,min(a[1],b[1])-r,max(a[0],b[0])+r,max(a[1],b[1])+r),('road',a,b,hw,reach))
        self.grid=[[self.height(x,y) for x in range(0,WIDTH+1,self.STEP)] for y in range(0,HEIGHT+1,self.STEP)]

    def add_index(self,bounds,item):
        x,y,X,Y=bounds
        for j in range(math.floor(y/20),math.floor(Y/20)+1):
            for i in range(math.floor(x/20),math.floor(X/20)+1):
                self.index.setdefault((i,j),[]).append(item)

    def road_height(self,x,y):
        best=(float('inf'),0)
        for pts in self.roads.values():
            for a,b in zip(pts,pts[1:]):
                d,t=project(x,y,a,b)
                if d<best[0]:
                    best=(d,mix(a[2],b[2],t))
        return best[1]

    def height(self,x,y):
        z=natural(x,y)
        road=(0,0,float('inf'))
        pad=(0,0)
        locked=None
        for kind,*values in self.index.get((int(x//20),int(y//20)),()):
            if kind=='pad':
                rect,target,reach=values
                distance=rect_distance(x,y,rect)
                weight=1-smooth(distance/reach)
                # Hold flat pad grades one terrain cell beyond the editable slab.
                if distance <= 1.7 and reach <= 12 and locked is None:
                    locked=target
                if weight>pad[0]:
                    pad=(weight,target)
            else:
                a,b,hw,reach=values
                d,t=project(x,y,a,b)
                weight=1-smooth((d-hw)/reach)
                if weight>road[0] or (weight==road[0] and d<road[2]):
                    road=(weight,mix(a[2],b[2],t),d)
        z=locked if locked is not None else mix(mix(z,pad[1],pad[0]),road[1],road[0])
        if abs(x-265)<6 and 135<y<164:
            # Keep the terrain collision below the bridge. The at-grade ends
            # return to the road surface outside the creek channel.
            w=(1-smooth((abs(x-265)-3.7)/2.3))*smooth(min(y-135,164-y)/2.0)
            z=mix(z,min(z,2.78),w)
        # Retain the continuous low-flow channel after road and approach grading.
        channel = 1-smooth((abs(y-creek_y(x))-4.4)/3.1)
        return mix(z,-4.0,channel)

    def surface(self,x,y):
        """Same diagonal interpolation as the triangulated Unreal ground."""
        s=self.STEP
        i=min(WIDTH//s-1,max(0,int(x//s)))
        j=min(HEIGHT//s-1,max(0,int(y//s)))
        u,v=clamp(x/s-i),clamp(y/s-j)
        a,b=self.grid[j][i:i+2]
        c,d=self.grid[j+1][i:i+2]
        return a+u*(b-a)+v*(d-b) if u>=v else a+v*(c-a)+u*(d-c)
