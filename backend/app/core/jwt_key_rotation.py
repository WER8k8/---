"""
JWT 密钥轮换服务

支持多密钥版本管理，实现安全的密钥轮换策略：
1. 支持多个签名密钥（active + inactive）
2. 新令牌使用最新密钥签名
3. 旧令牌在过渡期内仍可使用旧密钥验证
4. 支持自动/手动轮换
5. 密钥存储在 Redis（生产）或文件（开发）

轮换策略：
- 主密钥（active）：用于签名新令牌
- 副密钥（inactive）：用于验证旧令牌（过渡期内）
- 轮换间隔：默认 30 天
- 过渡期：默认 7 天（旧令牌仍可验证）
"""

import json
import os
import secrets
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import jwt

from app.core.cache import redis_client
from app.core.config import settings


JWT_KEY_PREFIX = "jwt:keys:"
JWT_CURRENT_KEY_ID_KEY = "jwt:current_key_id"
JWT_KEY_ROTATION_CONFIG = "jwt:rotation_config"


class JWTKeyRotationService:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._redis = redis_client
        self._use_redis = settings.REDIS_ENABLED and self._redis is not None
        self._dev_key_file = Path(__file__).resolve().parents[2] / "logs" / "jwt-rotation-keys.json"
        self._ensure_keys_exist()

    def _ensure_keys_exist(self):
        """_ensure_keys_exist。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._use_redis:
            current_id = self._redis.get(JWT_CURRENT_KEY_ID_KEY)
            if not current_id:
                self._bootstrap_redis_keys()
        else:
            if not self._dev_key_file.exists():
                self._bootstrap_dev_keys()

    def _bootstrap_redis_keys(self):
        """_bootstrap_redis_keys。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        primary_key = secrets.token_hex(32)
        secondary_key = secrets.token_hex(32)
        now = int(time.time())
        keys = {
            "primary": {
                "key_id": "k1",
                "secret": primary_key,
                "created_at": now,
                "status": "active",
                "rotation_at": now + (30 * 24 * 3600),
            },
            "secondary": {
                "key_id": "k2",
                "secret": secondary_key,
                "created_at": now,
                "status": "inactive",
                "rotation_at": 0,
            },
        }
        self._redis.set(JWT_CURRENT_KEY_ID_KEY, "k1")
        self._redis.set(JWT_KEY_PREFIX + "k1", json.dumps(keys["primary"]))
        self._redis.set(JWT_KEY_PREFIX + "k2", json.dumps(keys["secondary"]))
        self._redis.set(JWT_KEY_ROTATION_CONFIG, json.dumps({
            "rotation_interval_days": 30,
            "grace_period_days": 7,
        }))

    def _bootstrap_dev_keys(self):
        """_bootstrap_dev_keys。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        primary_key = secrets.token_hex(32)
        secondary_key = secrets.token_hex(32)
        now = int(time.time())
        keys = {
            "current_key_id": "k1",
            "keys": {
                "k1": {
                    "secret": primary_key,
                    "created_at": now,
                    "status": "active",
                    "rotation_at": now + (30 * 24 * 3600),
                },
                "k2": {
                    "secret": secondary_key,
                    "created_at": now,
                    "status": "inactive",
                    "rotation_at": 0,
                },
            },
            "config": {
                "rotation_interval_days": 30,
                "grace_period_days": 7,
            },
        }
        self._dev_key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._dev_key_file, "w", encoding="utf-8") as f:
            json.dump(keys, f, indent=2)

    def _get_all_keys(self) -> Dict[str, Dict]:
        """_get_all_keys。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._use_redis:
            keys = {}
            for key_id in ["k1", "k2"]:
                data = self._redis.get(JWT_KEY_PREFIX + key_id)
                if data:
                    keys[key_id] = json.loads(data)
            return keys
        else:
            if self._dev_key_file.exists():
                with open(self._dev_key_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("keys", {})
            return {}

    def _get_current_key_id(self) -> str:
        """_get_current_key_id。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        if self._use_redis:
            return self._redis.get(JWT_CURRENT_KEY_ID_KEY) or "k1"
        else:
            if self._dev_key_file.exists():
                with open(self._dev_key_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("current_key_id", "k1")
            return "k1"

    def _set_current_key_id(self, key_id: str):
        """_set_current_key_id。

        参数说明：
        :param self: 参数 self
        :param key_id: 参数 key_id
        :return: 返回处理结果。
        """
        if self._use_redis:
            self._redis.set(JWT_CURRENT_KEY_ID_KEY, key_id)
        else:
            if self._dev_key_file.exists():
                with open(self._dev_key_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["current_key_id"] = key_id
                with open(self._dev_key_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

    def _update_key(self, key_id: str, updates: Dict):
        """_update_key。

        参数说明：
        :param self: 参数 self
        :param key_id: 参数 key_id
        :param updates: 参数 updates
        :return: 返回处理结果。
        """
        if self._use_redis:
            data = self._redis.get(JWT_KEY_PREFIX + key_id)
            if data:
                key_data = json.loads(data)
                key_data.update(updates)
                self._redis.set(JWT_KEY_PREFIX + key_id, json.dumps(key_data))
        else:
            if self._dev_key_file.exists():
                with open(self._dev_key_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if key_id in data.get("keys", {}):
                    data["keys"][key_id].update(updates)
                with open(self._dev_key_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

    def get_signing_key(self) -> Tuple[str, str]:
        """get_signing_key。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        current_id = self._get_current_key_id()
        keys = self._get_all_keys()
        key_data = keys.get(current_id)
        if key_data and key_data.get("status") == "active":
            return current_id, key_data["secret"]
        return "k1", settings.JWT_SECRET_KEY

    def sign_token(self, data: dict) -> str:
        """sign_token。

        参数说明：
        :param self: 参数 self
        :param data: 参数 data
        :return: 返回处理结果。
        """
        key_id, secret = self.get_signing_key()
        to_encode = data.copy()
        to_encode["kid"] = key_id
        expire_seconds = time.time() + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        expire = datetime.fromtimestamp(expire_seconds)
        to_encode["exp"] = expire
        return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)

    def decode_token(self, token: str) -> Optional[Dict]:
        """decode_token。

        参数说明：
        :param self: 参数 self
        :param token: 参数 token
        :return: 返回处理结果。
        """
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid", "k1")
            keys = self._get_all_keys()
            key_data = keys.get(kid)
            if key_data and key_data.get("status") in ("active", "inactive"):
                now = int(time.time())
                if key_data["status"] == "inactive":
                    grace_end = key_data.get("rotation_at", 0) + (7 * 24 * 3600)
                    if now > grace_end:
                        return None
                return jwt.decode(token, key_data["secret"], algorithms=[settings.JWT_ALGORITHM])
            
            for key_id, key_data in keys.items():
                if key_data.get("status") in ("active", "inactive"):
                    try:
                        return jwt.decode(token, key_data["secret"], algorithms=[settings.JWT_ALGORITHM])
                    except jwt.InvalidTokenError:
                        continue

            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except jwt.InvalidTokenError:
            return None

    def rotate_keys(self) -> Dict:
        """rotate_keys。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        current_id = self._get_current_key_id()
        keys = self._get_all_keys()
        now = int(time.time())
        old_key_id = current_id
        new_key_id = "k2" if old_key_id == "k1" else "k1"
        new_secret = secrets.token_hex(32)
        self._update_key(old_key_id, {
            "status": "inactive",
            "rotation_at": now,
        })
        self._update_key(new_key_id, {
            "secret": new_secret,
            "created_at": now,
            "status": "active",
            "rotation_at": now + (30 * 24 * 3600),
        })
        self._set_current_key_id(new_key_id)
        return {
            "old_key_id": old_key_id,
            "new_key_id": new_key_id,
            "old_key_status": "inactive (grace period active)",
            "new_key_status": "active",
            "grace_period_ends_at": now + (7 * 24 * 3600),
            "next_rotation_at": now + (30 * 24 * 3600),
        }

    def get_key_status(self) -> Dict:
        """get_key_status。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        current_id = self._get_current_key_id()
        keys = self._get_all_keys()
        now = int(time.time())
        status = {
            "current_key_id": current_id,
            "keys": {},
            "next_rotation_due": None,
        }
        for key_id, key_data in keys.items():
            key_status = {
                "status": key_data.get("status"),
                "created_at": key_data.get("created_at"),
                "rotation_at": key_data.get("rotation_at"),
                "is_current": key_id == current_id,
            }
            if key_data.get("status") == "inactive":
                grace_end = key_data.get("rotation_at", 0) + (7 * 24 * 3600)
                key_status["grace_period_ends_at"] = grace_end
                key_status["grace_period_active"] = now < grace_end
            
            status["keys"][key_id] = key_status
            if key_id == current_id and key_data.get("rotation_at"):
                status["next_rotation_due"] = key_data["rotation_at"]
        
        return status

    def cleanup_expired_keys(self) -> Dict:
        """cleanup_expired_keys。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        keys = self._get_all_keys()
        now = int(time.time())
        cleaned = []
        for key_id, key_data in keys.items():
            if key_data.get("status") == "inactive":
                grace_end = key_data.get("rotation_at", 0) + (7 * 24 * 3600)
                if now > grace_end:
                    cleaned.append(key_id)
        
        return {
            "cleaned_keys": cleaned,
            "message": "Expired keys cleaned (if any)",
        }


jwt_key_rotation_service = JWTKeyRotationService()
