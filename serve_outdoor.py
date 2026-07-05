#!/usr/bin/env python3
"""屋外 GPS テスト用 — モバイル回線から HTTPS で開けるようにする

家の WiFi 圏外でも、PC のローカルサーバーをインターネット経由で公開します。
Cloudflare の Quick Tunnel を使うので、証明書警告なしの HTTPS になります。

使い方:
  python3 serve_outdoor.py

表示された URL をスマホ（モバイルデータ）で開く:
  https://xxxx.trycloudflare.com/thread_gps_pwa.html
"""

from __future__ import annotations

import http.server
import io
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request

PORT = 8767
APP_PATH = "/thread_gps_pwa.html"
DIR = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(DIR, "bin")
CLOUDFLARED = os.path.join(BIN_DIR, "cloudflared")

URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.I)
LOCALHOST_RUN_PATTERN = re.compile(r"https://[a-z0-9-]+\.lhr\.life", re.I)


def log(msg: str) -> None:
    print(msg, flush=True)


def local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        return "127.0.0.1"


def cloudflared_download_url() -> str:
    machine = platform.machine().lower()
    arch = "arm64" if machine in ("arm64", "aarch64") else "amd64"
    return f"https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-{arch}.tgz"


def ensure_cloudflared() -> str | None:
    if os.path.isfile(CLOUDFLARED) and os.access(CLOUDFLARED, os.X_OK):
        return CLOUDFLARED

    on_path = shutil.which("cloudflared")
    if on_path:
        return on_path

    if sys.platform != "darwin":
        return None

    log("")
    log("cloudflared が見つかりません。初回のみダウンロードします…")
    os.makedirs(BIN_DIR, exist_ok=True)

    url = cloudflared_download_url()
    try:
        with urllib.request.urlopen(url, timeout=120) as resp:
            data = resp.read()
    except Exception as err:
        log(f"  ダウンロード失敗: {err}")
        return None

    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
            tar.extractall(BIN_DIR)
    except Exception as err:
        log(f"  展開失敗: {err}")
        return None

    if not os.path.isfile(CLOUDFLARED):
        log("  cloudflared バイナリが見つかりません")
        return None

    os.chmod(CLOUDFLARED, 0o755)
    log("  cloudflared を bin/ に配置しました")
    return CLOUDFLARED


def start_http_server() -> http.server.HTTPServer:
    os.chdir(DIR)

    class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            path = self.path.split("?", 1)[0]
            if path.endswith((".html", ".js")) or path.endswith("manifest.json"):
                self.send_header("Cache-Control", "no-store, must-revalidate")
            super().end_headers()

    server = http.server.HTTPServer(("127.0.0.1", PORT), NoCacheHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def wait_for_url(proc: subprocess.Popen[str], pattern: re.Pattern[str], timeout: float = 90.0) -> str | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = proc.stdout.readline() if proc.stdout else ""
        if not line:
            if proc.poll() is not None:
                break
            time.sleep(0.2)
            continue
        sys.stdout.write(line)
        sys.stdout.flush()
        match = pattern.search(line)
        if match:
            return match.group(0)
    return None


def start_cloudflared_tunnel(binary: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [binary, "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def start_localhost_run_tunnel() -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-R", f"80:127.0.0.1:{PORT}",
            "nokey@localhost.run",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )


def print_usage(base_url: str, method: str) -> None:
    app_url = base_url.rstrip("/") + APP_PATH
    log("")
    log("=== 屋外 GPS テスト用 URL ===")
    log(f"  方式: {method}")
    log(f"  スマホで開く: {app_url}")
    log("")
    log("  手順:")
    log("  1. 上の URL をスマホに送る（LINE / メモなど）")
    log("  2. モバイルデータ ON・WiFi OFF で開く")
    log("  3. GPS開始 → 散歩（10〜15分）")
    log("  4. ホーム画面に追加すると次回も使いやすい")
    log("")
    log("  ※ データはスマホ内に保存されます（localStorage）")
    log("  ※ ページを開いたままなら、途中で PC が落ちても記録は続きます")
    log("  ※ 停止: Ctrl+C")
    log("")


def main() -> int:
    os.chdir(DIR)
    server = start_http_server()
    ip = local_ip()

    log("")
    log("=== 屋外 GPS テスト — トンネル起動中 ===")
    log(f"  ローカル: http://127.0.0.1:{PORT}{APP_PATH}")
    log(f"  家の WiFi 内: http://{ip}:{PORT}{APP_PATH} （HTTP・GPS不可）")
    log("")

    tunnel_proc: subprocess.Popen[str] | None = None
    base_url: str | None = None
    method = ""

    cloudflared_bin = ensure_cloudflared()
    if cloudflared_bin:
        log("Cloudflare Tunnel を起動しています…")
        tunnel_proc = start_cloudflared_tunnel(cloudflared_bin)
        base_url = wait_for_url(tunnel_proc, URL_PATTERN)
        method = "Cloudflare Tunnel（HTTPS・証明書 OK）"

    if not base_url:
        if tunnel_proc and tunnel_proc.poll() is None:
            tunnel_proc.terminate()
        log("")
        log("Cloudflare が使えないため、SSH トンネル（localhost.run）を試します…")
        tunnel_proc = start_localhost_run_tunnel()
        base_url = wait_for_url(tunnel_proc, LOCALHOST_RUN_PATTERN, timeout=120.0)
        if not base_url:
            # localhost.run sometimes prints a different host
            base_url = wait_for_url(tunnel_proc, re.compile(r"https://[^\s]+\.localhost\.run", re.I), timeout=5.0)
        method = "SSH トンネル localhost.run（HTTPS）"

    if not base_url:
        log("")
        log("トンネルの起動に失敗しました。")
        log("  - インターネット接続を確認")
        log("  - もう一度 python3 serve_outdoor.py")
        log("  - または手動: brew install cloudflared && cloudflared tunnel --url http://127.0.0.1:8767")
        server.shutdown()
        return 1

    print_usage(base_url, method)

    try:
        while True:
            if tunnel_proc and tunnel_proc.poll() is not None:
                log("")
                log("トンネルが終了しました。Ctrl+C でサーバーを止めてください。")
                tunnel_proc = None
            time.sleep(1)
    except KeyboardInterrupt:
        log("")
        log("停止しました")
        if tunnel_proc and tunnel_proc.poll() is None:
            tunnel_proc.terminate()
        server.shutdown()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
