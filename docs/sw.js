const CACHE = 'fff-v8';
const STATIC = [
  '/Found-Film-Friend/manifest.json',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(STATIC)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys =>
    Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
  ));
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = e.request.url;

  /* Skip: API calls, CDN, our own JS/CSS — always fresh */
  const path = new URL(url).pathname;
  if (url.includes('supabase.co') || url.includes('unpkg.com') || url.includes('fonts.') ||
      path.endsWith('.js') || path.endsWith('.css')) return;

  /* HTML pages: network-first so updates are instant; cache is offline fallback */
  if (e.request.mode === 'navigate' || url.endsWith('.html') ||
      url.endsWith('/Found-Film-Friend/') || url === self.registration.scope) {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
    return;
  }

  /* Everything else (manifest, images): cache-first */
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      if (res.ok && e.request.method === 'GET') {
        caches.open(CACHE).then(c => c.put(e.request, res.clone()));
      }
      return res;
    }))
  );
});
