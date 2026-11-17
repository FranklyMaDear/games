const CACHE = 'pinvigo-v5-chat';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './photo.png',
  './logo-pinvigo.png',
  './og-share.png',
  './el.json',
  './en.json'
];

self.addEventListener('install', e => {
  // Cache each file separately so one missing file does not cancel the rest
  e.waitUntil(
    caches.open(CACHE)
      .then(c => Promise.all(ASSETS.map(a => c.add(a).catch(() => {}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.protocol !== 'http:' && url.protocol !== 'https:') return;

  const isNav = req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html');
  const isLangPack = url.origin === location.origin && /\/(el|en)\.json$/.test(url.pathname);

  // Network-first for HTML and the language packs, so a new translation is never stuck behind an old cache
  if (isNav || isLangPack) {
    e.respondWith(
      fetch(req).then(res => {
        if (res && res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => caches.match(req).then(c => c || (isNav ? caches.match('./index.html') : undefined)))
    );
    return;
  }

  // Everything else: cache first, refresh in the background
  e.respondWith(
    caches.match(req).then(cached => {
      const net = fetch(req).then(res => {
        if (res && res.ok && url.origin === location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return res;
      }).catch(() => cached);
      return cached || net;
    })
  );
});
