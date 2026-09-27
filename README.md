# Radcomputer

Ein einfacher Fahrradcomputer als Web-App (PWA) fürs iPhone: Karte mit gefahrener Strecke, großer Tacho, Distanz, Fahrzeit, Schnitt, Max, Höhe und Uhrzeit. Dunkles, schlichtes Design. Kein Backend, kein Login, kein API-Key. Die Web-App besteht aus statischen Dateien.

> **Für Claude (Terminal):** Lies diese Datei komplett. Abschnitt „Offene Punkte“ ist die To-do-Liste. Abschnitt „Kontext & Randbedingungen“ erklärt, warum Dinge so gebaut sind, wie sie sind. Bitte nichts davon ohne Rückfrage umbauen.

---

## Dateien

| Datei | Zweck |
|---|---|
| `index.html` | Die komplette App: HTML, CSS und JavaScript in einer Datei |
| `manifest.json` | Web-App-Manifest (Name, Icons, Vollbild) → „Zum Home-Bildschirm“ |
| `sw.js` | Service Worker: Offline-Cache für App-Dateien und Kartenkacheln |
| `icon-180.png` | Apple-Touch-Icon (iPhone Home-Bildschirm) |
| `icon-192.png`, `icon-512.png` | Icons fürs Manifest |
| `keepawake.mp4`, `keepawake.webm` | Stummes 2-Sekunden-Video (16×16 px, schwarz), hält den Bildschirm an (siehe unten) |
| `README.md` | Diese Datei |
| `CLAUDE.md` | Kurzverweis für Claude Code auf diese README |

---

## Funktionen (Stand jetzt)

