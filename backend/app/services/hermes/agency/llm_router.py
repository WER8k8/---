# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""agency-orchestrator 10 provider / 7 免 Key — Hermes LLM 路由（对齐 ao factory）。"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_CATALOG_PATH = Path(__file__).resolve().parents[3] / "data" / "agency_provider_catalog.json"
_ARG_SAFE_LIMIT = 4 * 1024
_CLI_PROVIDERS = frozenset(
    {
        "claude-code",
        "gemini-cli",
        "copilot-cli",
        "codex-cli",
        "openclaw-cli",
        "hermes-cli",
    }
)


@dataclass
class AgencyLlmConfig:
    provider: str = "deepseek"
    model: str | None = None
    max_tokens: int = 4096
    base_url: str | None = None
    api_key: str | None = None
    timeout_sec: int = 600
    agent: str | None = None


def _load_catalog() -> dict[str, Any]:
    """_load_catalog。
    :return: 返回处理结果。
    """
    if not _CATALOG_PATH.is_file():
        return {"providers": [], "default_chain": []}
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8-sig"))


def _provider_spec(provider_id: str) -> dict[str, Any] | None:
    """_provider_spec。

    参数说明：
    :param provider_id: 参数 provider_id
    :return: 返回处理结果。
    """
    pid = (provider_id or "").strip().lower()
    for row in _load_catalog().get("providers") or []:
        if row.get("id") == pid:
            return row
    return None


def _settings():
    """_settings。
    :return: 返回处理结果。
    """
    from app.core.config import settings
    return settings


def _resolve_api_key(provider_id: str, spec: dict[str, Any] | None) -> str | None:
    """_resolve_api_key。

    参数说明：
    :param provider_id: 参数 provider_id
    :param spec: 参数 spec
    :return: 返回处理结果。
    """
    env_name = (spec or {}).get("env_key")
    if env_name:
        val = os.environ.get(env_name, "").strip()
        if val:
            return val
    settings_key = (spec or {}).get("settings_key")
    if settings_key:
        val = getattr(_settings(), settings_key, None)
        if val:
            return str(val).strip()
    return None


