import json, math, random, time, urllib.request, urllib.parse
random.seed(7)
def hav(a,b):
    R=6371000; r=math.pi/180
    x=math.sin((b[0]-a[0])*r/2)**2+math.cos(a[0]*r)*math.cos(b[0]*r)*math.sin((b[1]-a[1])*r/2)**2
    return 2*R*math.asin(math.sqrt(x))
def backtrack(pts):
    cum=[0]
    for i in range(1,len(pts)): cum.append(cum[-1]+hav(pts[i-1],pts[i]))
    # dichte Punkte alle ~5 m
    dense=[]; 
    for i in range(1,len(pts)):
        n=max(1,int(hav(pts[i-1],pts[i])/5))
        for k in range(n): dense.append((pts[i-1][0]+(pts[i][0]-pts[i-1][0])*k/n, pts[i-1][1]+(pts[i][1]-pts[i-1][1])*k/n, cum[i-1]+(cum[i]-cum[i-1])*k/n))
    worst=0
    for i in range(0,len(dense),2):
        for j in range(i+1,len(dense),2):
            gap=dense[j][2]-dense[i][2]
            if gap>80 and hav(dense[i],dense[j])<20: worst=max(worst,gap)
    return round(worst)
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'radcomputer-test (cpetersen637-code)'})
    return json.load(urllib.request.urlopen(req,timeout=30))
def decode6(s):
    idx=lat=lon=0; out=[]
    while idx<len(s):
        for which in (0,1):
            res=shift=0
            while True:
                b=ord(s[idx])-63; idx+=1; res|=(b&0x1f)<<shift; shift+=5
                if b<0x20: break
            d=~(res>>1) if res&1 else res>>1
            if which==0: lat+=d
            else: lon+=d
        out.append((lat/1e6,lon/1e6))
    return out
rows=[]
for n in range(40):
    a=(54.06+random.random()*0.03, 9.96+random.random()*0.05); b=(54.06+random.random()*0.03, 9.96+random.random()*0.05)
    o=get(f"https://routing.openstreetmap.de/routed-bike/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson&steps=true")
    op=[(c[1],c[0]) for c in o['routes'][0]['geometry']['coordinates']]
    ou=sum(1 for s in o['routes'][0]['legs'][0]['steps'] if s['maneuver'].get('modifier')=='uturn')
    J={"locations":[{"lat":a[0],"lon":a[1]},{"lat":b[0],"lon":b[1]}],"costing":"bicycle","costing_options":{"bicycle":{"bicycle_type":"Hybrid","use_roads":0.5}},"directions_type":"maneuvers"}
    v=get("https://valhalla1.openstreetmap.de/route?json="+urllib.parse.quote(json.dumps(J)))
    vp=decode6(v['trip']['legs'][0]['shape'])
    vu=sum(1 for m in v['trip']['legs'][0]['maneuvers'] if m['type'] in (12,13))
    rows.append((round(o['routes'][0]['distance']), backtrack(op), ou, round(v['trip']['summary']['length']*1000), backtrack(vp), vu))
    time.sleep(1.1)
print('OSRM: Länge, Hin-und-zurück-Strecke(m), Wendungen | Valhalla: dito')
for r in rows: 
    if r[1] or r[2] or r[4] or r[5]: print(r)
ob=sum(1 for r in rows if r[1] or r[2]); vb=sum(1 for r in rows if r[4] or r[5])
print(f'Routen mit Hin-und-zurück/Wenden: OSRM {ob}/40, Valhalla {vb}/40; Gesamtlänge OSRM {sum(r[0] for r in rows)} m, Valhalla {sum(r[3] for r in rows)} m')
