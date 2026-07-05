#!/bin/sh
# GitHub に初回 push する手順を案内する
set -e
USER="${1:-}"
if [ -z "$USER" ]; then
  echo "用法: ./push_to_github.sh <GitHubユーザー名>"
  echo "例:   ./push_to_github.sh taro"
  exit 1
fi

REPO="ito"
REMOTE="https://github.com/${USER}/${REPO}.git"

cd "$(dirname "$0")"

if git remote get-url origin >/dev/null 2>&1; then
  echo "origin は既に設定されています: $(git remote get-url origin)"
else
  git remote add origin "$REMOTE"
  echo "remote を追加: $REMOTE"
fi

cat <<EOF

=== 次の操作（ブラウザ + ターミナル）===

【1】ブラウザでリポジトリを作成（まだなら）
    https://github.com/new
    - Repository name: ${REPO}
    - Public
    - README / .gitignore / license は追加しない

【2】このターミナルで push
    git push -u origin main

【3】Pages を有効化（初回のみ）
    https://github.com/${USER}/${REPO}/settings/pages
    - Build and deployment → Source: GitHub Actions

【4】1〜2分待ってデプロイ確認
    https://github.com/${USER}/${REPO}/actions

【5】スマホで開く
    https://${USER}.github.io/${REPO}/thread_gps_pwa.html

    記録を書き出す → 読み込む → オフライン準備 → ホームに追加

EOF