- **Karte:** MapLibre GL 4.7.1 direkt (via unpkg-CDN; bis v14 Leaflet + Plugin, das konnte nicht kippen/drehen). Vektorkarte von **OpenFreeMap** (OSM-Daten, kostenlos, ohne Key), Basis-Stil „liberty“, per `darkStyle()` komplett umgefärbt (Farben in `MAPCOL` oben im Script). Wenn der Stil nicht lädt: OSM-Rasterkarte grau/invertiert (Stil `RASTER`). Ohne WebGL keine Karte, der Tacho läuft trotzdem. Gebäude mit Höhe (nur in der 3D-Ansicht sichtbar). Eigene Linien (Route, Strecke, Vorschläge, Fahrt) als GeoJSON-Quellen in `OV`, werden nach jedem Stilwechsel per `addOverlays()` neu eingehängt. (CARTO verlangt seit 2026 einen API-Key.) Folgt der Position. Wer die Karte verschiebt, schaltet das Folgen ab, „Zentrieren“ schaltet es wieder ein.
- **Tacho:** Nimmt `coords.speed` vom GPS, sonst Strecke ÷ Zeit (nur zwischen zwei genauen Punkten ≥ 1 s auseinander). Werte > 90 km/h werden verworfen, angezeigt wird der Median der letzten 3 Werte (einzelne Ausreißer kommen nicht durch, auch nicht ins Max). Unter 1,5 km/h wird 0 angezeigt.
- **Distanz:** Haversine ab dem letzten Streckenpunkt (`lastGood`). Punkt zählt nur bei Genauigkeit < 30 m, Abstand > 3 m und Streckentempo < 90 km/h (so wird auch langsames Fahren korrekt summiert). Nach Start/Weiter beginnt ein neuer Streckenabschnitt, die Strecke während der Pause zählt nicht.
- **Fahrzeit:** Zählt nur, wenn Tempo > 0 und der letzte GPS-Punkt jünger als 5 s ist (bei Signalverlust steht die Zeit, Anzeige „Kein GPS-Signal“).
- **Schnitt:** Distanz ÷ Bewegungszeit. **Max:** höchstes geglättetes Tempo bei guter Genauigkeit.
- **Höhenmeter:** Summe der Anstiege (↑). GPS-Höhe wird geglättet (gleitender Mittelwert), gezählt wird erst ab 5 m Änderung (Glättungsfaktor 0,15, per Simulation abgestimmt), Punkte mit Höhengenauigkeit > 25 m werden ignoriert. Abstieg wird intern mitgezählt (`descM`), aber nicht angezeigt.
- **Menü** (☰ unten links auf der Karte): **Feedback** (Textfeld, Entwurf in `localStorage` `fbDraft`; „Senden“ öffnet ein vorausgefülltes GitHub-Issue in diesem Repo mit App-Version, Gerät und Ansicht, ohne Standort. Feedback also unter Issues nachsehen), Ziel suchen (mit „Letzte Ziele“, max. 8, `localStorage` `recent`), Routen (GPX laden/gespeicherte Routen), Gefahrene Fahrten (Liste → Strecke auf der Karte, Werte, **GPX teilen** über das iOS-Teilen-Menü bzw. Download, Nachfahren, Löschen), Statistik (Woche/Monat/Jahr/Gesamt: Fahrten, km, Zeit, Höhenmeter + Rekorde), „Navigation beenden“ bei aktiver Navi.
- **Beenden** (früher Reset): speichert die Fahrt (ab 50 m) in IndexedDB (`radcomputer` → `rides`) und setzt zurück. Aufgezeichnet wird dafür `rec` = [lat, lon, Zeit s, Höhe, Abschnittsbeginn]. GPX-Routen liegen in `gpx`.
- **Navigation** (Ziel über das Menü):
  - Ziel per **Adresssuche** (Nominatim/OSM, bevorzugt Treffer in der Nähe), **letzte Ziele**, **langes Drücken auf die Karte** oder **GPX-Route** (z. B. aus Komoot/Strava).
  - **Routenauswahl:** nach der Zielwahl mehrere Varianten farbig auf der Karte + Liste (km · min · Anzahl Abbiegungen, Markierung „Kürzeste“ / „Wenigste Abbiegungen“), antippen (Liste oder Linie) hebt die Route hervor und zoomt darauf, „Los“ startet. Varianten: **Valhalla** auf dem FOSSGIS-Server (`valhalla1.openstreetmap.de`, bicycle/Hybrid, `use_roads` 0,5 mit 2 Alternativen, dazu `use_roads` 0,9 = mehr Hauptstrecken, weniger Abbiegen) und **OSRM** (`routing.openstreetmap.de/routed-bike`). Fast gleiche Routen (90 % der Punkte < 25 m) werden aussortiert. Valhalla war im Test (40 Routen) ~16 % kürzer als OSRM.
  - `removeBacktracks`: Kommt eine Route nach > 80 m wieder auf < 25 m an eine frühere Stelle (oder den Startpunkt) zurück (typisch: einseitiger Radweg → erst weg, wenden, auf der anderen Seite zurück), wird das Stück durch den direkten Weg ersetzt.
  - Neuberechnung unterwegs nutzt die gewählte Variante (`nav.profile`), ohne erneute Auswahl.
  - **3D-Ansicht von hinten** (`camUpdate()`): Solange eine Navigation läuft und die Karte folgt, ist die Karte gekippt (Pitch 58°), die Fahrtrichtung zeigt nach oben und die eigene Position (flacher grüner Pfeil) sitzt im unteren Teil, die Route liegt davor. Richtung = Verlauf der Route 25 m voraus (`updateBearing()`), neben der Route der GPS-Kurs. Kamera gleitet in 1 s zur nächsten Position; ist sie weit weg (Zoom < 13 oder > 1 km, z. B. direkt nach dem Öffnen), springt sie sofort hin. Nach „Los“ geht es sofort in die 3D-Ansicht, auch im Stand. Bereits gefahrener Teil der Route wird ausgeblendet. Zwei-Finger-Zoom ändert den Navi-Zoom (`navZoom`, Standard 16,5), Verschieben schaltet das Folgen ab, „Zentrieren“ zurück in die 3D-Ansicht. Ohne Navigation flach, aber ebenfalls in Fahrtrichtung gedreht (Position etwas unter der Mitte); Richtung aus dem GPS-Kurs, sonst aus der Bewegung ab 12 m (`hdgRef`), im Stand bleibt sie stehen. Eigene Position ist immer ein Pfeil in Fahrtrichtung. **Drehen** mit zwei Fingern möglich (schaltet das Folgen ab wie Verschieben), Kippen per Geste ist abgeschaltet. **Kompass** oben links: Nadel zeigt nach Norden; antippen wechselt zwischen „Fahrtrichtung oben“ (grüner Ring) und „Norden oben“ (grauer Ring), gemerkt in `localStorage` `orient`, schaltet Folgen wieder an.
  - Anzeige oben, frei auf der Karte (ohne Kachel): mittig nur die nächste Abbiegung als blauer Pfeil + Meter, oben rechts 🏁 mit Rest-km und Ankunftszeit untereinander (Ankunft nach eigenem Schnitt, sonst 18 km/h). Scharfe dunkle Kontur (paint-order/-webkit-text-stroke) statt weichem Schatten.
  - Mehr als 40 m neben der Route (3 GPS-Punkte hintereinander) → Route wird neu berechnet (höchstens alle 10 s). Bei GPX-Routen nur Warnung „neben der Route“ mit Abstand, ohne Abbiegehinweise.
  - Ziel erreicht bei < 25 m Rest. Navigation wird in `localStorage` (Schlüssel `nav`) gesichert und beim Öffnen wiederhergestellt.
  - Funktioniert unabhängig von Start/Pause (Navi geht auch ohne Aufzeichnung).
