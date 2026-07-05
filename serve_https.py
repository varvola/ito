#!/usr/bin/env python3
"""ローカル HTTPS サーバー（スマホ GPS テスト用）"""

import http.server
import os
import socket
import ssl
import subprocess
import sys

PORT = 8766
DIR = os.path.dirname(os.path.abspath(__file__))
CERT = os.path.join(DIR, "dev-cert.pem")
KEY = os.path.join(DIR, "dev-key.pem")


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        path = self.path.split("?", 1)[0]
        if path.endswith((".html", ".js")) or path.endswith("manifest.json"):
            self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()


def ensure_cert():
    if os.path.exists(CERT) and os.path.exists(KEY):
        return
    ip = local_ip()
    print(f"証明書を作成中（初回のみ）… IP: {ip}")
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048",
            "-keyout", KEY, "-out", CERT,
            "-days", "365", "-nodes",
            "-subj", f"/CN={ip}",
            "-addext", f"subjectAltName=IP:{ip},IP:127.0.0.1,DNS:localhost",
        ],
        check=True,
    )


def main():
    os.chdir(DIR)
    ensure_cert()

    handler = NoCacheHTTPRequestHandler
    server = http.server.HTTPServer(("0.0.0.0", PORT), handler)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(CERT, KEY)
    server.socket = ctx.wrap_socket(server.socket, server_side=True)

    ip = local_ip()
    url = f"https://{ip}:{PORT}/thread_gps_pwa.html"

    print("")
    print("=== スマホ GPS テスト用 HTTPS サーバー ===")
    print(f"  スマホで開く: {url}")
    print("")
    print("  ※ 「安全ではない」と出たら「詳細」→「続行」")
    print("  ※ 停止: Ctrl+C")
    print("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止しました")
        sys.exit(0)


if __name__ == "__main__":
    main()
