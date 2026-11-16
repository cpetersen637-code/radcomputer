"""Layout-Schalter unten (Menü → Powermeter): aus = Start über volle Breite, an = Start schmal + Watt/Kadenz;
bleibt fest, auch nach Neuladen, Beenden und ohne verbundenes Gerät.
Start: python -m http.server 8765 im Repo, dann: python tests/rc_layout.py"""
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
        state = lambda: pg.evaluate("[Math.round($('startBtn').getBoundingClientRect().width), $('pw3').offsetParent !== null, $('cad').offsetParent !== null]")
        print('Standard (aus): Startbreite, Watt, Kadenz =', await state())
        await pg.screenshot(path=T+r'\lay_ohne.png', clip={'x':0,'y':560,'width':390,'height':284})
        await pg.click('#menuBtn'); await pg.click('[data-go=pm]'); await pg.click('#pmLayBtn')
        print('Schalter:', await pg.inner_text('#pmLayBtn'), '| an:', await state())
        await pg.click('#mClose'); await pg.reload(); await pg.wait_for_timeout(2500)
        print('nach Neuladen (kein Gerät):', await state(), '| Watt', await pg.inner_text('#pw3'))
        await pg.screenshot(path=T+r'\lay_mit.png', clip={'x':0,'y':560,'width':390,'height':284})
        await pg.evaluate("$('startBtn').click(); endRide()"); await pg.wait_for_timeout(500)
        print('nach Beenden:', await state())
        await pg.click('#menuBtn'); await pg.click('[data-go=pm]'); await pg.click('#pmLayBtn'); await pg.click('#mClose')
        print('wieder aus:', await state(), '| errors', errs); await b.close()
asyncio.run(main())
