exec(open(__import__('os').environ['TEMP']+'/cmp.py',encoding='utf-8').read().split('rows=[]')[0])
random.seed(11); rows=[]; starts=[]
# Startpunkte: Punkte mitten auf bereits berechneten Routen (also direkt auf Rad-/Straßenwegen, oft neben Parallelwegen)
while len(starts)<40:
    a=(54.06+random.random()*0.03, 9.96+random.random()*0.05); b=(54.06+random.random()*0.03, 9.96+random.random()*0.05)
    o=get(f"https://routing.openstreetmap.de/routed-bike/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson")
    cs=o['routes'][0]['geometry']['coordinates']
    for k in (len(cs)//3, 2*len(cs)//3):
        # 6 m seitlich versetzen (GPS-Ungenauigkeit / andere Straßenseite)
        starts.append((cs[k][1]+random.uniform(-6,6)/111000, cs[k][0]+random.uniform(-6,6)/65000))
    time.sleep(1.1)
for a in starts[:40]:
    b=(54.06+random.random()*0.03, 9.96+random.random()*0.05)
    o=get(f"https://routing.openstreetmap.de/routed-bike/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson&steps=true")
    op=[(c[1],c[0]) for c in o['routes'][0]['geometry']['coordinates']]
    ou=sum(1 for s in o['routes'][0]['legs'][0]['steps'] if s['maneuver'].get('modifier')=='uturn')
    J={"locations":[{"lat":a[0],"lon":a[1]},{"lat":b[0],"lon":b[1]}],"costing":"bicycle","costing_options":{"bicycle":{"bicycle_type":"Hybrid","use_roads":0.5}},"directions_type":"maneuvers"}
    v=get("https://valhalla1.openstreetmap.de/route?json="+urllib.parse.quote(json.dumps(J)))
    vp=decode6(v['trip']['legs'][0]['shape'])
    vu=sum(1 for m in v['trip']['legs'][0]['maneuvers'] if m['type'] in (12,13))
    rows.append((round(o['routes'][0]['distance']), backtrack(op), ou, round(v['trip']['summary']['length']*1000), backtrack(vp), vu, a))
    time.sleep(1.1)
for r in rows:
    if r[1] or r[2] or r[4] or r[5]: print(r)
ob=sum(1 for r in rows if r[1] or r[2]); vb=sum(1 for r in rows if r[4] or r[5])
print(f'Routen mit Hin-und-zurück/Wenden: OSRM {ob}/40, Valhalla {vb}/40; Gesamtlänge OSRM {sum(r[0] for r in rows)} m, Valhalla {sum(r[3] for r in rows)} m')
