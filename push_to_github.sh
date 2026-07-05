#!/bin/sh
# GitHub に push する手順を案内する
set -e
USER="${1:-varvola}"
REPO="ito"
REMOTE="https://github.com/${USER}/${REPO}.git"

cd "$(dirname "$0")"
./sync_docs.sh

if git remote get-url origin >/dev/null 2>&1; then
  echo "origin: $(git remote get-url origin)"
else
  git remote add origin "$REMOTE"
  echo "remote を追加: $REMOTE"
fi

cat <<EOF

=== push ===
  git add -A && git commit -m "更新"   # 変更がある場合
  git push -u origin main

※ トークンは repo 権限だけでOK（workflow 不要）

=== Pages 有効化（初回のみ）===
  https://github.com/${USER}/${REPO}/settings/pages
  - Source: Deploy from a branch
  - Branch: main  /  Folder: /docs

=== スマホ URL ===
  https://${USER}.github.io/${REPO}/thread_gps_pwa.html

EOF
