"""Layout-Schalter unten (Menü → Powermeter): ohne = Steigung/Gesamtzeit, mit = Watt/Kadenz; bleibt fest, auch nach Neuladen
und ohne verbundenes Gerät. Start: python -m http.server 8765 im Repo, dann: python tests/rc_layout.py"""
import asyncio
from playwright.async_api import async_playwright
T = r'C:\Users\cpete\AppData\Local\Temp'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, geolocation={'latitude':54.0725,'longitude':9.9845,'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto('http://localhost:8765/'); await pg.wait_for_timeout(2500)
        vis = lambda: asyncio.gather(*[pg.is_visible(s) for s in ('#pw3', '#cad', '#grade', '#total')])
        print('Standard (ohne):', await vis())
        # Fahrt bergauf: 5 m pro Punkt, 0,25 m höher → 5 %
        await pg.evaluate("""() => { navigator.geolocation.clearWatch(watchId); $('startBtn').click(); rideT0 = Date.now() - 125000;
          let t = Date.now() - 100000, lat = 54.07;
          for (let i = 0; i < 100; i++) { t += 1000; lat += 5 / 111200;
            onPos({timestamp:t, coords:{latitude:lat, longitude:9.98, accuracy:5, speed:5, altitude:20 + i * 0.25, altitudeAccuracy:5}}); } }""")
        await pg.wait_for_timeout(1200)
        print('Steigung:', await pg.inner_text('#grade'), '| Gesamtzeit:', await pg.inner_text('#total'))
        await pg.screenshot(path=T+r'\lay_ohne.png', clip={'x':0,'y':560,'width':390,'height':284})
        await pg.click('#menuBtn'); await pg.click('[data-go=pm]'); await pg.click('#pmLayBtn')
        print('Schalter:', await pg.inner_text('#pmLayBtn'), '| nach an:', await vis())
        await pg.click('#mClose'); await pg.evaluate('save()'); await pg.reload(); await pg.wait_for_timeout(2500)
        print('nach Neuladen (kein Gerät):', await vis(), '| Watt', await pg.inner_text('#pw3'), '| Gesamtzeit', await pg.inner_text('#total'))
        await pg.screenshot(path=T+r'\lay_mit.png', clip={'x':0,'y':560,'width':390,'height':284})
        await pg.evaluate('endRide()'); await pg.wait_for_timeout(500)
        print('nach Beenden:', await vis(), '| Gesamtzeit', await pg.inner_text('#total'))
        await pg.click('#menuBtn'); await pg.click('[data-go=pm]'); await pg.click('#pmLayBtn'); await pg.click('#mClose')
        print('wieder aus:', await vis(), '| errors', errs); await b.close()
asyncio.run(main())
