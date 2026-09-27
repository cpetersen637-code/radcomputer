import asyncio, sys
from playwright.async_api import async_playwright
# Im Stand (ohne Start) Route wählen → sofort 3D-Ansicht; App neu laden mit gespeicherter Route → direkt 3D, ohne Gleitflug
OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\cpete\AppData\Local\Temp'
CAM = "({pitch: +map.getPitch().toFixed(0), bearing: +map.getBearing().toFixed(0), zoom: +map.getZoom().toFixed(1), follow, nav: !!nav})"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader', '--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390, 'height':844}, device_scale_factor=2,
                                  geolocation={'latitude':54.0725, 'longitude':9.9845, 'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/?los'); await pg.wait_for_timeout(4000)
        print('vor Route   ', await pg.evaluate(CAM))
        await pg.evaluate("chooseDest({lat:54.0850, lon:9.9750, name:'Test'})"); await pg.wait_for_timeout(5000)
        print('Auswahl     ', await pg.evaluate(CAM))
        await pg.evaluate("$('routeGo').click()"); await pg.wait_for_timeout(1500)
        print('nach Los    ', await pg.evaluate(CAM))
        await pg.screenshot(path=OUT + r'\rc_los.png')
        await pg.reload(); await pg.wait_for_timeout(300)
        samples = []
        for _ in range(12):
            samples.append(await pg.evaluate(CAM)); await pg.wait_for_timeout(250)
        print('nach Neuladen:')
        for s in samples: print('  ', s)
        print('errors', errs); await b.close()
asyncio.run(main())
