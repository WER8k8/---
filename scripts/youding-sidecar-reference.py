#!/usr/bin/env python3

"""【仅开发 mock】禁止生产使用。健康探测返回 mode=mock，优丁 backend 不会将其计为已配置。"""

from __future__ import annotations



import argparse

import json

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from typing import Any





class Handler(BaseHTTPRequestHandler):

    def log_message(self, format: str, *args: Any) -> None:

        return



    def _json(self, code: int, body: dict[str, Any]) -> None:

        raw = json.dumps(body, ensure_ascii=False).encode()

        self.send_response(code)

        self.send_header("Content-Type", "application/json; charset=utf-8")

        self.send_header("Content-Length", str(len(raw)))

        self.end_headers()

        self.wfile.write(raw)



    def do_GET(self) -> None:

        if self.path == "/api/youding/health":

            self._json(

                200,

                {

                    "ok": True,

                    "mode": "mock",

                    "produces_output": False,

                    "service": "youding-sidecar-reference-DO-NOT-USE",

                },

            )

            return

        self._json(404, {"error": "not_found"})



    def do_POST(self) -> None:

        self._json(

            503,

            {

                "ok": False,

                "error_code": "MOCK_SIDECAR_DISABLED",

                "hint": "此为 mock 参考实现，请使用 scripts/youding-sidecar-real.py 或优丁内置真实链",

            },

        )





def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument("--host", default="127.0.0.1")

    parser.add_argument("--port", type=int, default=9900)

    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)

    print(f"MOCK sidecar (disabled) http://{args.host}:{args.port}")

    server.serve_forever()





if __name__ == "__main__":

    main()

