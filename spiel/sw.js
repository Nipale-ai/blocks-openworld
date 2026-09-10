// sw.js — Runde 31 (Katalog #54): Offline-PWA für blocks-openworld/spiel.
// Cache-First für alle Asset-Dateien, Netz-Erst für index.html (Updates kommen sofort beim nächsten Online-Besuch).
const CACHE = 'blocks-v1';
const KERN = ['./', './index.html', './assets/manifest.js'];
self.addEventListener('install', (e) => { self.skipWaiting(); e.waitUntil(caches.open(CACHE).then(c => c.addAll(KERN)).catch(() => {})); });
self.addEventListener('activate', (e) => { e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim())); });
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url); if (e.request.method !== 'GET') return;
  if (url.pathname.endsWith('/index.html') || url.pathname.endsWith('/spiel/')) {
    e.respondWith(fetch(e.request).then(r => { caches.open(CACHE).then(c => c.put(e.request, r.clone())).catch(() => {}); return r.clone(); }).catch(() => caches.match(e.request).then(m => m || caches.match('./index.html'))));
    return;
  }
  e.respondWith(caches.match(e.request).then(m => m || fetch(e.request).then(r => { if (r.ok && url.origin === location.origin) { const k = r.clone(); caches.open(CACHE).then(c => c.put(e.request, k)).catch(() => {}); } return r; }).catch(() => m)));
});
