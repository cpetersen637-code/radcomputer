# Projekt: Radcomputer

Fahrradcomputer als Web-App (PWA) für ein iPhone (Firmenhandy, Auto-Sperre per MDM auf 1 Minute fest).

**Lies zuerst `README.md`.** Dort stehen Funktionen, Randbedingungen, Hosting-Anleitung und die offenen Punkte (To-do-Liste).

Regeln für Änderungen:
- Nach jeder Dateiänderung die Cache-Version in `sw.js` erhöhen (`radcomputer-vN`), neue Dateien in `CORE` eintragen.
- Keep-Awake (Wake Lock + stummes Video) und das Speichern in `localStorage` nicht entfernen, das ist wegen iOS/MDM nötig.
- Keine Build-Tools einführen, die App bleibt statisches HTML/JS.
- Offene Punkte vor dem Umsetzen kurz mit dem Nutzer abstimmen.
- Kommunikation mit dem Nutzer auf Deutsch.
