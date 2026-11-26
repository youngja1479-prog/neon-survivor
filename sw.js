/* 네온 생존자 (루트 index.html) 서비스 워커
 * - index.html: network-first (항상 최신 + 오프라인 fallback)
 * - 매니페스트/아이콘: stale-while-revalidate
 * - heroes/(네온 서바이벌) 요청: 손대지 않고 네트워크로 그대로 통과
 * - 그 밖의 요청도 간섭하지 않는다.
 */
const CACHE = 'ns1-pwa-v1';
const SHELL = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

const abs = p => new URL(p, self.location.href).href;
const scopePath = () => new URL(self.registration.scope).pathname; // 예: /neon-survivor/

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    await Promise.all(SHELL.map(u => cache.add(new Request(abs(u), { cache: 'reload' })).catch(() => {})));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (e) { return; }
  if (url.origin !== self.location.origin) return;

  const base = scopePath();
  // 다른 앱(네온 서바이벌 = heroes/)은 이 워커가 건드리지 않는다.
  if (url.pathname === base + 'heroes' || url.pathname.indexOf(base + 'heroes/') === 0) return;

  const isDoc = req.mode === 'navigate' ||
    url.pathname === base || url.pathname === base + 'index.html';
  if (isDoc) { event.respondWith(networkFirst(req, base)); return; }

  if (url.pathname === base + 'manifest.json' || url.pathname.indexOf(base + 'icons/') === 0) {
    event.respondWith(staleWhileRevalidate(req, event));
  }
});

async function networkFirst(req, base) {
  const cache = await caches.open(CACHE);
  try {
    const res = await fetch(req);
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  } catch (err) {
    const hit = await cache.match(req, { ignoreSearch: true });
    if (hit) return hit;
    const shell = await cache.match(abs('./index.html'));
    if (shell) return shell;
    return new Response(
      '<!doctype html><meta charset="utf-8"><title>오프라인</title>' +
      '<body style="background:#07060f;color:#eef1ff;font-family:sans-serif;text-align:center;padding:48px">' +
      '<h1 style="color:#4df3ff">네온 생존자</h1><p>오프라인 상태입니다. 연결 후 다시 열어 주세요.</p></body>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  }
}

async function staleWhileRevalidate(req, event) {
  const cache = await caches.open(CACHE);
  const fresh = fetch(req).then(res => {
    if (res && res.ok) cache.put(req, res.clone());
    return res;
  }).catch(() => null);
  event.waitUntil(Promise.resolve(fresh));      // 캐시 갱신이 잘리지 않게
  const hit = await cache.match(req, { ignoreSearch: true });
  if (hit) return hit;
  const res = await fresh;
  if (res) return res;
  return new Response('', { status: 504, statusText: 'Offline' });
}
