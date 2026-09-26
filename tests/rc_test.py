import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        try: b = await p.chromium.launch()
        except Exception: b = await p.chromium.launch(channel='msedge')
        ctx = await b.new_context(geolocation={'latitude':54.07,'longitude':9.98,'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/'); await pg.wait_for_timeout(1500)
        await pg.click('#startBtn')
        lat=54.07
        for i in range(8):   # ~5,5 m pro Sekunde ≈ 20 km/h
            lat+=0.00005; await ctx.set_geolocation({'latitude':lat,'longitude':9.98,'accuracy':5}); await pg.wait_for_timeout(1000)
        await pg.click('#startBtn')  # Pause
        lat+=0.01                     # 1,1 km während der Pause
        await ctx.set_geolocation({'latitude':lat,'longitude':9.98,'accuracy':5}); await pg.wait_for_timeout(1200)
        await pg.click('#startBtn')  # Weiter
        for i in range(4):
            lat+=0.00005; await ctx.set_geolocation({'latitude':lat,'longitude':9.98,'accuracy':5}); await pg.wait_for_timeout(1000)
        t1 = await pg.inner_text('#time')
        await pg.wait_for_timeout(7000)   # keine neuen Punkte -> Zeit muss stehen
        t2 = await pg.inner_text('#time')
        ride = json.loads(await pg.evaluate("localStorage.getItem('ride')"))
        await pg.reload(); await pg.wait_for_timeout(1500)
        segs = await pg.evaluate("track.getLatLngs().length")
        tiles = await pg.evaluate("[...document.querySelectorAll('.leaflet-tile')].slice(0,1).map(t=>t.src)")
        print('dist', await pg.inner_text('#dist'), 'max', await pg.inner_text('#max'))
        print('time vor/nach 7s Signalverlust', t1, t2, '| status', await pg.inner_text('#status'))
        print('Abschnitte gespeichert', len(ride['track']), [len(s) for s in ride['track']], 'nach Reload', segs)
        print('tile', tiles, 'errors', errs)
        await b.close()
asyncio.run(main())
