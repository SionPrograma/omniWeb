const CACHE_NAME = 'omniweb-shell-v1.1';
const ASSETS = [
    '/shell/',
    '/shell/index.html',
    '/shell/style.css',
    '/shell/logbook.css',
    '/shell/creator.css',
    '/shell/main.js',
    '/shell/creator.js',
    '/shell/galaxy.js',
    '/shell/assets/logo.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&family=Outfit:wght@200;400;700&display=swap'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS);
        })
    );
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            );
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    // SECURITY/DEV BYPASS: Bypass SW for local development assets to avoid stale caches
    const url = new URL(event.request.url);
    const isLocal = url.hostname === 'localhost' || url.hostname === '127.0.0.1';

    // Strategy: Network First, falling back to cache
    // For local dev, we prefer the network to always see latest changes
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // If it's a valid GET response, update cache in background
                if (response && response.ok && event.request.method === 'GET' && !isLocal) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                // Network failed or offline, try cache
                return caches.match(event.request).then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    // If it's a page navigation and offline, return cached shell
                    if (event.request.mode === 'navigate') {
                        return caches.match('/shell/index.html');
                    }
                });
            })
    );
});
