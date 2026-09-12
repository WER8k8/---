#!/usr/bin/env python3

"""YouDing 真实 sidecar（非 mock）：听写 → 英译 → edge-tts → ffmpeg 合成真实 mp4/srt。



启动（在 backend 虚拟环境中）:

  cd backend

  ..\\.venv\\Scripts\\python.exe ..\\scripts\\youding-sidecar-real.py --port 9901



环境:

  YOUDUB_WEBUI_BASE_URL=http://127.0.0.1:9901

  需 ffmpeg、edge-tts；听写需讯飞密钥或本机 faster-whisper。

"""

from __future__ import annotations



import argparse

import asyncio

import json

import os

import shutil

import sys

import threading

import time

import uuid

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pathlib import Path

from typing import Any

from urllib.parse import urlparse



ROOT = Path(__file__).resolve().parents[1]

BACKEND = ROOT / "backend"

if str(BACKEND) not in sys.path:

    sys.path.insert(0, str(BACKEND))



_JOBS: dict[str, dict[str, Any]] = {}





def _load_settings():

    os.chdir(BACKEND)

    from app.core.config import settings  # noqa: WPS433



    return settings





def _download_video(video_url: str, dest: Path) -> bool:

    import httpx



    try:

        with httpx.Client(timeout=300, follow_redirects=True) as client:

            resp = client.get(video_url)

            resp.raise_for_status()

            dest.write_bytes(resp.content)

        return dest.is_file() and dest.stat().st_size > 0

    except Exception:

        return False





def _resolve_local_video(video_url: str, uploads: Path) -> Path | None:

    if not video_url:

        return None

    part = video_url.split("?", 1)[0]

    if part.startswith("/uploads/"):

        candidate = uploads / part.removeprefix("/uploads/")

        return candidate if candidate.is_file() else None

    parsed = urlparse(part)

    if parsed.path.startswith("/uploads/"):

        candidate = uploads / parsed.path.removeprefix("/uploads/")

        return candidate if candidate.is_file() else None

    if part.startswith(("http://", "https://")):

        tmp = uploads / f"sidecar_in_{uuid.uuid4().hex[:10]}.mp4"

        return tmp if _download_video(part, tmp) else None

    path = Path(part)

    return path if path.is_file() else None





