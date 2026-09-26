import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=3, geolocation={'latitude':54.0725,'longitude':9.9845,'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/?n3'); await pg.wait_for_timeout(3000)
        await pg.evaluate("chooseDest({lat:54.0850, lon:9.9750, name:'Test'})"); await pg.wait_for_timeout(3000)
        pts = await pg.evaluate("nav.pts")
        for q in pts[1:4]:
            await ctx.set_geolocation({'latitude':q[0],'longitude':q[1],'accuracy':5}); await pg.wait_for_timeout(800)
        await pg.evaluate("follow=true; map.setView([last.lat,last.lon],16)"); await pg.wait_for_timeout(4000)
        await pg.screenshot(path=r'C:\Users\cpete\AppData\Local\Temp\rc_nav3.png', clip={'x':0,'y':0,'width':390,'height':300})
        # alle Pfeilarten zeigen
        for a in ['→','↖','⟳','⚠']:
            await pg.evaluate(f"navShow('{a}','120 m','','',{{rest:'3,4 km',time:'18:05'}})"); await pg.wait_for_timeout(200)
            await pg.screenshot(path=rf'C:\Users\cpete\AppData\Local\Temp\rc_arrow_{ord(a)}.png', clip={'x':120,'y':0,'width':150,'height':80})
        print('errors', errs); await b.close()
asyncio.run(main())
