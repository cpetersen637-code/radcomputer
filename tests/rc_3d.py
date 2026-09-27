import asyncio, sys
from playwright.async_api import async_playwright
# 3D-Navi-Ansicht: Ziel wählen, Route nehmen, entlang der Route fahren, Screenshots vor/nach einer Abbiegung
OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\cpete\AppData\Local\Temp'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader', '--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390, 'height':844}, device_scale_factor=2,
                                  geolocation={'latitude':54.0725, 'longitude':9.9845, 'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        await pg.goto('http://localhost:8765/?t3d'); await pg.wait_for_timeout(4000)
        await pg.screenshot(path=OUT + r'\rc3d_0_start.png')
        await pg.evaluate("chooseDest({lat:54.0850, lon:9.9750, name:'Test'})"); await pg.wait_for_timeout(5000)
        await pg.screenshot(path=OUT + r'\rc3d_1_pick.png')
        # Route per Klick auf die Karte (Linie) auswählen testen, dann Los
        await pg.evaluate("$('routeGo').click()"); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=OUT + r'\rc3d_2_overview.png')
        await pg.evaluate("navigator.geolocation.clearWatch(watchId); $('startBtn').click()")
        steps = await pg.evaluate("nav.steps.map(s => [Math.round(s.d), s.a])")
        print('steps', steps)
        total = await pg.evaluate("nav.total")
        # entlang der Route fahren, 5 m/s
        async def ride_to(d0, d1):
            await pg.evaluate(f"""(async () => {{
              for (let d = {d0}; d <= {d1}; d += 5) {{
                const q = routeAt(d);
                onPos({{timestamp: Date.now(), coords:{{latitude:q[0], longitude:q[1], accuracy:5, speed:5, heading:null, altitude:null}}}});
                await new Promise(r => setTimeout(r, 60));
              }}
            }})()""")
        turn = next((s[0] for s in steps if s[1] not in ('↑', '🏁') and s[0] > 60), total / 2)
        await ride_to(0, turn - 60); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=OUT + r'\rc3d_3_before_turn.png')
        print('vor Abbiegung', await pg.evaluate("({pitch: map.getPitch().toFixed(0), bearing: map.getBearing().toFixed(0), zoom: map.getZoom().toFixed(1), follow, arrow: meEl.classList.contains('arrow')})"))
        await ride_to(turn - 55, turn + 60); await pg.wait_for_timeout(1500)
        await pg.screenshot(path=OUT + r'\rc3d_4_after_turn.png')
        print('nach Abbiegung', await pg.evaluate("({pitch: map.getPitch().toFixed(0), bearing: map.getBearing().toFixed(0)})"))
        # Verschieben schaltet Folgen ab, Zentrieren wieder an
        await pg.mouse.move(200, 250); await pg.mouse.down(); await pg.mouse.move(260, 300, steps=5); await pg.mouse.up()
        f1 = await pg.evaluate("follow")
        await pg.evaluate("$('centerBtn').click()"); await pg.wait_for_timeout(1200)
        print('follow nach Ziehen', f1, 'nach Zentrieren', await pg.evaluate("follow"))
        await pg.evaluate("endNav()"); await pg.wait_for_timeout(1500)
        print('nach Ende', await pg.evaluate("({pitch: map.getPitch().toFixed(0), bearing: map.getBearing().toFixed(0), tracks: trackPoints()})"))
        await pg.screenshot(path=OUT + r'\rc3d_5_ended.png')
        # Menü: Fahrten/Statistik öffnen, Rechtsklick-Popup
        await pg.mouse.click(200, 200, button='right'); await pg.wait_for_timeout(500)
        print('popup', await pg.evaluate("!!document.querySelector('.maplibregl-popup')"))
        print('errors', errs); await b.close()
asyncio.run(main())
