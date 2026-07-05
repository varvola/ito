#!/bin/sh
# docs/ を GitHub Pages 用に最新化する（push 前に実行）
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT/docs"
cp "$ROOT/thread_gps_pwa.html" "$ROOT/docs/"
cp "$ROOT/thread_gps_pwa.html" "$ROOT/docs/index.html"
cp "$ROOT/sw.js" "$ROOT/manifest.json" "$ROOT/docs/"
cp "$ROOT"/icon-*.png "$ROOT/docs/"
touch "$ROOT/docs/.nojekyll"
echo "docs/ を更新しました"