- **Start / Pause / Weiter / Beenden** (Beenden mit Sicherheitsabfrage).
- **Fahrt wird gesichert** in `localStorage` (Schlüssel `ride`): bei jedem GPS-Punkt, alle 5 s während der Fahrt und bei Start/Pause/Reset. Beim Öffnen wird sie wiederhergestellt, der Knopf zeigt dann „Weiter“.
- **Bildschirm bleibt an** während der Fahrt (Wake Lock API + Video-Trick, siehe unten).
- **Offline:** Die App startet ohne Netz. Schon angesehene Kartenkacheln kommen aus dem Cache (max. ca. 2000 Kacheln).
- **Querformat:** Karte links, Anzeigen rechts.
- **Oben:** Als Home-Bildschirm-App legt iOS einen Weichzeichner unter die Statusleiste, der bis in die Karte reicht (im Safari-Tab nicht). Lösung (vom Nutzer am iPhone bestätigt): fester deckender Streifen `#topShield` + 32 px Abstand (`body` padding-top). Der frühere Umschalter mit Varianten und Messwerten ist entfernt.

---

## Kontext & Randbedingungen (wichtig)

1. **Gerät: iPhone, und zwar ein Firmenhandy mit MDM.** Die Organisation erzwingt eine Auto-Sperre von max. 1 Minute, das lässt sich nicht ändern. Deshalb:
   - Wake Lock API (`navigator.wakeLock`) funktioniert in Safari ab iOS 16.4, als Home-Screen-App zuverlässig erst ab iOS 18.4.
   - **Fallback „Video-Trick“:** Ein unsichtbares, stummes, in Schleife laufendes `<video playsinline muted loop>` wird beim Tippen auf Start abgespielt. iOS lässt den Bildschirm bei laufendem Video an (gleiche Ausnahme wie bei Video-Apps). Das Video muss durch eine Nutzeraktion gestartet werden, darum passiert das im Start-Button. Alle 10 s wird geprüft, ob es noch läuft (z. B. nach einem Anruf), sonst neu gestartet.
   - `keepawake.mp4` ist H.264 (für iPhone). `keepawake.webm` (VP8) ist Fallback für Browser ohne H.264 (z. B. Chromium in Tests).
2. **Web-Apps auf iOS bekommen bei gesperrtem Bildschirm kein GPS.** Deshalb muss der Bildschirm an bleiben. Das Drücken der Seitentaste unterbricht die Aufzeichnung trotzdem.
3. **GPS braucht HTTPS** (oder `localhost`). Einfaches `http://` über das Heimnetz funktioniert auf dem iPhone nicht.
4. **Karte absichtlich OpenStreetMap statt Google Maps:** Google Maps JS API braucht einen API-Key mit Kreditkarte. Der Nutzer wollte ursprünglich Google Maps, OSM ist bewusst der kostenlose Ersatz (siehe offene Punkte).
5. **Nach Änderungen an Dateien** die Cache-Version in `sw.js` erhöhen (`const APP = 'radcomputer-v14'` → `v15` usw.), sonst sieht das iPhone die alte Version. Neue Dateien auch in die `CORE`-Liste in `sw.js` eintragen.

---

## Hosting

### Variante A: GitHub Pages (empfohlen, PC muss nicht laufen)

1. GitHub-Konto anlegen, neues **öffentliches** Repository, z. B. `radcomputer`.
2. Alle Dateien aus diesem Ordner hochladen (Web: „Add file → Upload files“, oder per git, siehe unten).
3. Repository → **Settings → Pages** → Source: „Deploy from a branch“, Branch `main`, Ordner `/ (root)` → Save.
4. Nach ca. 1 Minute erreichbar unter `https://<github-name>.github.io/radcomputer/`.

