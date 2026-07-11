#!/bin/sh
# gh-pages ブランチを更新（GitHub Pages 用）
set -e
cd "$(dirname "$0")"
./sync_docs.sh
git add docs/
git diff --staged --quiet || git commit -m "Update docs for Pages"
git push origin main
git branch -D gh-pages 2>/dev/null || true
git subtree split --prefix docs -b gh-pages
git push -f origin gh-pages
echo ""
echo "完了。Settings → Pages → Branch: gh-pages / (root)"
