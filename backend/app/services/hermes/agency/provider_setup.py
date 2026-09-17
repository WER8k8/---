# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Hermes agency LLM — 服务器/bootstrap 安装计划（非交互部分可脚本化）。"""

from __future__ import annotations

import os
import shutil
from typing import Any

from app.services.hermes.agency.llm_router import list_providers, probe_provider

# 生产推荐：API Key + 本地 Ollama；CLI OAuth 仅适合本机/跳板机一次性登录
SERVER_DEFAULT_CHAIN = "deepseek,ollama,openai,hermes-cli,gemini-cli,claude-code"
DEV_DEFAULT_CHAIN = "hermes-cli,ollama,gemini-cli,deepseek,claude-code,openai,claude"

_CLI_INSTALL = {
    "gemini-cli": {
        "npm": "@google/gemini-cli",
        "auth": "首次在本机或 SSH 交互终端执行: gemini -p hi（浏览器登录 Google）",
        "server_note": "无头服务器建议改用 gemini API Key + provider: openai + base_url",
    },
    "claude-code": {
        "npm": "@anthropic-ai/claude-code",
        "auth": "首次交互执行: claude（Anthropic 账号登录）",
        "server_note": "生产建议 AI_ANTHROPIC_API_KEY + provider: claude",
    },
    "copilot-cli": {
        "npm": "@github/copilot",
        "auth": "copilot 首次运行 GitHub 登录",
        "server_note": "云服务器不推荐；用 API",
    },
    "codex-cli": {
        "npm": "@openai/codex",
        "auth": "codex 首次 OpenAI 登录",
        "server_note": "云服务器不推荐；用 OPENAI_API_KEY",
    },
    "openclaw-cli": {
        "npm": "openclaw@latest",
        "auth": "openclaw onboard --install-daemon",
        "server_note": "易与 Hermes 环形调用，生产慎用",
    },
    "hermes-cli": {
        "install": "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash",
        "auth": "按 Hermes 文档配置 token；本仓库开发机已在 venv/Scripts/hermes.exe",
        "server_note": "可与 backend 同机部署 venv 内 hermes",
    },
}


def _ollama_steps() -> list[dict[str, Any]]:
    """_ollama_steps。
    :return: 返回处理结果。
    """
    model = os.environ.get("HERMES_AGENCY_OLLAMA_MODEL", "llama3.1")
    return [
        {
            "id": "ollama_compose",
            "automated": True,
            "command": "docker compose -f deploy/production/agency-llm-compose.yml up -d ollama",
            "description": "Docker 启动 Ollama（推荐生产）",
        },
        {
            "id": "ollama_pull",
            "automated": True,
            "command": f"ollama pull {model}",
            "description": f"拉取默认模型 {model}",
        },
        {
            "id": "ollama_env",
            "automated": True,
            "command": "OLLAMA_BASE_URL=http://127.0.0.1:11434",
            "description": "写入 .env（与 backend 同机）",
        },
    ]


def build_setup_plan(*, target: str = "server") -> dict[str, Any]:
    """
    target: server | dev
    返回可自动化步骤 + 需人工一次性步骤（CLI OAuth）。
    """
    probed = {p["id"]: p for p in list_providers(probe=True)}
    automated: list[dict[str, Any]] = []
    manual: list[dict[str, Any]] = []
    ready: list[str] = []
    for pid, row in probed.items():
        if row.get("available"):
            ready.append(pid)
            continue
        spec = _CLI_INSTALL.get(pid)
        if pid == "ollama":
            automated.extend(_ollama_steps())
            manual.append(
                {
                    "provider": pid,
                    "reason": row.get("reason"),
                    "hint": "若不用 Docker，在服务器安装 Ollama 并 systemctl enable ollama",
                }
            )
            continue
        if pid in ("deepseek", "claude", "openai"):
            manual.append(
                {
                    "provider": pid,
                    "reason": row.get("reason"),
                    "hint": f"在 .env 配置 {row.get('env_key') or 'API Key'} 或 settings AI_*（生产首选）",
                    "automated_env_only": True,
                }
            )
            continue
        if spec:
            manual.append(
                {
                    "provider": pid,
                    "reason": row.get("reason"),
                    "install": spec.get("npm") and f"npm install -g {spec['npm']}" or spec.get("install"),
                    "auth": spec.get("auth"),
                    "server_note": spec.get("server_note"),
                }
            )
            if spec.get("npm"):
                automated.append(
                    {
                        "id": f"npm_{pid}",
                        "automated": True,
                        "command": f"npm install -g {spec['npm']}",
                        "description": f"安装 {pid} CLI（不含 OAuth）",
                    }
                )

    chain = SERVER_DEFAULT_CHAIN if target == "server" else DEV_DEFAULT_CHAIN
    return {
        "target": target,
        "ready_providers": ready,
        "recommended_chain": chain,
        "automated_steps": automated,
        "manual_steps": manual,
        "production_guidance": (
            "云服务器优先 deepseek/ollama/openai API Key，避免依赖 CLI 浏览器登录。"
            "CLI 通道适合本机开发或 SSH 跳板一次性 auth 后拷贝凭据（不推荐生产）。"
        ),
        "probe_summary": {
            "available": len(ready),
            "total": len(probed),
        },
    }