def _run_real_pipeline(job_id: str, payload: dict[str, Any]) -> None:

    try:

        from app.core.uploads_path import UPLOADS_DIR, ensure_uploads_dir

        from app.services.cross_border.audio_asr_service import transcribe_zh_from_media

        from app.services.cross_border.tts_service import (

            DEFAULT_VOICE,

            mux_video_with_audio,

            synthesize_english_mp3,

        )

        from app.services.cross_border.video_dub_service import _format_srt, _parse_json

        from app.services.ai_invocation_service import invoke_llm

        from app.core.database import SessionLocal



        ensure_uploads_dir()

        video_url = str(payload.get("video_url") or "")

        source = _resolve_local_video(video_url, UPLOADS_DIR)

        if not source:

            _JOBS[job_id] = {

                "status": "failed",

                "error": "VIDEO_NOT_FOUND",

                "hint": "无法读取 video_url 对应文件",

            }

            return



        _JOBS[job_id] = {"status": "running", "progress": 15, "hint": "听写中文…"}

        asr = transcribe_zh_from_media(source)

        if not asr.get("ok") or not str(asr.get("text") or "").strip():

            _JOBS[job_id] = {

                "status": "failed",

                "error": "ASR_FAILED",

                "hint": asr.get("error") or "听写失败，请配置讯飞或 faster-whisper",

            }

            return



        zh_text = str(asr["text"]).strip()

        _JOBS[job_id] = {"status": "running", "progress": 45, "hint": "翻译英文…"}



        prompt = (

            "把下方中文视频解说词译成英文配音稿。输出 JSON:\n"

            '{"script_en":"...","segments":[{"start":"00:00:00,000","end":"00:00:05,000","text_en":"..."}]}\n\n'

            f"中文:\n{zh_text}"

        )



        async def _translate() -> dict[str, Any]:

            db = SessionLocal()

            try:

                result = await invoke_llm(

                    db,

                    prompt=prompt,

                    scenario="inference",

                    max_tokens=1800,

                    lane="customer",

                )

                parsed = _parse_json(str(result.get("content") or ""))

                if not parsed.get("script_en"):

                    parsed["script_en"] = str(result.get("content") or "")

                if not parsed.get("segments"):

                    parsed["segments"] = [

                        {

                            "start": "00:00:00,000",

                            "end": "00:00:08,000",

                            "text_en": str(parsed.get("script_en") or "")[:200],

                        }

                    ]

                return parsed

            finally:

                db.close()



        translation = asyncio.run(_translate())

        segments = translation.get("segments") if isinstance(translation.get("segments"), list) else []

        srt_body = _format_srt(segments)

        dub_id = uuid.uuid4().hex[:12]

        srt_path = UPLOADS_DIR / f"sidecar_{dub_id}.srt"

        srt_path.write_text(srt_body, encoding="utf-8")



        _JOBS[job_id] = {"status": "running", "progress": 70, "hint": "合成英文配音…"}

        script_en = str(translation.get("script_en") or "").strip()



        async def _tts() -> Path | None:

            return await synthesize_english_mp3(script_en, voice=DEFAULT_VOICE)



        mp3 = asyncio.run(_tts())

        output_url = None

        audio_url = None

        if mp3 and mp3.is_file():

            audio_url = f"/uploads/{mp3.name}"

            out_path = UPLOADS_DIR / f"sidecar_{dub_id}_en.mp4"

            if mux_video_with_audio(source, mp3, out_path):

                output_url = f"/uploads/{out_path.name}"



        if not output_url and not srt_path.is_file():

            _JOBS[job_id] = {

                "status": "failed",

                "error": "NO_OUTPUT",

                "hint": "未生成 mp4 或 srt",

            }

            return



        _JOBS[job_id] = {

            "status": "done",

            "progress": 100,

            "hint": "完成",

            "result": {

                "output_url": output_url,

                "srt_url": f"/uploads/{srt_path.name}",

                "audio_url": audio_url,

                "transcript_zh": zh_text,

                "script_en": script_en,

                "output_mode": "opensource_dub" if output_url else "srt_only",

            },

        }

    except Exception as exc:

        _JOBS[job_id] = {

            "status": "failed",

            "error": "SIDEcar_PIPELINE_ERROR",

            "hint": str(exc)[:500],

        }





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

            ffmpeg_ok = bool(shutil.which("ffmpeg"))

            self._json(

                200,

                {

                    "ok": True,

                    "mode": "production",

                    "produces_output": True,

                    "service": "youding-sidecar-real",

                    "ffmpeg": ffmpeg_ok,

                },

            )

            return

        if self.path.startswith("/api/youding/jobs/"):

            job_id = self.path.rsplit("/", 1)[-1]

            job = _JOBS.get(job_id)

            if not job:

                self._json(404, {"error": "not_found"})

                return

            self._json(200, job)

            return

        self._json(404, {"error": "not_found"})



    def do_POST(self) -> None:

        if self.path != "/api/youding/translate-dub":

            self._json(404, {"error": "not_found"})

            return

        length = int(self.headers.get("Content-Length") or 0)

        raw = self.rfile.read(length) if length else b""

        payload: dict[str, Any] = {}

        ctype = (self.headers.get("Content-Type") or "").lower()

        if "application/json" in ctype and raw:

            try:

                data = json.loads(raw.decode())

                if isinstance(data, dict):

                    payload = data

            except json.JSONDecodeError:

                pass



        job_id = uuid.uuid4().hex[:12]

        _JOBS[job_id] = {"status": "queued", "progress": 5, "hint": "排队中"}

        threading.Thread(target=_run_real_pipeline, args=(job_id, payload), daemon=True).start()

        self._json(202, {"job_id": job_id, "status": "queued"})





def main() -> None:

    _load_settings()

    parser = argparse.ArgumentParser()

    parser.add_argument("--host", default="127.0.0.1")

    parser.add_argument("--port", type=int, default=9901)

    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)

    print(f"YouDing REAL sidecar http://{args.host}:{args.port} (mode=production)")

    server.serve_forever()





if __name__ == "__main__":

    main()

