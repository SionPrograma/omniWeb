const CACHE_NAME = 'omniweb-shell-v3';
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
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS);
        })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            );
        })
    );
});

self.addEventListener('fetch', (event) => {
    // Strategy: Network First, fallback to Cache
    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request).then((response) => {
                if (response) return response;
                if (event.request.mode === 'navigate') {
                    return caches.match('/shell/index.html');
                }
            });
        })
    );
});
