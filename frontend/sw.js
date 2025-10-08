const CACHE_NAME = "assets-v1";
const IMG_MATCHERS = [
  /\/cards\//,
  /\/karysel\//,
  /\/logo-.*\.(png|svg)/,
  /\/roadmap\.png/
];

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Только GET
  if (request.method !== "GET") return;

  const isImage = IMG_MATCHERS.some(rx => rx.test(url.pathname));
  if (isImage) {
    // cache-first для изображений
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      if (cached) return cached;

      try {
        const resp = await fetch(request, { cache: "no-store" });
        if (resp.ok) cache.put(request, resp.clone());
        return resp;
      } catch {
        return cached || Response.error();
      }
    })());
    return;
  }

  // Для остального — network-first
  event.respondWith((async () => {
    try {
      const resp = await fetch(request, { cache: "no-store" });
      return resp;
    } catch {
      const cache = await caches.open(CACHE_NAME);
      const fallback = await cache.match(request);
      return fallback || Response.error();
    }
  })());
});
