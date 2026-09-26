import asyncio
from playwright.async_api import async_playwright
JS = r"""
() => {
  // eigenes GPS abschalten, wir füttern onPos direkt
  navigator.geolocation.clearWatch(watchId);
  $('startBtn').click();
  let t = Date.now(), lat = 54.07, rnd = 1;
  const rand = () => (rnd = (rnd * 16807) % 2147483647) / 2147483647 - 0.5;
  const fix = (la, lo, o={}) => onPos({timestamp:t, coords:Object.assign({latitude:la, longitude:lo, accuracy:6,
     speed:null, altitude:null, altitudeAccuracy:8}, o)});
  const log = [];
  for (let i = 0; i < 300; i++) {           // 300 s mit 20 km/h = 1667 m, dabei 30 m Anstieg
    t += 1000; lat += 5.556 / 111200;
    const alt = 20 + 30 * Math.min(1, i / 200) + rand() * 6;      // ±3 m Rauschen
    let o = {altitude: alt, speed: 5.556};
    if (i === 50) o.speed = 150 / 3.6;                              // falscher GPS-Tempowert
    if (i === 100) { fix(lat + 0.0006, 9.98, {altitude: alt, speed: null}); continue; }  // 67-m-Sprung
    if (i === 150) { o.speed = null; t -= 700; }                      // Punkte nur 0,3 s auseinander
    if (i >= 200 && i < 210) o.speed = null;                        // GPS liefert kein Tempo
    fix(lat, 9.98, o);
    log.push(+$('speed').textContent);
  }
  return {dist: (distM/1000).toFixed(3), max: maxKmh.toFixed(1), maxShown: Math.max(...log), climb: climbM.toFixed(1), desc: descM.toFixed(1),
          altCell: $('alt').textContent};
}"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        ctx = await b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2, geolocation={'latitude':54.07,'longitude':9.98,'accuracy':5}, permissions=['geolocation'])
        pg = await ctx.new_page(); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/?sim'); await pg.wait_for_timeout(3000)
        print(await pg.evaluate(JS))
        await pg.evaluate("render(window._kmh||0)"); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=r'C:\Users\cpete\AppData\Local\Temp\rc_sim.png')
        print('errors', errs); await b.close()
asyncio.run(main())