def run_automated_bootstrap(*, pull_ollama_model: bool = True) -> dict[str, Any]:
    """仅执行无 OAuth 步骤：docker ollama、npm 全局安装（若允许）、ollama pull。"""
    import subprocess
    from app.core.config import settings
    results: list[dict[str, Any]] = []
    plan = build_setup_plan(target="server")
    for step in plan.get("automated_steps") or []:
        cmd = step.get("command") or ""
        sid = step.get("id") or ""
        if sid == "ollama_compose":
            auto_docker = (
                os.environ.get("HERMES_AGENCY_AUTO_DOCKER_OLLAMA") == "1"
                or getattr(settings, "HERMES_AGENCY_AUTO_DOCKER_OLLAMA", False)
            )
            if not auto_docker:
                results.append({**step, "skipped": True, "note": "set HERMES_AGENCY_AUTO_DOCKER_OLLAMA=1"})
                continue
            if not shutil.which("docker"):
                results.append({**step, "ok": False, "error": "docker not in PATH"})
                continue
            try:
                root = os.environ.get("PROJECT_ROOT") or os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
                )
                compose = os.path.join(root, "deploy", "production", "agency-llm-compose.yml")
                proc = subprocess.run(
                    ["docker", "compose", "-f", compose, "up", "-d", "ollama"],
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False,
                )
                results.append(
                    {
                        **step,
                        "ok": proc.returncode == 0,
                        "exit_code": proc.returncode,
                        "stderr": (proc.stderr or "")[:500],
                    }
                )
            except Exception as exc:
                results.append({**step, "ok": False, "error": str(exc)[:200]})
            continue
        if sid == "ollama_pull" and pull_ollama_model:
            if not shutil.which("ollama"):
                results.append({**step, "ok": False, "error": "ollama not in PATH"})
                continue
            model = os.environ.get("HERMES_AGENCY_OLLAMA_MODEL", "llama3.1")
            try:
                proc = subprocess.run(
                    ["ollama", "pull", model],
                    capture_output=True,
                    text=True,
                    timeout=600,
                    check=False,
                )
                results.append(
                    {
                        **step,
                        "ok": proc.returncode == 0,
                        "exit_code": proc.returncode,
                        "stderr": (proc.stderr or "")[:500],
                    }
                )
            except Exception as exc:
                results.append({**step, "ok": False, "error": str(exc)[:200]})
            continue
        if sid.startswith("npm_") and (
            os.environ.get("HERMES_AGENCY_AUTO_NPM_INSTALL") == "1"
            or getattr(settings, "HERMES_AGENCY_AUTO_NPM_INSTALL", False)
        ):
            try:
                npm_pkg = step.get("command", "").replace("npm install -g ", "").strip()
                proc = subprocess.run(
                    ["npm", "install", "-g", npm_pkg],
                    shell=False,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False,
                )
                results.append({**step, "ok": proc.returncode == 0, "exit_code": proc.returncode})
            except Exception as exc:
                results.append({**step, "ok": False, "error": str(exc)[:200]})
        else:
            results.append({**step, "skipped": True})

    after = list_providers(probe=True)
    return {
        "bootstrap_results": results,
        "providers_after": after,
        "available_after": sum(1 for p in after if p.get("available")),
    }