Per Terminal (wenn `git` und `gh` installiert sind):

```bash
cd radcomputer
git init && git add . && git commit -m "Radcomputer"
gh repo create radcomputer --public --source=. --push
gh api -X POST repos/{owner}/radcomputer/pages -f "source[branch]=main" -f "source[path]=/"
```

Update später: Dateien ändern, Cache-Version in `sw.js` erhöhen, `git commit -am "…" && git push`.

### Variante B: Auf dem eigenen PC hosten

Nur sinnvoll, wenn der PC während der Fahrt läuft (die App ist danach aber offline-fähig).

```bash
cd radcomputer
python -m http.server 8000
```

Dann HTTPS davor, eine der beiden Optionen:

- **Cloudflare Tunnel** (öffentliche https-Adresse, ändert sich bei jedem Start):
  `cloudflared tunnel --url http://localhost:8000`
- **Tailscale** (nur eigene Geräte, sicherer; Tailscale-App auch aufs iPhone, aber Achtung Firmenhandy/MDM, evtl. nicht erlaubt):
  `tailscale serve 8000`

Lokal testen am PC: `http://localhost:8000` (GPS im Desktop-Browser ist ungenau/WLAN-basiert).

---

## Auf dem iPhone installieren

1. Die https-Adresse **in Safari** öffnen (nicht Chrome, nur Safari kann auf iOS „Zum Home-Bildschirm“ als App).
2. Teilen-Symbol → **„Zum Home-Bildschirm“**.
3. App vom Home-Bildschirm starten → **Standortzugriff erlauben** („Beim Verwenden der App“).
4. **Test:** Start tippen, iPhone 2 Minuten hinlegen, Bildschirm muss anbleiben.
5. Nach Updates: App im App-Umschalter ganz schließen und neu öffnen.

---

## Offene Punkte (To-do)

Nach Priorität. Vor dem Umsetzen kurz mit dem Nutzer abstimmen.

1. **Fahrzeit bei Lücken korrigieren.** Wenn der Bildschirm kurz gesperrt war und die App weiterläuft, wird die Lücke als gerade Linie verbunden (Distanz ≈ ok), aber die Fahrzeit der Lücke fehlt → Schnitt zu hoch. Idee: Beim nächsten GPS-Punkt nach einer Lücke (> 5 s seit letztem Punkt) die Zeit dazurechnen, wenn Luftlinie ÷ Zeit ein plausibles Tempo ergibt (z. B. 3–60 km/h). Außerdem die Fahrzeit auf GPS-Zeitstempeln statt auf `setInterval` aufbauen (Timer laufen im Hintergrund nicht).
2. ~~**Fahrtenverlauf + GPX-Export.**~~ (erledigt: Menü → Gefahrene Fahrten) „Fahrt beenden“ speichert die Fahrt in eine Liste (IndexedDB oder localStorage), Export als `.gpx` (Teilen-Menü auf iOS via `navigator.share` mit Datei oder Download-Link) für Strava/Komoot. Dafür Punkte mit Zeitstempel und Höhe speichern (aktuell nur lat/lon).
3. ~~Höhenmeter bergauf~~ (erledigt)
4. **Beim Wiederherstellen** optional direkt fragen „Fahrt fortsetzen?“ statt nur den Knopf auf „Weiter“ zu setzen.
5. **Google Maps (optional).** Nur falls gewünscht: Google Maps JS API mit eigenem Key (Google Cloud, Kreditkarte, Key auf die eigene Domain beschränken). Alternativ in MapLibre eine hellere Kartenvariante oder Satellit (z. B. Esri World Imagery) als umschaltbare Ebene anbieten, ist kostenlos.
6. **Heller Modus / Sonnenlicht-Modus** (hoher Kontrast bei Sonne).
7. **MapLibre lokal einbinden** statt über unpkg (dann keine Abhängigkeit von einem CDN; Dateien in den Ordner legen und in `sw.js` cachen).
8. **Später evtl. native iOS-App** (Swift/SwiftUI oder Flutter), die auch bei gesperrtem Bildschirm aufzeichnet und Bluetooth-Sensoren (Trittfrequenz, Puls) kann. Braucht einen Mac + Apple-Entwicklerkonto (99 €/Jahr). Bei einem Firmen-iPhone evtl. durch MDM eingeschränkt.

---

### Erledigt: „oben verschwommen“ nur als Home-Bildschirm-App (27.09.2026)

