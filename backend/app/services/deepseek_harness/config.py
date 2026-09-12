"""DeepSeek Harness 接入配置（纯标准库，无重依赖，保证本包可随时安全导入）。

所有配置均可通过环境变量覆盖；未设置时使用与项目布局匹配的默认值。
关键路径：
- repo_dir    : 开源仓库克隆位置（workspace 根下的 deepseek-harness/）
- dsh_home    : dsh 运行时家目录（显式，绝不读 ~/.dsh）
- workspace   : agent 工作区（dsh 的 cwd）
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _find_workspace_root() -> Path:
    """从本文件向上寻找包含 deepseek-harness/ 的工作区根。"""
    cur = Path(__file__).resolve()
    for _ in range(12):
        if (cur / "deepseek-harness").is_dir():
            return cur
        if str(cur) == str(cur.parent):
            break
        cur = cur.parent
    # 兜底：固定层级（.../上线网站开发完成）
    return Path(__file__).resolve().parents[6]


WORKSPACE_ROOT = _find_workspace_root()
REPO_DIR = WORKSPACE_ROOT / "deepseek-harness"


def _env_path(name: str, default: Path) -> Path:
    v = os.environ.get(name)
    if v:
        return Path(v).expanduser()
    return default


def _env_str(name: str, default: str) -> str:
    return os.environ.get(name) or default


def _env_opt(name: str) -> Optional[str]:
    v = os.environ.get(name)
    return v if v else None


def _env_int_opt(name: str) -> Optional[int]:
    v = os.environ.get(name)
    if not v:
        return None
    try:
        return int(v)
    except ValueError:
        return None


@dataclass
class DeepSeekHarnessSettings:
    enabled: bool = True
    repo_dir: Path = REPO_DIR
    dsh_home: Path = field(
        default_factory=lambda: _env_path("DSH_HOME", WORKSPACE_ROOT / ".dsh-home")
    )
    workspace: Path = field(
        default_factory=lambda: _env_path(
            "DEEPSEEK_HARNESS_WORKSPACE", WORKSPACE_ROOT / "deepseek-harness-workspace"
        )
    )
    profile: str = field(
        default_factory=lambda: _env_str("DEEPSEEK_HARNESS_PROFILE", "sdk-minimal")
    )
    provider: str = field(
        default_factory=lambda: _env_str("DEEPSEEK_HARNESS_PROVIDER", "deepseek-official")
    )
    model: str = field(
        default_factory=lambda: _env_str("DEEPSEEK_HARNESS_MODEL", "deepseek-v4-flash")
    )
    reasoning_effort: Optional[str] = field(
        default_factory=lambda: _env_opt("DEEPSEEK_HARNESS_REASONING_EFFORT")
    )
    max_tokens: Optional[int] = field(
        default_factory=lambda: _env_int_opt("DEEPSEEK_HARNESS_MAX_TOKENS")
    )
    # 复用项目既有 DeepSeek 凭据（app.core.config 中的 AI_DEEPSEEK_*）
    api_key: Optional[str] = field(
        default_factory=lambda: _env_opt("DEEPSEEK_API_KEY")
        or _env_opt("AI_DEEPSEEK_API_KEY")
    )
    base_url: Optional[str] = field(
        default_factory=lambda: _env_opt("DEEPSEEK_BASE_URL")
        or _env_opt("AI_DEEPSEEK_BASE_URL")
    )
    initialize_timeout_seconds: float = 30.0
    request_timeout_seconds: Optional[float] = None

    def ensure_dirs(self) -> None:
        self.dsh_home.mkdir(parents=True, exist_ok=True)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def as_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "repo_dir": str(self.repo_dir),
            "repo_present": self.repo_dir.is_dir(),
            "dsh_home": str(self.dsh_home),
            "workspace": str(self.workspace),
            "profile": self.profile,
            "provider": self.provider,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "max_tokens": self.max_tokens,
            "has_api_key": bool(self.api_key),
            "base_url": self.base_url,
        }


_settings: Optional[DeepSeekHarnessSettings] = None


def get_settings() -> DeepSeekHarnessSettings:
    global _settings
    if _settings is None:
        _settings = DeepSeekHarnessSettings()
    return _settings
