const CACHE = "ito-shell-v50";
const SHELL_PATH = "./thread_gps_pwa.html";
const PRECACHE = [
  SHELL_PATH,
  "./manifest.json",
  "./icon-180.png",
  "./icon-192.png",
  "./icon-512.png"
];

const OFFLINE_STUB = `<!doctype html>
<html lang="ja">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>糸 — オフライン</title>
  <style>
    body { margin: 0; padding: 24px; font-family: system-ui, sans-serif; background: #17202a; color: #fff; line-height: 1.6; }
    h1 { font-size: 20px; margin: 0 0 12px; }
    p { margin: 0 0 10px; opacity: 0.9; font-size: 14px; }
    ol { margin: 12px 0; padding-left: 20px; font-size: 14px; }
    li { margin-bottom: 8px; }
  </style>
</head>
<body>
  <h1>糸 — オフライン起動できません</h1>
  <p>この端末にアプリ本体がまだ保存されていません。</p>
  <ol>
    <li>ネットに接続する（家の Wi‑Fi かモバイル回線）</li>
    <li><a href="https://varvola.github.io/ito/thread_gps_pwa.html" style="color:#7dd3fc">本番URL</a>を開く</li>
    <li>「強制更新」または「オフライン準備」をタップ</li>
    <li>次からは <strong>ホーム画面のアイコン</strong> から開く</li>
  </ol>
  <p>記録は端末内に残っています。準備が終わればオフラインでも開けます。</p>
</body>
</html>`;

function isShellRequest(url) {
  const path = url.pathname;
  return path.endsWith("thread_gps_pwa.html")
    || path.endsWith("manifest.json")
    || path.endsWith("sw.js")
    || path.endsWith("/");
}

function fetchFresh(request) {
  return fetch(request, { cache: "no-store" });
}

function matchShell(cache, request) {
  return cache.match(request, { ignoreSearch: true })
    .then((hit) => hit || cache.match(SHELL_PATH, { ignoreSearch: true }));
}

function offlineStubResponse() {
  return new Response(OFFLINE_STUB, {
    status: 200,
    headers: { "Content-Type": "text/html; charset=utf-8" }
  });
}

function cacheShellResponse(cache, request, response) {
  if (!response || response.status !== 200) return Promise.resolve();
  // opaque/cors でも本体HTMLは basic のはず。失敗時は握りつぶさない
  if (response.type !== "basic" && response.type !== "cors" && response.type !== "default") {
    return Promise.resolve();
  }
  return Promise.all([
    cache.put(request, response.clone()),
    cache.put(SHELL_PATH, response.clone())
  ]);
}

async function matchAnyItoShell(request) {
  const keys = await caches.keys();
  const itoKeys = keys
    .filter((k) => k.startsWith("ito-shell-"))
    .sort()
    .reverse();
  // 新しいキャッシュを優先し、だめなら古い版の本体を返す
  for (const key of itoKeys) {
    const cache = await caches.open(key);
    const hit = await matchShell(cache, request);
    if (hit) return hit;
  }
  return null;
}

async function currentCacheHasShell() {
  const cache = await caches.open(CACHE);
  const hit = await cache.match(SHELL_PATH, { ignoreSearch: true });
  return !!hit;
}

function respondShell(request) {
  return caches.open(CACHE).then(async (cache) => {
    const cached = await matchShell(cache, request);
    if (cached) {
      fetchFresh(request)
        .then((response) => cacheShellResponse(cache, request, response))
        .catch(() => {});
      return cached;
    }

    try {
      const response = await fetchFresh(request);
      if (response && response.status === 200) {
        await cacheShellResponse(cache, request, response);
        return response;
      }
    } catch (_) {}

    const retry = await matchShell(cache, request);
    if (retry) return retry;

    // 新キャッシュが空でも、旧 ito-shell-* があれば起動を優先
    const legacy = await matchAnyItoShell(request);
    if (legacy) return legacy;

    return offlineStubResponse();
  });
}

async function precacheAll(cache) {
  let shellOk = false;
  for (const url of PRECACHE) {
    try {
      const response = await fetchFresh(url);
      if (response && response.status === 200) {
        await cache.put(url, response.clone());
        if (url === SHELL_PATH) shellOk = true;
      }
    } catch (_) {}
  }
  return shellOk;
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => precacheAll(cache))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    // 新本体が入ってから古いキャッシュを消す。空キャッシュで詰まるのを防ぐ
    const ready = await currentCacheHasShell();
    if (ready) {
      const keys = await caches.keys();
      await Promise.all(
        keys
          .filter((k) => k !== CACHE && k.startsWith("ito-shell-"))
          .map((k) => caches.delete(k))
      );
    }
    await self.clients.claim();
  })());
});

self.addEventListener("message", (event) => {
  if (!event.data) return;
  if (event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
    return;
  }
  if (event.data.type === "CACHE_SHELL") {
    event.waitUntil(
      caches.open(CACHE).then(async (cache) => {
        try {
          const response = await fetchFresh(SHELL_PATH);
          if (response && response.status === 200) {
            await cache.put(SHELL_PATH, response.clone());
          }
        } catch (_) {}
      })
    );
  }
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);

  if (event.request.mode === "navigate" || isShellRequest(url)) {
    event.respondWith(respondShell(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || response.type !== "basic") {
          return response;
        }
        const copy = response.clone();
        caches.open(CACHE).then((cache) => cache.put(event.request, copy));
        return response;
      }).catch(() => cached);
    })
  );
});
