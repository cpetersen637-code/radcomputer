import asyncio
from playwright.async_api import async_playwright
T = r'C:\Users\cpete\AppData\Local\Temp'
SIM = r"""() => { navigator.geolocation.clearWatch(watchId); $('startBtn').click();
  let t = Date.now() - 900000, lat = 54.07, lon = 9.98;
  for (let i = 0; i < 400; i++) { t += 1000; lat += 4.5 / 111200; lon += (i > 200 ? 3 : 0) / 65000;
    onPos({timestamp:t, coords:{latitude:lat, longitude:lon, accuracy:6, speed:5.5, altitude:20 + i/10, altitudeAccuracy:8}}); }
  movingMs = 400000; return (distM/1000).toFixed(2); }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, geolocation={'latitude':54.0725,'longitude':9.9845,'accuracy':5}, permissions=['geolocation'], accept_downloads=True)
        pg = await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto('http://localhost:8765/?menu'); await pg.wait_for_timeout(3000)
        print('Fahrt km', await pg.evaluate(SIM))
        await pg.click('#resetBtn'); await pg.wait_for_timeout(800)
        print('nach Beenden Distanz:', await pg.inner_text('#dist'), 'rec', await pg.evaluate('rec.length'))
        await pg.click('#menuBtn'); await pg.wait_for_timeout(400)
        await pg.screenshot(path=T+r'\m_main.png')
        await pg.click('[data-go=rides]'); await pg.wait_for_timeout(600)
        print('Fahrten:', (await pg.inner_text('#rideList')).replace('\n',' | '))
        await pg.click('#rideList li'); await pg.wait_for_timeout(1500)
        print('Detail:', (await pg.inner_text('#rideInfo')).replace('\n',' '))
        await pg.screenshot(path=T+r'\m_ride.png')
        async with pg.expect_download() as dl: await pg.click('#rideShare')
        d = await dl.value; path = T+r'\m_test.gpx'; await d.save_as(path)
        g = open(path, encoding='utf-8').read(); print('GPX:', d.suggested_filename, g.count('<trkpt'), 'Punkte,', g.count('<trkseg>'), 'Segment(e),', '<ele>' in g, '<time>' in g)
        await pg.click('#mBack'); await pg.click('#mBack'); await pg.click('[data-go=stats]'); await pg.wait_for_timeout(600)
        print('Statistik:', (await pg.inner_text('#statsBox')).replace('\n',' | ').replace('\t',' '))
        await pg.screenshot(path=T+r'\m_stats.png')
        # GPX laden -> gespeichert + Navigation
        await pg.click('#mBack'); await pg.click('[data-go=gpx]')
        await pg.set_input_files('#gpxFile', path); await pg.wait_for_timeout(1500)
        print('GPX-Navi aktiv:', await pg.evaluate('nav && nav.mode'), '| Menü zu:', await pg.evaluate("$('menu').hidden"))
        await pg.click('#menuBtn'); await pg.click('[data-go=gpx]'); await pg.wait_for_timeout(600)
        print('GPX-Liste:', (await pg.inner_text('#gpxList')).replace('\n',' | '), '| Navi-beenden sichtbar (Hauptmenü):', await pg.evaluate("!$('mNavEnd').hidden"))
        # letzte Ziele
        await pg.evaluate("addRecent({lat:54.09, lon:9.97, name:'Christianstraße, Innenstadt'})")
        await pg.click('#mBack'); await pg.click('[data-go=dest]'); await pg.wait_for_timeout(300)
        print('Letzte Ziele:', (await pg.inner_text('#recentList')).replace('\n',' | '))
        await pg.screenshot(path=T+r'\m_dest.png')
        print('errors', errs); await b.close()
asyncio.run(main())
