import asyncio, sys
from playwright.async_api import async_playwright
# Ohne Navi: Karte dreht in Fahrtrichtung (GPS-Kurs bzw. aus der Bewegung), bleibt flach
OUT = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\cpete\AppData\Local\Temp'
JS = """(async () => {
  navigator.geolocation.clearWatch(watchId); $('startBtn').click();
  let t = Date.now(), lat = 54.0725, lon = 9.9845; const out = [];
  const fix = (o) => onPos({timestamp: t, coords: Object.assign({latitude:lat, longitude:lon, accuracy:5, speed:5, heading:null, altitude:null}, o)});
  for (let i = 0; i < 20; i++) { t += 1000; lat += 5 / 111200; fix({}); }            // nach Norden, ohne GPS-Kurs
  await new Promise(r => setTimeout(r, 1300)); out.push(['Nord', camBearing.toFixed(0), map.getBearing().toFixed(0), map.getPitch()]);
  for (let i = 0; i < 20; i++) { t += 1000; lon += 5 / 65400; fix({}); }             // nach Osten
  await new Promise(r => setTimeout(r, 1300)); out.push(['Ost', camBearing.toFixed(0), map.getBearing().toFixed(0), map.getPitch()]);
  for (let i = 0; i < 10; i++) { t += 1000; lat -= 5 / 111200; fix({heading:180}); } // nach Süden mit GPS-Kurs
  await new Promise(r => setTimeout(r, 1300)); out.push(['Süd', camBearing.toFixed(0), map.getBearing().toFixed(0), map.getPitch()]);
  for (let i = 0; i < 10; i++) { t += 1000; fix({speed:0, latitude: lat + (i % 2 ? 3 : -3) / 111200}); }  // Stand mit Rauschen
  await new Promise(r => setTimeout(r, 1300)); out.push(['Stand', camBearing.toFixed(0), map.getBearing().toFixed(0), map.getPitch()]);
  return out;
})()"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader', '--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390, 'height':844}, device_scale_factor=2,
                                  geolocation={'latitude':54.0725, 'longitude':9.9845, 'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/?hd'); await pg.wait_for_timeout(4000)
        for r in await pg.evaluate(JS): print(r)
        await pg.screenshot(path=OUT + r'\rc_heading.png')
        await pg.click('#menuBtn'); await pg.wait_for_timeout(300)
        print('Menü:', (await pg.inner_text('#menu')).replace('\n', ' | '))
        print('Abstand oben:', await pg.evaluate("getComputedStyle(document.body).paddingTop"), await pg.evaluate("$('topShield').offsetHeight"))
        print('errors', errs); await b.close()
asyncio.run(main())