- Variante 3 (fester Streifen + 32 px Abstand) hat laut Nutzer geholfen und ist jetzt fest eingebaut, Umschalter und Messwerte sind raus. Vorher ohne Erfolg: Statusleiste `black` statt `black-translucent`, `text-shadow` statt `-webkit-text-stroke`, Variante 1 und 2.

## Tests

`tests/` enthält Playwright-Skripte (Python, Edge per `channel='msedge'`, Server: `python -m http.server 8765` im Projektordner, Ausgabe mit `PYTHONIOENCODING=utf-8`). Screenshots landen in `%TEMP%`.
- `rc_3d.py` – Ziel wählen, Los, entlang der Route fahren: prüft 3D-Ansicht (Pitch/Richtung vor und nach einer Abbiegung), Folgen/Zentrieren, Rechtsklick-Popup
- `rc_los.py` – im Stand Route wählen → sofort 3D; Neuladen mit gespeicherter Route → direkt 3D ohne Gleitflug
- `rc_compass.py` – Kompass umschalten, Drehen von Hand → Folgen aus, Zentrieren; Feedback-URL (Titel/Text/Infos)
- `rc_heading.py` – ohne Navi: Karte dreht in Fahrtrichtung (mit/ohne GPS-Kurs), bleibt im Stand ruhig
- `rc_sim.py` – simulierte Fahrt mit Tempo-Ausreißern, GPS-Sprüngen und Höhenrauschen (prüft Filter, Max, Höhenmeter)
- `rc_menu.py` – Beenden/Speichern, Fahrtenliste, GPX-Export, Statistik, GPX-Import, letzte Ziele
- `rc_alt.py`, `rc_pick.py` – Routenauswahl, removeBacktracks, Neuberechnung
- `rc_nav3.py` – Navi-Anzeige; `rc_test.py` – Pause/Signalverlust/Abschnitte
- `cmp.py`, `cmp2.py` – Vergleich OSRM vs. Valhalla (Umwege/Wenden) an Zufallsrouten

## Bekannte Einschränkungen

- Seitentaste gedrückt / Bildschirm gesperrt → keine GPS-Punkte in der Zeit.
- Adresssuche und Routenberechnung brauchen Netz (die Route selbst bleibt nach dem Berechnen offline nutzbar, Neuberechnung aber nicht). Keine Sprachansage.
- Bildschirm an kostet Akku, bei langen Touren Powerbank.
- Höhenmeter aus GPS-Höhe (Web-Apps haben keinen Zugriff aufs Barometer), daher ungefähr ±10 % gegenüber Strava/Garmin.
- `localStorage` wird gelöscht, wenn Website-Daten in Safari gelöscht werden. iOS kann Daten von Web-Apps, die mehrere Wochen nicht geöffnet wurden, ebenfalls löschen.
- Kartendaten von OpenFreeMap (kostenlos, ohne Limit für normale Nutzung). Offline: Vektorkacheln, Schriften und Sprites werden gecacht, Stil/TileJSON Netz zuerst.

---

## Technische Notizen

- Keine Build-Tools, kein npm nötig. Einfach Dateien bearbeiten.
- Zentrale Zustandsvariablen in `index.html`: `running`, `distM`, `maxKmh`, `movingMs`, `last`, `trackSegs` (Liste von Abschnitten aus [lat, lon]), `newSeg`, `lastFixAt`.
- Wichtige Funktionen: `onPos` (GPS-Verarbeitung), `render` (Anzeige), `save`/`restore` (localStorage), `keepAwake` (Wake Lock + Video).
- Navigation: `nav` (aktive Route), `planRoutes` (Varianten + Auswahl), `routeTo` (Neuberechnung), `routeValhalla`/`routeOsrm`, `removeBacktracks`, `sameRoute`, `valStep`/`stepText` (Manöver → Pfeil), `project` (Position auf Route projizieren), `updateNav` (bei jedem GPS-Punkt), `searchPlace` (Nominatim), `loadGpx`. `sw.js` cached Nominatim/Routing (OSRM, Valhalla) absichtlich nicht.
- Farben als CSS-Variablen in `:root` (`--accent` grün `#3ddc97`, `--warn` orange für Pause).
- Getestet: Headless Chromium mit simuliertem GPS: keine JS-Fehler, Start/Pause, Speichern, Keep-Awake-Video läuft. **Nicht** getestet: echtes iPhone (Nutzer testet selbst).