def _resolve_base_url(provider_id: str, spec: dict[str, Any] | None, override: str | None) -> str:
    """_resolve_base_url。

    参数说明：
    :param provider_id: 参数 provider_id
    :param spec: 参数 spec
    :param override: 参数 override
    :return: 返回处理结果。
    """
    if override:
        return override.rstrip("/")
    pid = provider_id.lower()
    if pid == "deepseek":
        base = getattr(_settings(), "AI_DEEPSEEK_BASE_URL", "") or "https://api.deepseek.com"
        if not base.endswith("/v1"):
            base = base.rstrip("/") + "/v1"
        return base.rstrip("/")
    if pid == "openai":
        return (os.environ.get("OPENAI_BASE_URL") or spec.get("default_base_url") or "https://api.openai.com/v1").rstrip("/")
    if pid == "ollama":
        return (os.environ.get("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").rstrip("/")
    return (spec or {}).get("default_base_url") or ""


def probe_provider(provider_id: str) -> dict[str, Any]:
    """探测单个 provider 是否可用（CLI 在 PATH / API Key / Ollama 连通）。"""
    pid = (provider_id or "").strip().lower()
    spec = _provider_spec(pid) or {"id": pid, "kind": "api", "label": pid}
    row: dict[str, Any] = {
        "provider": pid,
        "label": spec.get("label") or pid,
        "kind": spec.get("kind") or ("cli" if pid in _CLI_PROVIDERS else "api"),
        "available": False,
        "reason": "unknown",
    }
    if pid in _CLI_PROVIDERS or spec.get("kind") == "cli":
        cmd = spec.get("command") or pid.replace("-cli", "")
        if pid == "claude-code":
            cmd = "claude"
        found = shutil.which(str(cmd))
        row["command"] = cmd
        if found:
            row["available"] = True
            row["reason"] = "cli_found"
        else:
            row["reason"] = "cli_not_installed"
        return row

    if pid == "ollama":
        base = _resolve_base_url(pid, spec, None)
        row["base_url"] = base
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(f"{base}/api/tags")
                if r.status_code == 200:
                    row["available"] = True
                    row["reason"] = "ollama_reachable"
                else:
                    row["reason"] = f"ollama_http_{r.status_code}"
        except Exception as exc:
            row["reason"] = f"ollama_unreachable:{exc.__class__.__name__}"
        return row

    key = _resolve_api_key(pid, spec)
    if key:
        row["available"] = True
        row["reason"] = "api_key_configured"
    else:
        row["reason"] = "missing_api_key"
    return row


def list_providers(*, probe: bool = True) -> list[dict[str, Any]]:
    """list_providers。

    参数说明：
    :param probe: 参数 probe
    :return: 返回处理结果。
    """
    catalog = _load_catalog()
    rows: list[dict[str, Any]] = []
    for spec in catalog.get("providers") or []:
        pid = str(spec.get("id") or "")
        if probe:
            rows.append({**spec, **probe_provider(pid)})
        else:
            rows.append(dict(spec))
    return rows


def provider_catalog_meta() -> dict[str, Any]:
    """provider_catalog_meta。
    :return: 返回处理结果。
    """
    cat = _load_catalog()
    probed = list_providers(probe=True)
    free = [p for p in probed if not p.get("requires_api_key")]
    avail = [p for p in probed if p.get("available")]
    return {
        "catalog_version": cat.get("catalog_version"),
        "provider_count": len(probed),
        "free_no_api_key_count": len(free),
        "available_count": len(avail),
        "default_chain": _default_chain(),
        "settings": {
            "hermes_agency_llm_enabled": getattr(_settings(), "HERMES_AGENCY_LLM_ENABLED", True),
            "default_provider": getattr(_settings(), "HERMES_AGENCY_DEFAULT_PROVIDER", None),
        },
    }


def _default_chain() -> list[str]:
    """_default_chain。
    :return: 返回处理结果。
    """
    custom = getattr(_settings(), "HERMES_AGENCY_PROVIDER_CHAIN", None)
    if custom:
        return [p.strip() for p in str(custom).split(",") if p.strip()]
    cat = _load_catalog()
    chain = cat.get("default_chain") or []
    default_p = getattr(_settings(), "HERMES_AGENCY_DEFAULT_PROVIDER", None)
    if default_p:
        dp = str(default_p).strip()
        if dp and dp not in chain:
            return [dp, *[c for c in chain if c != dp]]
    return list(chain)


def resolve_provider_chain(llm: dict[str, Any] | AgencyLlmConfig | None) -> list[AgencyLlmConfig]:
    """YAML llm 块优先，再按 default_chain 追加 fallback。"""
    primary: AgencyLlmConfig | None = None
    if isinstance(llm, AgencyLlmConfig):
        primary = llm
    elif isinstance(llm, dict) and llm.get("provider"):
        primary = AgencyLlmConfig(
            provider=str(llm.get("provider")),
            model=llm.get("model"),
            max_tokens=int(llm.get("max_tokens") or 4096),
            base_url=llm.get("base_url"),
            api_key=llm.get("api_key"),
            timeout_sec=int(llm.get("timeout") or getattr(_settings(), "HERMES_AGENCY_CLI_TIMEOUT_SEC", 600)),
            agent=llm.get("agent"),
        )

    configs: list[AgencyLlmConfig] = []
    seen: set[str] = set()
    def add(cfg: AgencyLlmConfig) -> None:
        """add。

        参数说明：
        :param cfg: 参数 cfg
        :return: 返回处理结果。
        """
        pid = cfg.provider.lower()
        if pid in seen:
            return
        seen.add(pid)
        configs.append(cfg)

    if primary:
        add(primary)
    for pid in _default_chain():
        add(AgencyLlmConfig(provider=pid, max_tokens=primary.max_tokens if primary else 4096))
    return configs


async def _run_subprocess(
    command: str,
    args: list[str],
    *,
    stdin_text: str | None = None,
    timeout_sec: int = 600,
) -> tuple[str, str, int]:
    """_run_subprocess。

    参数说明：
    :param command: 参数 command
    :param args: 参数 args
    :param stdin_text: 参数 stdin_text
    :param timeout_sec: 参数 timeout_sec
    :return: 返回处理结果。
    """
    if os.name == "nt":
        # Windows: npm global CLIs 常为 .cmd
        proc = await asyncio.create_subprocess_shell(
            " ".join([command, *[f'"{a}"' if " " in a else a for a in args]]),
            stdin=asyncio.subprocess.PIPE if stdin_text is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    else:
        exe = shutil.which(command) or command
        proc = await asyncio.create_subprocess_exec(
            exe,
            *args,
            stdin=asyncio.subprocess.PIPE if stdin_text is not None else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(stdin_text.encode("utf-8") if stdin_text is not None else None),
            timeout=timeout_sec,
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise TimeoutError(f"{command} 超时 ({timeout_sec}s)")
    return (
        (stdout_b or b"").decode("utf-8", errors="replace"),
        (stderr_b or b"").decode("utf-8", errors="replace"),
        proc.returncode or 0,
    )


def _merge_prompt(system_prompt: str, user_message: str) -> str:
    """_merge_prompt。

    参数说明：
    :param system_prompt: 参数 system_prompt
    :param user_message: 参数 user_message
    :return: 返回处理结果。
    """
    if system_prompt:
        return f"<system>\n{system_prompt}\n</system>\n\n{user_message}"
    return user_message


async def _invoke_cli(cfg: AgencyLlmConfig, system_prompt: str, user_message: str) -> dict[str, Any]:
    """_invoke_cli。

    参数说明：
    :param cfg: 参数 cfg
    :param system_prompt: 参数 system_prompt
    :param user_message: 参数 user_message
    :return: 返回处理结果。
    """
    pid = cfg.provider.lower()
    full = _merge_prompt(system_prompt, user_message)
    use_stdin = len(full.encode("utf-8")) > _ARG_SAFE_LIMIT
    timeout = cfg.timeout_sec
    if pid == "claude-code":
        sysp_file = None
        args = ["-p", "-", "--output-format", "json", "--tools", "", "--effort", "low", "--no-session-persistence"]
        try:
            if system_prompt:
                fd, sysp_file = tempfile.mkstemp(suffix=".txt", prefix="ao-sysprompt-")
                os.close(fd)
                Path(sysp_file).write_text(system_prompt, encoding="utf-8")
                args.extend(["--system-prompt-file", sysp_file])
            if cfg.model and cfg.model != "claude-code":
                args.extend(["--model", cfg.model])
            stdout, stderr, code = await _run_subprocess("claude", args, stdin_text=user_message, timeout_sec=timeout)
            if code != 0 and not stdout.strip():
                raise RuntimeError(f"claude-code failed: {stderr[:300]}")
            try:
                data = json.loads(stdout)
                content = str(data.get("result") or "").strip()
            except json.JSONDecodeError:
                content = stdout.strip()
            if not content:
                raise RuntimeError("claude-code empty output")
            return {"content": content, "provider": pid, "model": cfg.model}
        finally:
            if sysp_file:
                try:
                    os.unlink(sysp_file)
                except OSError:
                    pass

    if pid == "gemini-cli":
        args = (["-m", cfg.model] if cfg.model else []) + (["-p", full] if not use_stdin else ["-p", "-"])
        stdout, stderr, code = await _run_subprocess(
            "gemini", args, stdin_text=full if use_stdin else None, timeout_sec=timeout
        )
    elif pid == "copilot-cli":
        args = (["--model", cfg.model] if cfg.model else []) + (["-p", full] if not use_stdin else ["-p", "-"])
        stdout, stderr, code = await _run_subprocess(
            "copilot", args, stdin_text=full if use_stdin else None, timeout_sec=timeout
        )
    elif pid == "codex-cli":
        args = ["exec", "--skip-git-repo-check", "--sandbox", "read-only"]
        if cfg.model:
            args.extend(["--model", cfg.model])
        args.append("-" if use_stdin else full)
        stdout, stderr, code = await _run_subprocess(
            "codex", args, stdin_text=full if use_stdin else None, timeout_sec=timeout
        )
    elif pid == "openclaw-cli":
        agent = cfg.agent or cfg.model or os.environ.get("OPENCLAW_AGENT") or "main"
        args = ["agent", "--agent", agent, "--message", full if not use_stdin else "-"]
        stdout, stderr, code = await _run_subprocess(
            "openclaw", args, stdin_text=full if use_stdin else None, timeout_sec=timeout
        )
        stdout = "\n".join(
            ln
            for ln in stdout.splitlines()
            if ln.strip() and not ln.replace("\x1b", "").strip().startswith("[plugins]")
        )
    elif pid == "hermes-cli":
        args = ["-z", full if not use_stdin else "-"]
        if cfg.model:
            args.extend(["--model", cfg.model])
        stdout, stderr, code = await _run_subprocess(
            "hermes", args, stdin_text=full if use_stdin else None, timeout_sec=timeout
        )
    else:
        raise ValueError(f"unsupported_cli:{pid}")

    content = stdout.strip()
    if code != 0 and not content:
        raise RuntimeError(f"{pid} exit {code}: {stderr[:400]}")
    if not content:
        raise RuntimeError(f"{pid} empty output")
    return {"content": content, "provider": pid, "model": cfg.model}


async def _invoke_openai_compatible(
    cfg: AgencyLlmConfig,
    system_prompt: str,
    user_message: str,
) -> dict[str, Any]:
    """_invoke_openai_compatible。

    参数说明：
    :param cfg: 参数 cfg
    :param system_prompt: 参数 system_prompt
    :param user_message: 参数 user_message
    :return: 返回处理结果。
    """
    spec = _provider_spec(cfg.provider) or {}
    api_key = cfg.api_key or _resolve_api_key(cfg.provider, spec)
    if not api_key:
        raise RuntimeError(f"{cfg.provider}_missing_api_key")
    base = _resolve_base_url(cfg.provider, spec, cfg.base_url)
    model = cfg.model or spec.get("default_model") or "gpt-4o-mini"
    url = f"{base}/chat/completions"
    payload = {
        "model": model,
        "max_tokens": cfg.max_tokens,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt or "You are a helpful assistant."},
            {"role": "user", "content": user_message},
        ],
    }
    async with httpx.AsyncClient(timeout=cfg.timeout_sec) as client:
        r = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
        )
    if r.status_code >= 400:
        raise RuntimeError(f"{cfg.provider} http {r.status_code}: {r.text[:300]}")
    data = r.json()
    content = str(data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
    if not content:
        raise RuntimeError(f"{cfg.provider} empty completion")
    return {"content": content, "provider": cfg.provider, "model": model}


async def _invoke_anthropic(cfg: AgencyLlmConfig, system_prompt: str, user_message: str) -> dict[str, Any]:
    """_invoke_anthropic。

    参数说明：
    :param cfg: 参数 cfg
    :param system_prompt: 参数 system_prompt
    :param user_message: 参数 user_message
    :return: 返回处理结果。
    """
    spec = _provider_spec("claude") or {}
    api_key = cfg.api_key or _resolve_api_key("claude", spec)
    if not api_key:
        raise RuntimeError("claude_missing_api_key")
    model = cfg.model or spec.get("default_model") or "claude-sonnet-4-20250514"
    base = getattr(_settings(), "AI_ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    payload = {
        "model": model,
        "max_tokens": cfg.max_tokens,
        "system": system_prompt or "",
        "messages": [{"role": "user", "content": user_message}],
    }
    async with httpx.AsyncClient(timeout=cfg.timeout_sec) as client:
        r = await client.post(
            f"{base}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )
    if r.status_code >= 400:
        raise RuntimeError(f"claude http {r.status_code}: {r.text[:300]}")
    data = r.json()
    parts = data.get("content") or []
    content = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict)).strip()
    if not content:
        raise RuntimeError("claude empty completion")
    return {"content": content, "provider": "claude", "model": model}


