import asyncio, sys
from playwright.async_api import async_playwright
# Kompass (Norden/Fahrtrichtung oben), Drehen von Hand schaltet Folgen ab, Feedback öffnet GitHub-Issue
OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\cpete\AppData\Local\Temp'
RIDE = """(async () => {
  navigator.geolocation.clearWatch(watchId); $('startBtn').click();
  let t = Date.now(), lon = 9.9845;
  for (let i = 0; i < 15; i++) { t += 1000; lon += 5 / 65400;
    onPos({timestamp:t, coords:{latitude:54.0725, longitude:lon, accuracy:5, speed:5, heading:90, altitude:null}}); }
  await new Promise(r => setTimeout(r, 1300));
})()"""
ST = "({orient, bearing: +map.getBearing().toFixed(0), follow, needle: $('needle').getAttribute('transform'), ring: $('compass').classList.contains('hdg')})"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader', '--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390, 'height':844}, device_scale_factor=2,
                                  geolocation={'latitude':54.0725, 'longitude':9.9845, 'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/?cp'); await pg.wait_for_timeout(4000)
        await pg.evaluate(RIDE)
        print('Fahrtrichtung', await pg.evaluate(ST))
        await pg.screenshot(path=OUT + r'\rc_compass_hdg.png', clip={'x':0, 'y':0, 'width':390, 'height':120})
        await pg.click('#compass'); await pg.wait_for_timeout(1200)
        print('nach Tippen ', await pg.evaluate(ST), 'Hinweis:', await pg.inner_text('#orientTip'))
        await pg.click('#compass'); await pg.wait_for_timeout(1200)
        print('nochmal     ', await pg.evaluate(ST))
        await pg.evaluate("map.rotateTo(40, {duration:0}, {originalEvent:{}})"); await pg.wait_for_timeout(300)
        print('von Hand    ', await pg.evaluate(ST))
        await pg.evaluate("$('centerBtn').click()"); await pg.wait_for_timeout(1300)
        print('Zentrieren  ', await pg.evaluate(ST))
        # Feedback
        await pg.evaluate("window.open = (u) => { window._opened = u; }; window.confirm = () => true")
        await pg.click('#menuBtn'); await pg.click('[data-go=fb]')
        await pg.fill('#fbText', 'Kompass ist super\nzweite Zeile'); await pg.wait_for_timeout(200)
        print('Entwurf gespeichert:', await pg.evaluate("localStorage.getItem('fbDraft')"))
        await pg.screenshot(path=OUT + r'\rc_feedback.png')
        await pg.click('#fbSend'); await pg.wait_for_timeout(500)
        url = await pg.evaluate("window._opened")
        from urllib.parse import urlparse, parse_qs
        q = parse_qs(urlparse(url).query)
        print('URL:', url.split('?')[0]); print('Titel:', q['title'][0]); print('Text:\n' + q['body'][0])
        print('Entwurf danach:', await pg.evaluate("localStorage.getItem('fbDraft')"), 'Menü zu:', await pg.evaluate("$('menu').hidden"))
        print('errors', errs); await b.close()
asyncio.run(main())
