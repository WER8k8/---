#!/usr/bin/env python3
"""NVIDIA NIM → Cursor 本地代理：用 Cursor 认得的模型名，转发到真实 NVIDIA model id。"""

from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HOST = "127.0.0.1"
PORT = 8765
NVIDIA_BASE = "https://integrate.api.nvidia.com/v1"

# Cursor 可过校验的别名 → NVIDIA 真实 model id（本机实测可用）
MODEL_MAP: dict[str, str] = {
    "gpt-4o": "mistralai/mistral-large-3-675b-instruct-2512",
    "gpt-4o-mini": "deepseek-ai/deepseek-v4-flash",
    "gpt-4-turbo": "qwen/qwen3-coder-480b-a35b-instruct",
    "o1-mini": "meta/llama-3.3-70b-instruct",
    "gpt-4.1": "meta/llama-4-maverick-17b-128e-instruct",
    "gpt-4.1-mini": "nvidia/nemotron-3-super-120b-a12b",
}


def load_api_key() -> str:
    env = Path(__file__).resolve().parents[1] / "backend" / "config" / "dev" / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("AI_NVIDIA_API_KEY="):
                v = line.split("=", 1)[1].strip()
                if v:
                    return v
    key = os.environ.get("AI_NVIDIA_API_KEY", "").strip()
    if key:
        return key
    raise RuntimeError("未找到 AI_NVIDIA_API_KEY")


def map_model(name: str) -> str:
    return MODEL_MAP.get(name, name)


class Handler(BaseHTTPRequestHandler):
    api_key = ""

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[nvidia-proxy] {self.address_string()} - {fmt % args}\n")

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    def _forward(self, method: str, subpath: str, body: bytes | None = None) -> tuple[int, bytes, str]:
        url = f"{NVIDIA_BASE}/{subpath.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": self.headers.get("Content-Type", "application/json"),
        }
        data = body
        if body and subpath.rstrip("/").endswith("chat/completions"):
            try:
                payload = json.loads(body.decode("utf-8"))
                req_model = payload.get("model", "")
                payload["model"] = map_model(req_model)
                data = json.dumps(payload).encode("utf-8")
                self.log_message("map %s -> %s", req_model, payload["model"])
            except json.JSONDecodeError:
                pass

        req = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(req, timeout=120) as resp:
                return resp.status, resp.read(), resp.headers.get_content_type()
        except HTTPError as e:
            return e.code, e.read(), "application/json"
        except URLError as e:
            msg = json.dumps({"error": {"message": str(e.reason)}}).encode()
            return 502, msg, "application/json"

    def do_GET(self) -> None:
        if self.path.rstrip("/") in ("/v1/models", "/models"):
            status, raw, ctype = self._forward("GET", "models")
        elif self.path in ("/", "/health"):
            raw = json.dumps({"ok": True, "map": MODEL_MAP}).encode()
            status, ctype = 200, "application/json"
        else:
            status, raw, ctype = self._forward("GET", self.path.removeprefix("/v1/"))
        self.send_response(status)
        self.send_header("Content-Type", ctype or "application/json")
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:
        body = self._read_body()
        sub = self.path.removeprefix("/v1/").removeprefix("/")
        status, raw, ctype = self._forward("POST", sub, body)
        self.send_response(status)
        self.send_header("Content-Type", ctype or "application/json")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.end_headers()


def main() -> None:
    Handler.api_key = load_api_key()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"NVIDIA Cursor proxy http://{HOST}:{PORT}/v1")
    print("Cursor Base URL 填: http://127.0.0.1:8765/v1")
    print("模型映射:")
    for alias, real in MODEL_MAP.items():
        print(f"  {alias} -> {real}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
