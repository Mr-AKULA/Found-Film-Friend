const CACHE = 'fff-v5';
/* Only cache the shell — JS/CSS fetched fresh each time so updates apply instantly */
const STATIC = [
  '/Found-Film-Friend/',
  '/Found-Film-Friend/index.html',
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
  /* Never cache: API calls, CDN scripts, and our own JS/CSS (always fetch fresh) */
  if (url.includes('supabase.co') || url.includes('unpkg.com') || url.includes('fonts.') ||
      url.endsWith('.js') || url.endsWith('.css')) return;

  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).then(res => {
      if (res.ok && e.request.method === 'GET') {
        const clone = res.clone();
        caches.open(CACHE).then(c => c.put(e.request, clone));
      }
      return res;
    }))
  );
});
