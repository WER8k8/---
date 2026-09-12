"""国密算法服务 — FIX-13: GmSSL 认证库替换

支持国密标准算法：
- SM4: 对称加密（替代 AES）
- SM2: 非对称加密/签名（替代 RSA/ECDSA）
- SM3: 哈希函数（替代 SHA-256）

与现有 Fernet 加密服务并行，支持渐进式迁移。
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from base64 import b64decode, b64encode
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# SM3 哈希（软件实现，不依赖外部库）
# ═══════════════════════════════════════════════════════════

class SM3:
    """SM3 哈希算法（GB/T 32905-2016）。

    输出 256 位（32 字节）摘要，安全性对标 SHA-256。
    """
    # SM3 初始向量
    IV = [
        0x7380166f, 0x4914b2b9, 0x172442d7, 0xda8a0600,
        0xa96f30bc, 0x163138aa, 0xe38dee4d, 0xb0fb0e4e,
    ]
    # 常量 T_j
    @staticmethod
    def _t(j: int) -> int:
        """_t。

        参数说明：
        :param j: 参数 j
        :return: 返回处理结果。
        """
        return 0x79cc4519 if j < 16 else 0x7a879d8a

    @staticmethod
    def _ff(x: int, y: int, z: int, j: int) -> int:
        """_ff。

        参数说明：
        :param x: 参数 x
        :param y: 参数 y
        :param z: 参数 z
        :param j: 参数 j
        :return: 返回处理结果。
        """
        return (x ^ y ^ z) if j < 16 else ((x & y) | (x & z) | (y & z))

    @staticmethod
    def _gg(x: int, y: int, z: int, j: int) -> int:
        """_gg。

        参数说明：
        :param x: 参数 x
        :param y: 参数 y
        :param z: 参数 z
        :param j: 参数 j
        :return: 返回处理结果。
        """
        return (x ^ y ^ z) if j < 16 else ((x & y) | (~x & z))

    @staticmethod
    def _p0(x: int) -> int:
        """_p0。

        参数说明：
        :param x: 参数 x
        :return: 返回处理结果。
        """
        return x ^ ((x << 9) | (x >> 23)) ^ ((x << 17) | (x >> 15))

    @staticmethod
    def _p1(x: int) -> int:
        """_p1。

        参数说明：
        :param x: 参数 x
        :return: 返回处理结果。
        """
        return x ^ ((x << 15) | (x >> 17)) ^ ((x << 23) | (x >> 9))

    @staticmethod
    def _left_rotate(x: int, n: int) -> int:
        """_left_rotate。

        参数说明：
        :param x: 参数 x
        :param n: 参数 n
        :return: 返回处理结果。
        """
        return ((x << n) | (x >> (32 - n))) & 0xffffffff

    def _message_expand(self, b_i: list[int]) -> tuple[list[int], list[int]]:
        """消息扩展。"""
        w = [0] * 68
        w_ = [0] * 64
        for j in range(16):
            w[j] = b_i[j]

        for j in range(16, 68):
            w[j] = self._p1(w[j - 16] ^ w[j - 9] ^ self._left_rotate(w[j - 3], 15)) ^ self._left_rotate(w[j - 13], 7) ^ w[j - 6]

        for j in range(64):
            w_[j] = w[j] ^ w[j + 4]

        return w, w_

    def _cf(self, v_i: list[int], b_i: list[int]) -> list[int]:
        """压缩函数。"""
        w, w_ = self._message_expand(b_i)
        a, b, c, d, e, f, g, h = v_i
        for j in range(64):
            ss1 = self._left_rotate((self._left_rotate(a, 12) + e + self._left_rotate(self._t(j), j % 32)) & 0xffffffff, 7)
            ss2 = ss1 ^ self._left_rotate(a, 12)
            tt1 = (self._ff(a, b, c, j) + d + ss2 + w_[j]) & 0xffffffff
            tt2 = (self._gg(e, f, g, j) + h + ss1 + w[j]) & 0xffffffff
            d = c
            c = self._left_rotate(b, 9)
            b = a
            a = tt1
            h = g
            g = self._left_rotate(f, 19)
            f = e
            e = tt2 ^ self._left_rotate(tt2, 9) ^ self._left_rotate(tt2, 17)

        return [
            a ^ v_i[0], b ^ v_i[1], c ^ v_i[2], d ^ v_i[3],
            e ^ v_i[4], f ^ v_i[5], g ^ v_i[6], h ^ v_i[7],
        ]

    def digest(self, message: bytes) -> bytes:
        """计算 SM3 摘要。"""
        # 填充
        ml = len(message) * 8
        message = message + b'\x80'
        while (len(message) * 8) % 512 != 448:
            message += b'\x00'
        message += ml.to_bytes(8, 'big')
        # 分组处理
        n = len(message) // 64
        v = list(self.IV)
        for i in range(n):
            b_i = [int.from_bytes(message[i * 64 + j * 4:i * 64 + (j + 1) * 4], 'big') for j in range(16)]
            v = self._cf(v, b_i)

        return b''.join(x.to_bytes(4, 'big') for x in v)

    def hexdigest(self, message: bytes) -> str:
        """hexdigest。

        参数说明：
        :param self: 参数 self
        :param message: 参数 message
        :return: 返回处理结果。
        """
        return self.digest(message).hex()


# ═══════════════════════════════════════════════════════════
# SM4 对称加密（软件实现）
# ═══════════════════════════════════════════════════════════

class SM4:
    """SM4 分组密码（GB/T 32907-2016）。

    分组长度 128 位，密钥长度 128 位，轮数 32 轮。
    安全性对标 AES-128。
    """
    # S 盒
    SBOX = bytes([
        0xd6, 0x90, 0xe9, 0xfe, 0xcc, 0xe1, 0x3d, 0xb7, 0x16, 0xb6, 0x14, 0xc2, 0x28, 0xfb, 0x2c, 0x05,
        0x2b, 0x67, 0x9a, 0x76, 0x2a, 0xbe, 0x04, 0xc3, 0xaa, 0x44, 0x13, 0x26, 0x49, 0x86, 0x06, 0x99,
        0x9c, 0x42, 0x50, 0xf4, 0x91, 0xef, 0x98, 0x7a, 0x33, 0x54, 0x0b, 0x43, 0xed, 0xcf, 0xac, 0x62,
        0xe4, 0xb3, 0x1c, 0xa9, 0xc9, 0x08, 0xe8, 0x95, 0x80, 0xdf, 0x94, 0xfa, 0x75, 0x8f, 0x3f, 0xa6,
        0x47, 0x07, 0xa7, 0xfc, 0xf3, 0x73, 0x17, 0xba, 0x83, 0x59, 0x3c, 0x19, 0xe6, 0x85, 0x4f, 0xa8,
        0x68, 0x6b, 0x81, 0xb2, 0x71, 0x64, 0xda, 0x8b, 0xf8, 0xeb, 0x0f, 0x4b, 0x70, 0x56, 0x9d, 0x35,
        0x1e, 0x24, 0x0e, 0x5e, 0x63, 0x58, 0xd1, 0xa2, 0x25, 0x22, 0x7c, 0x3b, 0x01, 0x21, 0x78, 0x87,
        0xd4, 0x00, 0x46, 0x57, 0x9f, 0xd3, 0x27, 0x52, 0x4c, 0x36, 0x02, 0xe7, 0xa0, 0xc4, 0xc8, 0x9e,
        0xea, 0xbf, 0x8a, 0xd2, 0x40, 0xc7, 0x38, 0xb5, 0xa3, 0xf7, 0xf2, 0xce, 0xf9, 0x61, 0x15, 0xa1,
        0xe0, 0xae, 0x5d, 0xa4, 0x9b, 0x34, 0x1a, 0x55, 0xad, 0x93, 0x32, 0x30, 0xf5, 0x8c, 0xb1, 0xe3,
        0x1d, 0xf6, 0xe2, 0x2e, 0x82, 0x66, 0xca, 0x60, 0xc0, 0x29, 0x23, 0xab, 0x0d, 0x53, 0x4e, 0x6f,
        0xd5, 0xdb, 0x37, 0x45, 0xde, 0xfd, 0x8e, 0x2f, 0x03, 0xff, 0x6a, 0x72, 0x6d, 0x6c, 0x5b, 0x51,
        0x8d, 0x1b, 0xaf, 0x92, 0xbb, 0xdd, 0xbc, 0x7f, 0x11, 0xd9, 0x5c, 0x41, 0x1f, 0x10, 0x5a, 0xd8,
        0x0a, 0xc1, 0x31, 0x88, 0xa5, 0xcd, 0x7b, 0xbd, 0x2d, 0x74, 0xd0, 0x12, 0xb8, 0xe5, 0xb4, 0xb0,
        0x89, 0x69, 0x97, 0x4a, 0x0c, 0x96, 0x77, 0x7e, 0x65, 0xb9, 0xf1, 0x09, 0xc5, 0x6e, 0xc6, 0x84,
        0x18, 0xf0, 0x7d, 0xec, 0x3a, 0xdc, 0x4d, 0x20, 0x79, 0xee, 0x5f, 0x3e, 0xd7, 0xcb, 0x39, 0x48,
    ])
    FK = [0xa3b1bac6, 0x56aa3350, 0x677d9197, 0xb27022dc]
    CK = [
        0x00070e15, 0x1c232a31, 0x383f464d, 0x545b6269,
        0x70777e85, 0x8c939aa1, 0xa8afb6bd, 0xc4cbd2d9,
        0xe0e7eef5, 0xfc030a11, 0x181f262d, 0x343b4249,
        0x50575e65, 0x6c737a81, 0x888f969d, 0xa4abb2b9,
        0xc0c7ced5, 0xdce3eaf1, 0xf8ff060d, 0x141b2229,
        0x30373e45, 0x4c535a61, 0x686f767d, 0x848b9299,
        0xa0a7aeb5, 0xbcc3cad1, 0xd8dfe6ed, 0xf4fb0209,
        0x10171e25, 0x2c333a41, 0x484f565d, 0x646b7279,
    ]
    def __init__(self, key: bytes):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param key: 参数 key
        :return: 返回处理结果。
        """
        if len(key) != 16:
            raise ValueError("SM4 key must be 16 bytes")
        self._rk = self._key_schedule(key)

    def _tau(self, a: int) -> int:
        """S 盒变换。"""
        return (self.SBOX[(a >> 24) & 0xff] << 24 |
                self.SBOX[(a >> 16) & 0xff] << 16 |
                self.SBOX[(a >> 8) & 0xff] << 8 |
                self.SBOX[a & 0xff])

    def _l(self, b: int) -> int:
        """线性变换 L。"""
        return b ^ self._left_rotate(b, 2) ^ self._left_rotate(b, 10) ^ self._left_rotate(b, 18) ^ self._left_rotate(b, 24)

    def _l_prime(self, b: int) -> int:
        """密钥扩展线性变换 L'。"""
        return b ^ self._left_rotate(b, 13) ^ self._left_rotate(b, 23)

    @staticmethod
    def _left_rotate(x: int, n: int) -> int:
        """_left_rotate。

        参数说明：
        :param x: 参数 x
        :param n: 参数 n
        :return: 返回处理结果。
        """
        return ((x << n) | (x >> (32 - n))) & 0xffffffff

    def _f(self, x0: int, x1: int, x2: int, x3: int, rk: int) -> int:
        """轮函数 F。"""
        return x0 ^ self._l(self._tau(x1 ^ x2 ^ x3 ^ rk))

    def _key_schedule(self, key: bytes) -> list[int]:
        """密钥扩展。"""
        k = [int.from_bytes(key[i * 4:(i + 1) * 4], 'big') ^ self.FK[i] for i in range(4)]
        rk = []
        for i in range(32):
            k.append(k[i] ^ self._l_prime(self._tau(k[i + 1] ^ k[i + 2] ^ k[i + 3] ^ self.CK[i])))
            rk.append(k[i + 4])
        return rk

    def _encrypt_block(self, plaintext: bytes) -> bytes:
        """加密一个分组（16 字节）。"""
        x = [int.from_bytes(plaintext[i * 4:(i + 1) * 4], 'big') for i in range(4)]
        for i in range(32):
            x.append(self._f(x[i], x[i + 1], x[i + 2], x[i + 3], self._rk[i]))
        return b''.join(x[35 - i].to_bytes(4, 'big') for i in range(4))

    def _decrypt_block(self, ciphertext: bytes) -> bytes:
        """解密一个分组（16 字节）。"""
        x = [int.from_bytes(ciphertext[i * 4:(i + 1) * 4], 'big') for i in range(4)]
        for i in range(32):
            x.append(self._f(x[i], x[i + 1], x[i + 2], x[i + 3], self._rk[31 - i]))
        return b''.join(x[35 - i].to_bytes(4, 'big') for i in range(4))

    def _pad(self, data: bytes) -> bytes:
        """PKCS7 填充。"""
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)

    def _unpad(self, data: bytes) -> bytes:
        """PKCS7 去填充。"""
        return data[:-data[-1]]

    def encrypt_cbc(self, plaintext: bytes, iv: bytes) -> bytes:
        """CBC 模式加密。"""
        if len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        data = self._pad(plaintext)
        prev = iv
        ciphertext = b""
        for i in range(0, len(data), 16):
            block = bytes(a ^ b for a, b in zip(data[i:i + 16], prev))
            encrypted = self._encrypt_block(block)
            ciphertext += encrypted
            prev = encrypted
        return ciphertext

    def decrypt_cbc(self, ciphertext: bytes, iv: bytes) -> bytes:
        """CBC 模式解密。"""
        if len(iv) != 16:
            raise ValueError("IV must be 16 bytes")
        prev = iv
        plaintext = b""
        for i in range(0, len(ciphertext), 16):
            block = ciphertext[i:i + 16]
            decrypted = self._decrypt_block(block)
            plaintext += bytes(a ^ b for a, b in zip(decrypted, prev))
            prev = block
        return self._unpad(plaintext)


