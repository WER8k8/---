# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Security package: ClawPatrol + JWT/auth (re-export from app.core.security.py)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from app.core.security.claw_patrol import (
    ClawPatrolFirewall,
    ThreatLevel,
    scan_ai_generated_code,
)

_IMPL_NAME = "app.core._jwt_security_impl"
_legacy_path = Path(__file__).resolve().parent.parent / "security.py"

if _IMPL_NAME not in sys.modules:
    _spec = importlib.util.spec_from_file_location(_IMPL_NAME, _legacy_path)
    if _spec is None or _spec.loader is None:
        raise ImportError(f"Cannot load JWT security module at {_legacy_path}")
    _impl = importlib.util.module_from_spec(_spec)
    sys.modules[_IMPL_NAME] = _impl
    _spec.loader.exec_module(_impl)
else:
    _impl = sys.modules[_IMPL_NAME]

get_current_user = _impl.get_current_user
resolve_user_from_bearer_token = _impl.resolve_user_from_bearer_token
resolve_user_from_request = _impl.resolve_user_from_request
get_current_user_optional = _impl.get_current_user_optional
optional_auth = _impl.optional_auth
require_admin = _impl.require_admin
require_role = _impl.require_role
require_permission = _impl.require_permission
require_any_role = _impl.require_any_role
create_access_token = _impl.create_access_token
decode_refresh_payload = _impl.decode_refresh_payload
decode_refresh_token = _impl.decode_refresh_token
get_password_hash = _impl.get_password_hash
verify_password = _impl.verify_password
security_scheme = _impl.security_scheme
pwd_context = _impl.pwd_context

__all__ = [
    "ClawPatrolFirewall",
    "ThreatLevel",
    "scan_ai_generated_code",
    "get_current_user",
    "resolve_user_from_bearer_token",
    "resolve_user_from_request",
    "get_current_user_optional",
    "optional_auth",
    "require_admin",
    "require_role",
    "require_permission",
    "require_any_role",
    "create_access_token",
    "decode_refresh_payload",
    "decode_refresh_token",
    "get_password_hash",
    "verify_password",
    "security_scheme",
    "pwd_context",
]