async def _invoke_ollama(cfg: AgencyLlmConfig, system_prompt: str, user_message: str) -> dict[str, Any]:
    """_invoke_ollama。

    参数说明：
    :param cfg: 参数 cfg
    :param system_prompt: 参数 system_prompt
    :param user_message: 参数 user_message
    :return: 返回处理结果。
    """
    spec = _provider_spec("ollama") or {}
    base = _resolve_base_url("ollama", spec, cfg.base_url)
    model = cfg.model or spec.get("default_model") or "llama3.1"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt or ""},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
        "options": {"num_predict": cfg.max_tokens},
    }
    async with httpx.AsyncClient(timeout=cfg.timeout_sec) as client:
        r = await client.post(f"{base}/api/chat", json=payload)
    if r.status_code >= 400:
        raise RuntimeError(f"ollama http {r.status_code}: {r.text[:300]}")
    data = r.json()
    content = str((data.get("message") or {}).get("content") or "").strip()
    if not content:
        raise RuntimeError("ollama empty completion")
    return {"content": content, "provider": "ollama", "model": model}


async def invoke_provider(
    cfg: AgencyLlmConfig,
    *,
    system_prompt: str,
    user_message: str,
) -> dict[str, Any]:
    """invoke_provider。

    参数说明：
    :param cfg: 参数 cfg
    :param system_prompt: 参数 system_prompt
    :param user_message: 参数 user_message
    :return: 返回处理结果。
    """
    pid = cfg.provider.lower()
    if pid in _CLI_PROVIDERS or pid == "claude-code":
        return await _invoke_cli(cfg, system_prompt, user_message)
    if pid == "ollama":
        return await _invoke_ollama(cfg, system_prompt, user_message)
    if pid == "claude":
        return await _invoke_anthropic(cfg, system_prompt, user_message)
    if pid in ("deepseek", "openai") or cfg.base_url:
        return await _invoke_openai_compatible(cfg, system_prompt, user_message)
    if cfg.base_url:
        return await _invoke_openai_compatible(cfg, system_prompt, user_message)
    raise ValueError(f"unsupported_provider:{pid}")