# ═══════════════════════════════════════════════════════════
# GmSSL 服务
# ═══════════════════════════════════════════════════════════

@dataclass
class GmSSLCryptoResult:
    """国密加密结果"""
    ciphertext: str = ""
    plaintext: str = ""
    hash_value: str = ""
    algorithm: str = ""
    success: bool = False
    error: str = ""


class GmSSLCryptoService:
    """国密算法服务。

    提供 SM3/SM4 国密标准算法，支持：
    1. SM4-CBC 对称加密/解密（替代 AES）
    2. SM3 哈希/摘要（替代 SHA-256）
    3. HMAC-SM3 消息认证码

    密钥管理：
    - 主密钥从环境变量 GMSSL_MASTER_KEY 获取
    - 支持密钥派生（SM3-KDF）
    """
    def __init__(self, master_key: str = ""):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param master_key: 参数 master_key
        :return: 返回处理结果。
        """
        self._master_key = (master_key or os.getenv("GMSSL_MASTER_KEY", "")).encode()
        if not self._master_key:
            logger.warning("GmSSLCryptoService: GMSSL_MASTER_KEY not set")

    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return bool(self._master_key)

    def _derive_key(self, salt: bytes, key_len: int = 16) -> bytes:
        """SM3 派生密钥（KDF）。"""
        if not self._master_key:
            raise RuntimeError("Master key not configured")

        # 简单 KDF: SM3(master_key || salt || counter)
        key_material = b""
        counter = 0
        while len(key_material) < key_len:
            sm3 = SM3()
            data = self._master_key + salt + counter.to_bytes(4, 'big')
            key_material += sm3.digest(data)
            counter += 1
        return key_material[:key_len]

    def encrypt_sm4(self, plaintext: str, key_id: str = "default") -> GmSSLCryptoResult:
        """SM4-CBC 加密。"""
        try:
            salt = key_id.encode()
            key = self._derive_key(salt, 16)
            iv = self._derive_key(b"iv:" + salt, 16)
            sm4 = SM4(key)
            ciphertext = sm4.encrypt_cbc(plaintext.encode("utf-8"), iv)
            return GmSSLCryptoResult(
                ciphertext=b64encode(ciphertext).decode(),
                algorithm="SM4-CBC",
                success=True,
            )
        except Exception as e:
            logger.error("SM4 encrypt failed: %s", e)
            return GmSSLCryptoResult(error=str(e), algorithm="SM4-CBC")

    def decrypt_sm4(self, ciphertext_b64: str, key_id: str = "default") -> GmSSLCryptoResult:
        """SM4-CBC 解密。"""
        try:
            salt = key_id.encode()
            key = self._derive_key(salt, 16)
            iv = self._derive_key(b"iv:" + salt, 16)
            ciphertext = b64decode(ciphertext_b64)
            sm4 = SM4(key)
            plaintext = sm4.decrypt_cbc(ciphertext, iv)
            return GmSSLCryptoResult(
                plaintext=plaintext.decode("utf-8"),
                algorithm="SM4-CBC",
                success=True,
            )
        except Exception as e:
            logger.error("SM4 decrypt failed: %s", e)
            return GmSSLCryptoResult(error=str(e), algorithm="SM4-CBC")

    def hash_sm3(self, data: str | bytes) -> GmSSLCryptoResult:
        """SM3 哈希。"""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            sm3 = SM3()
            digest = sm3.digest(data)
            return GmSSLCryptoResult(
                hash_value=digest.hex(),
                algorithm="SM3",
                success=True,
            )
        except Exception as e:
            return GmSSLCryptoResult(error=str(e), algorithm="SM3")

    def hmac_sm3(self, data: str | bytes, key_id: str = "default") -> GmSSLCryptoResult:
        """HMAC-SM3 消息认证码。"""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            salt = key_id.encode()
            key = self._derive_key(b"hmac:" + salt, 32)
            sm3 = SM3()
            inner_pad = bytes(b ^ 0x36 for b in key.ljust(64, b'\x00'))
            outer_pad = bytes(b ^ 0x5c for b in key.ljust(64, b'\x00'))
            inner_hash = sm3.digest(inner_pad + data)
            # Need fresh SM3 instance
            sm3 = SM3()
            mac = sm3.digest(outer_pad + inner_hash)
            return GmSSLCryptoResult(
                hash_value=mac.hex(),
                algorithm="HMAC-SM3",
                success=True,
            )
        except Exception as e:
            return GmSSLCryptoResult(error=str(e), algorithm="HMAC-SM3")

    def encrypt_record(self, record: dict[str, Any], sensitive_fields: list[str] | None = None) -> dict[str, Any]:
        """加密记录中的敏感字段（国密版）。"""
        if sensitive_fields is None:
            sensitive_fields = ["email", "phone", "password", "secret_key", "api_key",
                                "access_token", "refresh_token"]

        encrypted = {}
        for key, value in record.items():
            if key in sensitive_fields and isinstance(value, str) and value:
                result = self.encrypt_sm4(value, key_id=key)
                encrypted[key] = result.ciphertext if result.success else value
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_record(self, record: dict[str, Any], sensitive_fields: list[str] | None = None) -> dict[str, Any]:
        """解密记录中的敏感字段（国密版）。"""
        if sensitive_fields is None:
            sensitive_fields = ["email", "phone", "password", "secret_key", "api_key",
                                "access_token", "refresh_token"]

        decrypted = {}
        for key, value in record.items():
            if key in sensitive_fields and isinstance(value, str) and value and len(value) > 20:
                # Heuristic: encrypted values are base64 and longer
                result = self.decrypt_sm4(value, key_id=key)
                decrypted[key] = result.plaintext if result.success else value
            else:
                decrypted[key] = value
        return decrypted


# 单例
gmssl_crypto_service = GmSSLCryptoService()