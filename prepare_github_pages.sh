#!/bin/sh
# GitHub Pages 用に PWA ファイルだけを _site/ にコピーする
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="$ROOT/_site"
rm -rf "$OUT"
mkdir -p "$OUT"
cp "$ROOT/thread_gps_pwa.html" "$ROOT/sw.js" "$ROOT/manifest.json" "$OUT/"
cp "$ROOT"/icon-*.png "$OUT/"
echo ""
echo "=== _site/ を GitHub Pages にデプロイ ==="
echo "1. git init && GitHub にリポジトリ作成"
echo "2. _site の中身を push（または .github/workflows/pages.yml を使う）"
echo "3. スマホで https://<user>.github.io/<repo>/thread_gps_pwa.html を開く"
echo "4. 記録を書き出す → 新URLで読み込む → オフライン準備 → ホームに追加"
echo ""
