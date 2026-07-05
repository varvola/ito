# 糸

GPS位置ゲーム PWA。

## スマホ（本番）

https://varvola.github.io/ito/thread_gps_pwa.html

## GitHub Pages へ反映

```bash
./sync_docs.sh
git add docs/
git commit -m "Update PWA"
git push
```

Settings → Pages → **main** ブランチ / **/docs** フォルダ

## ローカル開発

```bash
python3 serve_https.py
python3 serve_outdoor.py
```
