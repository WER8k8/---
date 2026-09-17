# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""微信支付平台证书 — 按 serial 缓存，验签失败时刷新一次。"""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from app.services.wechat_pay_v3 import WeChatPayV3Client, WeChatPayV3Config

logger = logging.getLogger(__name__)

WECHAT_CERTIFICATES_URL = "https://api.mch.weixin.qq.com/v3/certificates"
DEFAULT_CACHE_TTL = 3600


def _cache_ttl_seconds() -> int:
    """_cache_ttl_seconds。
    :return: 返回处理结果。
    """
    raw = (os.getenv("WECHAT_CERT_CACHE_TTL_SECONDS") or "").strip()
    try:
        return max(60, int(raw)) if raw else DEFAULT_CACHE_TTL
    except ValueError:
        return DEFAULT_CACHE_TTL


def _env_platform_pem() -> str:
    """_env_platform_pem。
    :return: 返回处理结果。
    """
    return (os.getenv("WECHAT_PAY_PLATFORM_PUBLIC_KEY") or "").replace("\\n", "\n").strip()


def _env_platform_serial() -> str:
    """_env_platform_serial。
    :return: 返回处理结果。
    """
    return (os.getenv("WECHAT_PAY_PLATFORM_SERIAL") or "").strip()


class WeChatPlatformCertStore:
    """平台公钥缓存；不主动后台轮询，仅在验签解析时按需拉取。"""
    _cache: dict[str, tuple[str, float]] = {}
    def __init__(self, client: WeChatPayV3Client):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param client: 参数 client
        :return: 返回处理结果。
        """
        self.client = client

    def resolve_public_key(
        self,
        serial_no: str,
        *,
        force_refresh: bool = False,
    ) -> Optional[str]:
        """resolve_public_key。

        参数说明：
        :param self: 参数 self
        :param serial_no: 参数 serial_no
        :param force_refresh: 参数 force_refresh
        :return: 返回处理结果。
        """
        serial = (serial_no or "").strip()
        env_pem = _env_platform_pem()
        env_serial = _env_platform_serial()
        if env_pem and (not serial or not env_serial or serial == env_serial):
            return env_pem

        if not force_refresh and serial:
            cached = self._cache.get(serial)
            if cached and cached[1] > time.time():
                return cached[0]

        if not self.client.is_live:
            return env_pem or None

        try:
            mapping = self.fetch_certificates(force=force_refresh)
        except Exception as exc:
            logger.warning("拉取微信平台证书失败: %s", exc)
            if serial and serial in self._cache:
                return self._cache[serial][0]
            return env_pem or None

        if serial and serial in mapping:
            return mapping[serial]
        if mapping:
            return next(iter(mapping.values()))
        return env_pem or None

    def fetch_certificates(self, *, force: bool = False) -> dict[str, str]:
        """fetch_certificates。

        参数说明：
        :param self: 参数 self
        :param force: 参数 force
        :return: 返回处理结果。
        """
        if force:
            self._cache.clear()

        url_path = "/v3/certificates"
        headers = {
            "Authorization": self.client._authorization("GET", url_path, ""),
            "Accept": "application/json",
        }
        with httpx.Client(timeout=20.0) as http:
            resp = http.get(WECHAT_CERTIFICATES_URL, headers=headers)
        if resp.status_code >= 400:
            raise RuntimeError(f"微信平台证书 HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        items = data.get("data") or []
        ttl = _cache_ttl_seconds()
        expire_at = time.time() + ttl
        mapping: dict[str, str] = {}
        for item in items:
            serial = str(item.get("serial_no") or "").strip()
            enc = item.get("encrypt_certificate") or {}
            if not serial or not enc.get("ciphertext"):
                continue
            try:
                decrypted = WeChatPayV3Client.decrypt_resource(
                    self.client.config.api_v3_key,
                    {
                        "ciphertext": enc.get("ciphertext"),
                        "nonce": enc.get("nonce"),
                        "associated_data": enc.get("associated_data") or "certificate",
                    },
                )
            except Exception as exc:
                logger.warning("解密平台证书 serial=%s 失败: %s", serial, exc)
                continue
            if isinstance(decrypted, str):
                pem = decrypted
            else:
                pem = str(decrypted.get("certificate") or "")
            if not pem:
                continue
            mapping[serial] = pem
            self._cache[serial] = (pem, expire_at)

        return mapping

    @classmethod
    def clear_cache(cls) -> None:
        """clear_cache。

        参数说明：
        :param cls: 参数 cls
        :return: 返回处理结果。
        """
        cls._cache.clear()

    @classmethod
    def cache_snapshot(cls) -> list[dict[str, Any]]:
        """返回当前内存缓存条目（运维只读）。"""
        now = time.time()
        out: list[dict[str, Any]] = []
        for serial, (_, expire_at) in cls._cache.items():
            out.append(
                {
                    "serial": serial,
                    "expires_at": datetime.fromtimestamp(expire_at, tz=timezone.utc).isoformat(),
                    "expired": expire_at <= now,
                }
            )
        out.sort(key=lambda x: x["serial"])
        return out


def build_cert_store(config: Optional[WeChatPayV3Config] = None) -> WeChatPlatformCertStore:
    """build_cert_store。

    参数说明：
    :param config: 参数 config
    :return: 返回处理结果。
    """
    if config is None:
        from app.services.wechat_pay_v3 import load_wechat_pay_v3_config
        config = load_wechat_pay_v3_config()
    return WeChatPlatformCertStore(WeChatPayV3Client(config))
