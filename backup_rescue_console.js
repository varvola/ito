// Android / 古い PWA 用 — Mac の Chrome リモートデバッグのコンソールに貼り付けて実行
(async () => {
  const PREFIX = "thread_gps_pwa_";
  const data = {};
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith(PREFIX)) data[key] = localStorage.getItem(key);
  }
  const payload = {
    app: "ito",
    version: 1,
    exportedAt: new Date().toISOString(),
    shellVersion: "rescue",
    data
  };
  const json = JSON.stringify(payload, null, 2);
  const count = Object.keys(data).length;
  const filename = `ito-backup-${new Date().toISOString().slice(0, 10)}.json`;
  console.log(`糸の記録: ${count} 件`, payload);
  try {
    const file = new File([json], filename, { type: "application/json" });
    if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
      await navigator.share({ files: [file], title: "糸 記録" });
      console.log("共有シートを開きました");
      return;
    }
  } catch (err) {
    if (err && err.name === "AbortError") return;
  }
  try {
    await navigator.clipboard.writeText(json);
    alert(`クリップボードにコピーしました（${count}件）`);
  } catch (_) {
    copy(json);
    console.log("DevTools の copy(json) を実行しました。Mac 側クリップボードを確認してください。");
  }
})();
