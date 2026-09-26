import asyncio, json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, geolocation={'latitude':54.0725,'longitude':9.9845,'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/?alt'); await pg.wait_for_timeout(3000)
        await pg.evaluate("chooseDest({lat:54.0950, lon:9.9600, name:'Test'})")
        await pg.wait_for_selector('#routeList li', timeout=30000); await pg.wait_for_timeout(2500)
        print('Auswahl:'); print(await pg.inner_text('#routeList'))
        await pg.screenshot(path=r'C:\Users\cpete\AppData\Local\Temp\rc_alt.png')
        await pg.click('#routeList li:nth-child(2)'); await pg.wait_for_timeout(1500)
        print('Profil:', await pg.evaluate("JSON.stringify(nav.profile)"), 'Punkte', await pg.evaluate("nav.pts.length"))
        # Rückweg-Test: removeBacktracks mit künstlichem Hin-und-zurück am Start
        print('Backtrack-Test:', await pg.evaluate("""(() => {
          const s = {lat:54.0725, lon:9.9845};
          const pts = [[54.0725,9.9845],[54.0735,9.9845],[54.0745,9.9845],[54.0745,9.98475],[54.0735,9.98475],[54.0725,9.98475],[54.0715,9.98475],[54.0705,9.98475]];
          const r = removeBacktracks(pts, [{d:0,a:'↑',t:''},{d:222,a:'⤺',t:''},{d:400,a:'→',t:''}], s);
          return r.pts.length + ' Punkte, Länge ' + Math.round(cumDist(r.pts).pop()) + ' m (vorher ' + Math.round(cumDist(pts).pop()) + ' m), Schritte ' + r.steps.map(x=>x.a+Math.round(x.d)).join(' ');
        })()"""))
        # Reroute mit gewähltem Profil
        await pg.evaluate("routeTo(nav.dest, last, false, nav.profile)"); await pg.wait_for_timeout(3000)
        print('Reroute ok, Profil', await pg.evaluate("JSON.stringify(nav.profile)"))
        await pg.screenshot(path=r'C:\Users\cpete\AppData\Local\Temp\rc_alt2.png', clip={'x':0,'y':0,'width':390,'height':200})
        print('errors', errs); await b.close()
asyncio.run(main())
