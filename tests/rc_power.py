"""Powermeter-Test mit simuliertem Bluetooth-Gerät (navigator.bluetooth wird vorgetäuscht).
Start: python -m http.server 8765 im Repo, dann: python tests/rc_power.py"""
import asyncio, re
from playwright.async_api import async_playwright
T = r'C:\Users\cpete\AppData\Local\Temp'
# Falsches Gerät: sendet alle 667 ms (= 90 rpm) einen Messwert mit Kurbeldaten (Flag 0x20), Leistung 180–220 W
FAKE = r"""
(() => {
  const listeners = {}, chL = [];
  let timer = null, revs = 0, t = 0, n = 0;
  const ch = { addEventListener:(e, f) => chL.push(f),
    startNotifications: async () => { timer = setInterval(() => {
      revs = (revs + 1) % 65536; t = (t + 683) % 65536; n++;
      const b = new DataView(new ArrayBuffer(8)); b.setUint16(0, 0x20, true); b.setInt16(2, n % 2 ? 180 : 220, true);
      b.setUint16(4, revs, true); b.setUint16(6, t, true);
      chL.forEach(f => f({target:{value:b}})); }, 667); } };
  const dev = { id:'fake1', name:'Assioma Duo', addEventListener:(e, f) => (listeners[e] = listeners[e] || []).push(f),
    gatt:{ connect: async () => ({ getPrimaryService: async u => { if (u !== 0x1818) throw new Error('svc'); return { getCharacteristic: async c => ch }; } }),
           disconnect: () => { clearInterval(timer); (listeners.gattserverdisconnected || []).forEach(f => f()); } } };
  window._fakeDrop = () => { clearInterval(timer); (listeners.gattserverdisconnected || []).forEach(f => f()); };
  Object.defineProperty(navigator, 'bluetooth', { value:{ requestDevice: async o => { window._req = o; return dev; } } });
})();
"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='msedge', args=['--enable-unsafe-swiftshader','--use-angle=swiftshader'])
        mk = lambda: b.new_context(viewport={'width':390,'height':844}, device_scale_factor=2,
            geolocation={'latitude':54.0725,'longitude':9.9845,'accuracy':5}, permissions=['geolocation'], accept_downloads=True)
        # 1) Browser ohne Bluetooth (wie Safari): Hinweis auf Bluefy
        ctx = await mk(); pg = await ctx.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("Object.defineProperty(navigator, 'bluetooth', {value: undefined})")
        await pg.goto('http://localhost:8765/'); await pg.wait_for_timeout(2000)
        await pg.click('#menuBtn'); await pg.click('[data-go=pm]'); await pg.wait_for_timeout(300)
        print('ohne BT: Hinweis sichtbar', await pg.is_visible('#pmNoBt'), '| Buttons sichtbar', await pg.is_visible('#pmBtns'),
              '| URL', await pg.inner_text('#pmUrl'), '| Watt-Zeile', await pg.evaluate("$('btns').classList.contains('pw')"))
        await pg.screenshot(path=T+r'\pm_nobt.png'); await ctx.close()

        # 2) Mit simuliertem Powermeter
        ctx = await mk(); pg = await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.add_init_script(FAKE)
        await pg.goto('http://localhost:8765/'); await pg.wait_for_timeout(2500)
        await pg.click('#menuBtn'); await pg.click('[data-go=pm]'); await pg.click('#pmConn'); await pg.wait_for_timeout(2500)
        print('Filter:', await pg.evaluate('JSON.stringify(_req)'), '| Status', await pg.inner_text('#pmStateV'),
              '| Gerät', await pg.inner_text('#pmNameV'), '| jetzt', await pg.inner_text('#pmNowV'), '| Menü', await pg.inner_text('#pmMenu'))
        await pg.screenshot(path=T+r'\pm_menu.png')
        await pg.click('#mClose')
        # Fahrt in Echtzeit simulieren (Sekundentakt zählt Leistung), 12 s
        await pg.evaluate("""() => { navigator.geolocation.clearWatch(watchId); $('startBtn').click();
          let lat = 54.07, lon = 9.98; window._sim = setInterval(() => { lat += 5.5 / 111200;
            onPos({timestamp:Date.now(), coords:{latitude:lat, longitude:lon, accuracy:6, speed:5.5, altitude:20, altitudeAccuracy:8}}); }, 500); }""")
        await pg.wait_for_timeout(12000)
        print('Anzeige: 3s', await pg.inner_text('#pw3'), '| Ø', await pg.inner_text('#pwAvg'), '| Kadenz', await pg.inner_text('#cad'),
              '| pwN', await pg.evaluate('pwN'), '| rec mit Watt', await pg.evaluate('rec.filter(r => r[5] != null).length'), '/', await pg.evaluate('rec.length'))
        await pg.screenshot(path=T+r'\pm_dash.png')
        await pg.click('#menuBtn'); await pg.wait_for_timeout(300)
        print('Menü: Fahrt-beenden sichtbar', await pg.is_visible('#mRideEnd'))
        await pg.click('[data-go=pm]'); await pg.wait_for_timeout(300)
        print('PM-Menü:', (await pg.inner_text('#menu .mview[data-v=pm] .kv')).replace('\n', ' '))
        await pg.screenshot(path=T+r'\pm_menu2.png'); await pg.click('#mClose')
        print('Zentrieren-Knopf:', await pg.evaluate("JSON.stringify($('centerBtn').getBoundingClientRect())"), '| Menü-Knopf', await pg.evaluate("JSON.stringify($('menuBtn').getBoundingClientRect())"))
        print('Abstand oben (Browser):', await pg.evaluate("getComputedStyle(document.body).paddingTop"))
        # Verbindung reißt ab → Anzeige --, Neuverbindung nach ~2 s
        await pg.evaluate('_fakeDrop()'); await pg.wait_for_timeout(300)
        print('nach Abriss:', await pg.evaluate('PM.state'), '| 3s', await pg.inner_text('#pw3'))
        await pg.wait_for_timeout(3500)
        print('nach Neuverbindung:', await pg.evaluate('PM.state'), '| 3s', await pg.inner_text('#pw3'))
        # Neuladen mitten in der Fahrt: Ø-Werte bleiben erhalten
        avg_before = await pg.inner_text('#pwAvg')
        await pg.evaluate('clearInterval(_sim); save()')
        await pg.reload(); await pg.wait_for_timeout(2500)
        print('nach Neuladen: Ø', await pg.inner_text('#pwAvg'), '(vorher', avg_before + ') | Zeile sichtbar', await pg.evaluate("$('btns').classList.contains('pw')"), '| 3s', await pg.inner_text('#pw3'))
        # Beenden → gespeicherte Fahrt mit Leistung
        await pg.evaluate('distM = 200'); await pg.evaluate('endRide()'); await pg.wait_for_timeout(800)
        print('nach Beenden Zeile sichtbar:', await pg.evaluate("$('btns').classList.contains('pw')"))
        await pg.click('#menuBtn'); await pg.click('[data-go=rides]'); await pg.wait_for_timeout(600)
        print('Liste:', (await pg.inner_text('#rideList')).replace('\n', ' | '))
        await pg.click('#rideList li'); await pg.wait_for_timeout(1200)
        print('Detail:', (await pg.inner_text('#rideInfo')).replace('\n', ' '))
        await pg.screenshot(path=T+r'\pm_ride.png')
        async with pg.expect_download() as dl: await pg.click('#rideShare')
        d = await dl.value; path = T+r'\pm_test.gpx'; await d.save_as(path)
        g = open(path, encoding='utf-8').read()
        print('GPX: power', g.count('<power>'), 'cad', g.count('<gpxtpx:cad>'), 'trkpt', g.count('<trkpt'), '| ns', 'xmlns:gpxtpx' in g)
        print('  Beispiel:', re.search(r'<trkpt[^\n]*<power>[^\n]*', g).group(0)[:220])
        await pg.click('#mBack'); await pg.click('#mBack'); await pg.click('[data-go=stats]'); await pg.wait_for_timeout(600)
        print('Statistik:', (await pg.inner_text('#statsBox')).replace('\n', ' | ').replace('\t', ' '))
        print('errors', errs); await b.close()
asyncio.run(main())
