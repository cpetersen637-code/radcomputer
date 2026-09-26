import asyncio
from playwright.async_api import async_playwright
T = r'C:\Users\cpete\AppData\Local\Temp'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, geolocation={'latitude':54.0725,'longitude':9.9845,'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/?pick'); await pg.wait_for_timeout(3000)
        await pg.evaluate("chooseDest({lat:54.0950, lon:9.9600, name:'Test'})")
        await pg.wait_for_selector('#routeList li', timeout=30000); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=T+r'\p1.png')
        await pg.click('#routeList li:nth-child(3)'); await pg.wait_for_timeout(2000)
        print('nav nach Auswahl (soll null):', await pg.evaluate('!!nav'))
        await pg.screenshot(path=T+r'\p2.png')
        await pg.click('#routeGo'); await pg.wait_for_timeout(1500)
        print('nav nach Los:', await pg.evaluate('!!nav'), 'Punkte gleich gewählter Route:', await pg.evaluate('nav.pts.length'))
        print('errors', errs); await b.close()
asyncio.run(main())
