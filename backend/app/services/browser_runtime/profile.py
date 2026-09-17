# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""租户 Profile 隔离（总纲 §4.7：每租户独立 Profile 防跨租户泄漏）。

红线 1：Profile 路径不可越界（任何 resolve 调用必须落在 config 根目录之下）；
红线 2：白名单之外的租户禁止创建 Profile（仅允许解析根目录元数据）。

本轮 25-B 仅落地理路径计算与白名单校验，不实际写盘（写盘待 25-C 真实执行时
按需惰性创建）。
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Iterable, Optional

from app.services.browser_runtime.exceptions import (
    BrowserRuntimeDisabled,
    ProfileIsolationError,
)

logger = logging.getLogger("uj-admin.browser_runtime.profile")

# Profile id 字符集（仅 [a-zA-Z0-9_-]）—— 防路径注入/越界
_PROFILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")

# 默认根目录（开发兜底用临时目录；生产应在 config.BROWSER_RUNTIME_PROFILE_ROOT 设置）
DEFAULT_PROFILE_ROOT = "/tmp/uj_browser_profiles"


@dataclass
class ProfilePath:
    """租户 Profile 物理路径。"""

    tenant_id: str
    root: str
    path: str

    def __str__(self) -> str:  # noqa: Dunder
        return self.path


def _settings():
    try:
        from app.core.config import settings  # noqa: PLC0415

        return settings
    except Exception:  # noqa: BLE001
        return None


def _resolve_root() -> str:
    s = _settings()
    root = getattr(s, "BROWSER_RUNTIME_PROFILE_ROOT", None) if s else None
    return root or DEFAULT_PROFILE_ROOT


def _parse_allowed_tenants(raw: str) -> set[str]:
    if not raw:
        return set()
    return {t.strip() for t in raw.split(",") if t.strip()}


def is_runtime_enabled() -> bool:
    """全局开关（默认关）。"""
    s = _settings()
    return bool(getattr(s, "BROWSER_RUNTIME_ENABLED", False)) if s else False


def is_tenant_allowed(tenant_id: str) -> bool:
    """租户白名单（开启时按白名单粒度鉴权，未开启视为不允许）。"""
    if not is_runtime_enabled():
        return False
    s = _settings()
    raw = getattr(s, "BROWSER_RUNTIME_ALLOWED_TENANTS", "") if s else ""
    allowed = _parse_allowed_tenants(raw)
    return tenant_id in allowed


def ensure_tenant_allowed(tenant_id: str) -> None:
    """开关+白名单闸门：未启用或租户不在白名单抛 BrowserRuntimeDisabled。"""
    if not is_runtime_enabled():
        raise BrowserRuntimeDisabled("BROWSER_RUNTIME_ENABLED is False")
    if not is_tenant_allowed(tenant_id):
        raise BrowserRuntimeDisabled(
            f"tenant {tenant_id} not in BROWSER_RUNTIME_ALLOWED_TENANTS"
        )


def resolve_profile_path(tenant_id: str) -> ProfilePath:
    """计算租户 Profile 物理路径。**不触磁盘**——纯路径解析。

    路径格式：{root}/{tenant_id}/profile-{short_hash}
    - 短 hash 来自 tenant_id 前 8 位（仅用于路径防冲突，**不构成安全边界**）
    - 越界检查：解析后路径必须在 root 之下，否则抛 ProfileIsolationError
    """
    if not _PROFILE_ID_RE.match(tenant_id):
        raise ProfileIsolationError(f"invalid_tenant_id: {tenant_id}")
    root = os.path.realpath(_resolve_root())
    short = tenant_id[:8] if len(tenant_id) >= 8 else tenant_id
    target = os.path.realpath(os.path.join(root, tenant_id, f"profile-{short}"))
    # 越界检查：必须以 root 开头
    if not (target == root or target.startswith(root + os.sep)):
        raise ProfileIsolationError(
            f"profile path escapes root: {tenant_id} -> {target}"
        )
    return ProfilePath(tenant_id=tenant_id, root=root, path=target)


def mask_tenant_id(tenant_id: str) -> str:
    """证据 / 日志输出时掩码租户 ID（前 4 + 末 4，中间 ****）—— 防泄漏。"""
    if not tenant_id or len(tenant_id) < 12:
        return tenant_id[:2] + "****" if tenant_id else ""
    return f"{tenant_id[:4]}****{tenant_id[-4:]}"


def ensure_profile_dir(profile_path: ProfilePath) -> ProfilePath:
    """惰性创建租户 Profile 物理目录（轮25-C 真实执行时用）。

    防御：
    - 二次校验路径在 root 之下（即使 resolve_profile_path 已校验，防御 race）；
    - 显式 mode 0o700（仅 owner 可读写，Linux/Mac 强隔离；Windows 忽略 mode
      但 NTFS ACL 仍生效）；
    - 创建失败抛 BrowserRuntimeUnavailable（让 runtime.execute 走降级）。
    """
    from app.services.browser_runtime.exceptions import BrowserRuntimeUnavailable

    real_root = os.path.realpath(profile_path.root)
    real_target = os.path.realpath(profile_path.path)
    if not (real_target == real_root or real_target.startswith(real_root + os.sep)):
        raise ProfileIsolationError(
            f"profile path escapes root (race): {profile_path.tenant_id} -> {real_target}"
        )
    try:
        os.makedirs(real_target, mode=0o700, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        raise BrowserRuntimeUnavailable(
            f"profile_dir_create_failed: {profile_path.tenant_id} -> {exc}"
        )
    # 跨平台权限收紧：Windows 下尽量用 icacls 收紧（best-effort，失败不阻断）
    if os.name == "nt":
        try:
            import subprocess  # noqa: PLC0415
            subprocess.run(
                ["icacls", real_target, "/inheritance:r",
                 "/grant:r", f"{os.environ.get('USERNAME', '')}:(OI)(CI)F"],
                check=False, capture_output=True, timeout=5,
            )
        except Exception:  # noqa: BLE001
            pass
    return ProfilePath(
        tenant_id=profile_path.tenant_id, root=real_root, path=real_target
    )
