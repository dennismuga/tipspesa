
const CACHE_NAME = 'tipspesa-pwa-v1';
const urlsToCache = [
    '/',
    '/plans.html',  // Main page (adjust if your entry is index.html)
    '/static/styles.css',
    '/static/plugin.css',
    '/static/main.css',
    '/static/logo.png',
    '/static/favicon.png',
    '/static/whatsapp.png',
    '/static/Subbackground.png',
    '/static/circles.min.js',
    '/static/plugin.js',
    'https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;600;700&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css',
    'https://unpkg.com/tailwindcss@^2/dist/tailwind.min.css',
    'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css',
    'https://code.jquery.com/jquery-3.4.1.min.js',
    'https://code.jquery.com/ui/1.12.1/jquery-ui.min.js',
    'https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js'
    // Add more static assets as needed (e.g., other images)
];
// Install event: Cache core files
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});
// Activate event: Clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
// Fetch event: Serve from cache, fallback to network
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Cache hit - return response
                if (response) {
                    return response;
                }
                // Clone request for network fetch
                return fetch(event.request).then(response => {
                    // Check if response is ok
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }
                    // Clone and cache new response
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(event.request, responseToCache);
                        });
                    return response;
                });
            }).catch(() => {
                // Network failed - serve offline page or fallback
                if (event.request.destination === 'document') {
                    return caches.match('/');  // Serve cached main page
                }
                return new Response('Offline - Please connect to the internet.', {
                    status: 503,
                    statusText: 'Service Unavailable'
                });
            })
    );
});