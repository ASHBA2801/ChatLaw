// ChatLaw service worker: installability plus an offline page, nothing more.
//
// Only full page navigations are handled. Everything else (Next.js RSC payloads
// such as /chat?_rsc=..., JS chunks, API calls) goes straight to the network:
// answering those from a cache or with offline.html breaks the app, and cached
// HTML from a previous deploy points at chunks that no longer exist.
const CACHE_NAME = "chatlaw-offline-v3";
const OFFLINE_URL = "/offline.html";
const PRECACHE = [OFFLINE_URL, "/icons/icon-192.png", "/icons/icon-512.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || request.mode !== "navigate") return;
  if (new URL(request.url).origin !== self.location.origin) return;

  event.respondWith(
    fetch(request).catch(async () => (await caches.match(OFFLINE_URL)) || Response.error()),
  );
});
