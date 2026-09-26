// Offline-Cache: App-Dateien + zuletzt geladene Kartenkacheln
const APP = 'radcomputer-v9';
const TILES = 'radcomputer-tiles-osm';  // neuer Name: alte CARTO-Kacheln ("API key required") werden gelöscht
const CORE = [
  './', './index.html', './manifest.json', './icon-180.png', './icon-192.png', './icon-512.png', './keepawake.mp4', './keepawake.webm',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css',
  'https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js',
  'https://unpkg.com/@maplibre/maplibre-gl-leaflet@0.0.22/leaflet-maplibre-gl.js'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(APP).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== APP && k !== TILES).map(k => caches.delete(k)))
  ).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const url = e.request.url;
  if (e.request.method !== 'GET') return;
  // Adresssuche und Routing immer live aus dem Netz, nicht cachen
  if (url.includes('nominatim.openstreetmap.org') || url.includes('routing.openstreetmap.de')) return;

  // OpenFreeMap: Stil/TileJSON (ändern sich, verweisen auf aktuelle Kartenversion) Netz zuerst, offline aus dem Cache
  if (url.includes('tiles.openfreemap.org') && !/\.(pbf|pbf\?.*|png|json\?.*)$|\/fonts\/|\/sprites\//.test(url)) {
    e.respondWith(caches.open(TILES).then(c => fetch(e.request)
      .then(res => { if (res.ok) c.put(e.request, res.clone()); return res; })
      .catch(() => c.match(e.request).then(r => r || new Response('', {status: 504})))));
    return;
  }

  // Kartenkacheln, Schriften, Sprites: erst Cache, sonst Netz und merken (max. ~2000 Einträge)
  if (url.includes('tiles.openfreemap.org') || url.includes('tile.openstreetmap.org')) {
    e.respondWith(caches.open(TILES).then(async c => {
      const hit = await c.match(e.request);
      if (hit) return hit;
      try {
        const res = await fetch(e.request);
        if (res.ok || res.type === 'opaque') {
          c.put(e.request, res.clone());
          c.keys().then(k => { if (k.length > 2000) k.slice(0, k.length - 2000).forEach(r => c.delete(r)); });
        }
        return res;
      } catch (_) { return new Response('', {status: 504}); }
    }));
    return;
  }

  // App & Schriften: Netz zuerst (Updates), offline aus dem Cache
  e.respondWith(
    fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(APP).then(c => c.put(e.request, copy));
      return res;
    }).catch(() => caches.match(e.request).then(r => r || caches.match('./index.html')))
  );
});
