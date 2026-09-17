# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""字段级加密：AES-256-GCM，用于敏感 PII 字段（email/phone）。

密钥来源：通过 HKDF-SHA256 从 SECRET_KEY 派生 32 字节加密密钥。
警告：更换 SECRET_KEY 会导致已有加密数据无法解密。

用法（在 Repository/Service 层调用）：
    from app.core.field_crypto import encrypt_field, decrypt_field
    encrypted = encrypt_field("user@example.com")
    plaintext = decrypt_field(encrypted)
"""

import os
import base64
import hashlib

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from app.core.config import settings

# 固定上下文信息，防止同一 SECRET_KEY 被其他用途复用
_FIELD_CRYPTO_CONTEXT = b"uj-saas-field-crypto-v1"


def _get_key() -> bytes:
    """通过 HKDF-SHA256 从 SECRET_KEY 派生 32 字节加密密钥。"""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=_FIELD_CRYPTO_CONTEXT,
    )
    return hkdf.derive(settings.SECRET_KEY.encode())


def encrypt_field(plaintext: str) -> str:
    """AES-256-GCM 加密，返回 base64(nonce + ciphertext)"""
    if not plaintext:
        return ""
    aesgcm = AESGCM(_get_key())
    nonce = os.urandom(12)
    # AAD 绑定算法版本，防止密钥混淆攻击
    aad = b"aes256gcm-v1"
    ct = aesgcm.encrypt(nonce, plaintext.encode(), aad)
    return base64.b64encode(nonce + ct).decode()


def decrypt_field(ciphertext: str) -> str:
    """解密 base64(nonce + ciphertext) → 明文"""
    if not ciphertext:
        return ""
    aesgcm = AESGCM(_get_key())
    raw = base64.b64decode(ciphertext)
    nonce, ct = raw[:12], raw[12:]
    aad = b"aes256gcm-v1"
    return aesgcm.decrypt(nonce, ct, aad).decode()