async def invoke_agency_llm(
    db: Any,
    *,
    system_prompt: str,
    user_message: str,
    llm: dict[str, Any] | AgencyLlmConfig | None = None,
    tenant_id: str | None = None,
    task_type: str = "agency_workflow",
    lane: str = "customer",
) -> dict[str, Any]:
    """
    按 ao provider 链调用；全部失败则 fallback 网站 invoke_llm（NVIDIA/租户通道）。
    """
    if not getattr(_settings(), "HERMES_AGENCY_LLM_ENABLED", True):
        return await _fallback_site_llm(
            db,
            prompt=f"{system_prompt}\n\n---\n\n{user_message}",
            tenant_id=tenant_id,
            task_type=task_type,
            lane=lane,
        )

    errors: list[str] = []
    for cfg in resolve_provider_chain(llm):
        probe = probe_provider(cfg.provider)
        if not probe.get("available"):
            errors.append(f"{cfg.provider}:{probe.get('reason')}")
            continue
        try:
            out = await invoke_provider(cfg, system_prompt=system_prompt, user_message=user_message)
            out["routing"] = "agency_provider"
            out["provider_used"] = cfg.provider
            return out
        except Exception as exc:
            logger.info("agency provider %s failed: %s", cfg.provider, exc)
            errors.append(f"{cfg.provider}:{exc.__class__.__name__}")

    logger.warning("agency LLM chain exhausted, fallback site invoke_llm: %s", errors[:5])
    out = await _fallback_site_llm(
        db,
        prompt=f"{system_prompt}\n\n---\n\n{user_message}",
        tenant_id=tenant_id,
        task_type=task_type,
        lane=lane,
    )
    out["routing"] = "site_invoke_llm"
    out["agency_errors"] = errors[:8]
    return out


async def _fallback_site_llm(
    db: Any,
    *,
    prompt: str,
    tenant_id: str | None,
    task_type: str,
    lane: str,
) -> dict[str, Any]:
    """_fallback_site_llm。

    参数说明：
    :param db: 参数 db
    :param prompt: 参数 prompt
    :param tenant_id: 参数 tenant_id
    :param task_type: 参数 task_type
    :param lane: 参数 lane
    :return: 返回处理结果。
    """
    from app.services.ai_invocation_service import invoke_llm
    result = await invoke_llm(
        db,
        prompt=prompt,
        scenario="article",
        max_tokens=4096,
        task_type=task_type,
        tenant_id=tenant_id,
        lane=lane,
    )
    return {
        "content": str(result.get("content") or "").strip(),
        "provider_used": "site_invoke_llm",
        "model_name": result.get("model_name"),
    }
