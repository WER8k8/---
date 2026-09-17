# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""国密 SM2/SM3/SM4 工具（敏感字段加密、完整性校验、接口签名）。

依赖 gmssl；未安装时 encrypt/decrypt 会抛出明确错误，应用仍可启动。
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
from typing import Optional, Tuple

_GMSSL_AVAILABLE = False
try:
    from gmssl import sm3 as _sm3_mod
    from gmssl.sm2 import CryptSM2
    from gmssl.sm4 import CryptSM4, SM4_DECRYPT, SM4_ENCRYPT

    _GMSSL_AVAILABLE = True
except ImportError:
    CryptSM2 = None  # type: ignore
    CryptSM4 = None  # type: ignore
    SM4_DECRYPT = SM4_ENCRYPT = None  # type: ignore
    _sm3_mod = None


class GMCryptoError(RuntimeError):
    pass


def gmssl_available() -> bool:
    """gmssl_available。
    :return: 返回处理结果。
    """
    return _GMSSL_AVAILABLE


def sm3_hex(data: bytes | str) -> str:
    """sm3_hex。

    参数说明：
    :param data: 参数 data
    :return: 返回处理结果。
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    if _GMSSL_AVAILABLE and _sm3_mod is not None:
        return _sm3_mod.sm3_hash(list(data))
    # 开发兜底（非国密合规场景）；生产应安装 gmssl
    return hashlib.sha256(data).hexdigest()


def _sm4_key_16(raw: str) -> bytes:
    """规范为 16 字节 SM4 密钥。"""
    if len(raw) >= 32 and all(c in "0123456789abcdefABCDEF" for c in raw[:32]):
        return bytes.fromhex(raw[:32])[:16].ljust(16, b"\0")
    digest = hashlib.sha256(raw.encode("utf-8")).digest()
    return digest[:16]


def sm4_encrypt(plaintext: str, key_material: str) -> str:
    """SM4-ECB + PKCS7，返回 base64。"""
    if not _GMSSL_AVAILABLE:
        raise GMCryptoError("未安装 gmssl，请执行: pip install gmssl")
    raw = plaintext.encode("utf-8")
    pad = 16 - (len(raw) % 16)
    raw += bytes([pad]) * pad
    crypt = CryptSM4()
    crypt.set_key(_sm4_key_16(key_material), SM4_ENCRYPT)
    enc = crypt.crypt_ecb(raw)
    return base64.b64encode(enc).decode("ascii")


def sm4_decrypt(ciphertext_b64: str, key_material: str) -> str:
    """sm4_decrypt。

    参数说明：
    :param ciphertext_b64: 参数 ciphertext_b64
    :param key_material: 参数 key_material
    :return: 返回处理结果。
    """
    if not _GMSSL_AVAILABLE:
        raise GMCryptoError("未安装 gmssl，请执行: pip install gmssl")
    enc = base64.b64decode(ciphertext_b64.encode("ascii"))
    crypt = CryptSM4()
    crypt.set_key(_sm4_key_16(key_material), SM4_DECRYPT)
    raw = crypt.crypt_ecb(enc)
    pad = raw[-1]
    if pad < 1 or pad > 16:
        raise GMCryptoError("SM4 解密失败：填充无效")
    return raw[:-pad].decode("utf-8")


def sm2_sign(message: str, private_key_hex: str, public_key_hex: str) -> str:
    """sm2_sign。

    参数说明：
    :param message: 参数 message
    :param private_key_hex: 参数 private_key_hex
    :param public_key_hex: 参数 public_key_hex
    :return: 返回处理结果。
    """
    if not _GMSSL_AVAILABLE:
        raise GMCryptoError("未安装 gmssl")
    sm2 = CryptSM2(public_key=public_key_hex, private_key=private_key_hex)
    sig = sm2.sign(message.encode("utf-8"), secrets.token_hex(16))
    return base64.b64encode(sig).decode("ascii")


def sm2_verify(message: str, signature_b64: str, public_key_hex: str) -> bool:
    """sm2_verify。

    参数说明：
    :param message: 参数 message
    :param signature_b64: 参数 signature_b64
    :param public_key_hex: 参数 public_key_hex
    :return: 返回处理结果。
    """
    if not _GMSSL_AVAILABLE:
        raise GMCryptoError("未安装 gmssl")
    sm2 = CryptSM2(public_key=public_key_hex, private_key="")
    sig = base64.b64decode(signature_b64.encode("ascii"))
    return bool(sm2.verify(sig, message.encode("utf-8")))


def resolve_sm4_key(explicit: Optional[str] = None, fallback_secret: str = "") -> str:
    """resolve_sm4_key。

    参数说明：
    :param explicit: 参数 explicit
    :param fallback_secret: 参数 fallback_secret
    :return: 返回处理结果。
    """
    key = (explicit or os.getenv("GM_SM4_KEY") or "").strip()
    if key:
        return key
    if fallback_secret:
        return fallback_secret
    raise GMCryptoError("未配置 GM_SM4_KEY 或 SECRET_KEY")


def seal_secret(plaintext: str, key_material: str) -> dict:
    """封装敏感配置：SM3 摘要 + SM4 密文。"""
    body = plaintext.encode("utf-8")
    return {
        "alg": "SM4-ECB+SM3",
        "sm3": sm3_hex(body),
        "ciphertext": sm4_encrypt(plaintext, key_material),
    }


def unseal_secret(payload: dict, key_material: str) -> str:
    """unseal_secret。

    参数说明：
    :param payload: 参数 payload
    :param key_material: 参数 key_material
    :return: 返回处理结果。
    """
    plain = sm4_decrypt(str(payload["ciphertext"]), key_material)
    if sm3_hex(plain) != str(payload.get("sm3", "")):
        raise GMCryptoError("SM3 校验失败，数据可能被篡改")
    return plain


def self_test(key_material: str, sm2_pub: str = "", sm2_priv: str = "") -> dict:
    """创始人调试：国密自检。"""
    sample = "youding-gm-self-test"
    out: dict = {
        "gmssl_installed": _GMSSL_AVAILABLE,
        "sm3_sample": sm3_hex(sample),
    }
    if not _GMSSL_AVAILABLE:
        out["error"] = "pip install gmssl"
        return out
    sealed = seal_secret(sample, key_material)
    out["sm4_roundtrip_ok"] = unseal_secret(sealed, key_material) == sample
    if sm2_pub and sm2_priv:
        try:
            sig = sm2_sign(sample, sm2_priv, sm2_pub)
            out["sm2_verify_ok"] = sm2_verify(sample, sig, sm2_pub)
        except Exception as exc:
            out["sm2_verify_ok"] = False
            out["sm2_error"] = str(exc)[:200]
    return out
