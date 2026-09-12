"""邮件发送队列 + 数据飞轮 + 安全加密 + AI 安全 — FIX-62 ~ FIX-65

FIX-62: 邮件发送队列（高吞吐 + 高送达率）
FIX-63: 数据飞轮（越用越聪明的获客系统）
FIX-64: 敏感字段加密审计
FIX-65: AI 安全（LLM 输入/输出安全）
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
from base64 import b64decode, b64encode
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.cache import redis_client

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# FIX-62: 邮件发送队列
# ═══════════════════════════════════════════════════════════

class EmailQueueStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    DEFERRED = "deferred"
    RATE_LIMITED = "rate_limited"


@dataclass
class EmailQueueItem:
    """邮件队列项"""
    item_id: str
    to_email: str
    to_name: str = ""
    subject: str = ""
    body: str = ""
    priority: int = 0        # 0-10, 越高越优先
    domain: str = ""
    campaign_id: str = ""
    status: EmailQueueStatus = EmailQueueStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    last_error: str = ""
    scheduled_at: str = ""
    created_at: str = ""
    gate_verdict: str = ""   # 邮件链路关卡裁决（总纲 §6.4）：空=未经关卡
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        d = {
            "item_id": self.item_id,
            "to_email": self.to_email,
            "to_name": self.to_name,
            "subject": self.subject[:50],
            "priority": self.priority,
            "status": self.status.value,
            "attempts": self.attempts,
            "scheduled_at": self.scheduled_at,
        }
        if self.gate_verdict:
            d["gate_verdict"] = self.gate_verdict
        return d


class EmailSendQueue:
    """邮件发送队列管理器。

    特性：
    1. 优先级队列（高优先级先发）
    2. 域名速率限制（每域名每小时上限）
    3. 批量发送 + 并发控制
    4. 自动重试（指数退避）
    5. 退信/投诉自动处理
    """
    def __init__(self, queue_id: str = "default"):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param queue_id: 参数 queue_id
        :return: 返回处理结果。
        """
        self._queue_id = queue_id
        self._queue: list[EmailQueueItem] = []
        self._domain_rates: dict[str, dict] = defaultdict(lambda: {
            "sent": 0, "hour_start": datetime.now(timezone.utc),
        })
        self._domain_limits: dict[str, int] = {}
        self._lock = asyncio.Lock()
        self._load_from_redis()

    def _save_to_redis(self) -> None:
        """将队列数据持久化到 Redis，故障时降级到内存。"""
        if not redis_client:
            return
        try:
            queue_data = [item.to_dict() for item in self._queue]
            redis_client.set(
                f"email:queue:{self._queue_id}",
                json.dumps(queue_data),
                ex=86400,
            )
        except Exception as e:
            logger.warning("Failed to save email queue to Redis: %s", e)

    def _load_from_redis(self) -> None:
        """从 Redis 加载队列数据，故障时保持内存模式。"""
        if not redis_client:
            return
        try:
            saved = redis_client.get(f"email:queue:{self._queue_id}")
            if saved:
                self._queue = [EmailQueueItem(**item) for item in json.loads(saved)]
                logger.info("Loaded %d items from Redis for queue '%s'", len(self._queue), self._queue_id)
        except Exception as e:
            logger.warning("Failed to load email queue from Redis: %s", e)

    # 域名速率限制配置
    DEFAULT_DOMAIN_LIMITS = {
        "gmail.com": 500,
        "yahoo.com": 300,
        "outlook.com": 300,
        "hotmail.com": 300,
        "aol.com": 200,
        "icloud.com": 200,
        "protonmail.com": 100,
        "default": 1000,
    }
    def set_domain_limits(self, limits: dict[str, int]) -> None:
        """set_domain_limits。

        参数说明：
        :param self: 参数 self
        :param limits: 参数 limits
        :return: 返回处理结果。
        """
        self._domain_limits = limits

    def _get_domain_limit(self, email: str) -> int:
        """获取域名速率限制。"""
        domain = email.split("@")[-1].lower() if "@" in email else "default"
        return self._domain_limits.get(domain,
               self.DEFAULT_DOMAIN_LIMITS.get(domain,
               self.DEFAULT_DOMAIN_LIMITS["default"]))

    async def enqueue(
        self,
        to_email: str,
        subject: str,
        body: str,
        to_name: str = "",
        priority: int = 0,
        campaign_id: str = "",
        scheduled_at: str = "",
        tenant_id: str = "",
    ) -> EmailQueueItem:
        """入队邮件。

        Args:
            to_email: 收件人邮箱
            subject: 主题
            body: 正文
            to_name: 收件人姓名
            priority: 优先级
            campaign_id: 营销活动 ID
            scheduled_at: 计划发送时间
            tenant_id: 可选；提供时经邮件链路双关卡（总纲 §6.4，特性开关默认关）：
                清洗关硬拦截 → 状态 DEFERRED + last_error=gate_blocked（不入发送流）；
                复核关为标记语义（裁决记录于 gate_verdict）。

        Returns:
            队列项
        """
        now = datetime.now(timezone.utc).isoformat()
        # ---- 邮件链路双关卡（总纲 §6.4；开关默认关/异常→off，零回归）----
        gate_verdict = ""
        blocked = False
        if tenant_id:
            try:
                from app.services.pipeline.chains import gate_content  # noqa: PLC0415
                report = gate_content(
                    None,
                    tenant_id=tenant_id,
                    title=subject,
                    content=body,
                    chain="email",
                )
                gate_verdict = report.verdict
                blocked = report.blocked
            except Exception:  # noqa: BLE001 — 关卡故障不得阻断邮件流（零回归）
                logger.warning("email chain gate 异常，视为 off（不改变原流程）")
                gate_verdict = "off"

        item = EmailQueueItem(
            item_id=f"eq_{hashlib.md5(f'{to_email}{subject}{now}'.encode()).hexdigest()[:12]}",
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body=body,
            priority=priority,
            domain=to_email.split("@")[-1] if "@" in to_email else "",
            campaign_id=campaign_id,
            scheduled_at=scheduled_at or now,
            created_at=now,
            gate_verdict=gate_verdict,
        )
        if blocked:
            item.status = EmailQueueStatus.DEFERRED
            item.last_error = "gate_blocked"

        async with self._lock:
            self._queue.append(item)
            # 按优先级和时间排序
            self._queue.sort(key=lambda x: (-x.priority, x.scheduled_at))
            self._save_to_redis()

        return item

    async def enqueue_batch(
        self,
        recipients: list[dict],
        subject_template: str,
        body_template: str,
        campaign_id: str = "",
        priority: int = 0,
    ) -> list[EmailQueueItem]:
        """批量入队。

        Args:
            recipients: [{email, name, ...}]
            subject_template: 主题模板
            body_template: 正文模板
            campaign_id: 营销活动 ID
            priority: 优先级

        Returns:
            队列项列表
        """
        items = []
        for r in recipients:
            email = r.get("email", "")
            if not email:
                continue

            # 替换模板变量
            subject = subject_template
            body = body_template
            for key, value in r.items():
                placeholder = "{" + key + "}"
                subject = subject.replace(placeholder, str(value))
                body = body.replace(placeholder, str(value))

            item = await self.enqueue(
                to_email=email,
                subject=subject,
                body=body,
                to_name=r.get("name", ""),
                priority=priority,
                campaign_id=campaign_id,
            )
            items.append(item)

        return items

    async def dequeue_batch(
        self,
        batch_size: int = 50,
        send_func=None,
    ) -> list[dict]:
        """出队并发送一批邮件。

        Args:
            batch_size: 批量大小
            send_func: 发送函数 async (item) -> (success, error)

        Returns:
            发送结果列表
        """
        now = datetime.now(timezone.utc)
        results = []
        async with self._lock:
            # 筛选可发送的
            sendable = []
            remaining = []
            for item in self._queue:
                if item.status != EmailQueueStatus.PENDING:
                    remaining.append(item)
                    continue

                scheduled = datetime.fromisoformat(item.scheduled_at)
                if scheduled > now:
                    remaining.append(item)
                    continue

                # 域名速率限制
                domain = item.domain or "default"
                limit = self._get_domain_limit(item.to_email)
                reset_hour = self._domain_rates[domain]["hour_start"].replace(tzinfo=timezone.utc)
                if now - reset_hour > timedelta(hours=1):
                    self._domain_rates[domain] = {"sent": 0, "hour_start": now}

                if self._domain_rates[domain]["sent"] >= limit:
                    remaining.append(item)
                    continue

                if len(sendable) < batch_size:
                    sendable.append(item)
                    self._domain_rates[domain]["sent"] += 1
                else:
                    remaining.append(item)

            self._queue = remaining
            self._save_to_redis()

        # 发送
        if send_func:
            for item in sendable:
                item.status = EmailQueueStatus.PROCESSING
                item.attempts += 1
                try:
                    success, error = await send_func(item)
                    if success:
                        item.status = EmailQueueStatus.SENT
                        results.append({"item_id": item.item_id, "status": "sent", "email": item.to_email})
                    else:
                        if item.attempts >= item.max_attempts:
                            item.status = EmailQueueStatus.FAILED
                        else:
                            item.status = EmailQueueStatus.DEFERRED
                            item.last_error = error or "unknown"
                            # 重新入队（延迟）
                            async with self._lock:
                                self._queue.append(item)
                                self._save_to_redis()
                        results.append({"item_id": item.item_id, "status": "failed", "error": error})
                except Exception as e:
                    item.status = EmailQueueStatus.FAILED
                    item.last_error = str(e)
                    results.append({"item_id": item.item_id, "status": "failed", "error": str(e)})

        return results

    async def get_stats(self) -> dict[str, Any]:
        """获取队列统计。"""
        async with self._lock:
            status_counts = defaultdict(int)
            domain_counts = defaultdict(int)
            for item in self._queue:
                status_counts[item.status.value] += 1
                domain_counts[item.domain] += 1

            return {
                "total": len(self._queue),
                "by_status": dict(status_counts),
                "by_domain": dict(domain_counts),
                "domain_rates": {
                    d: {"sent": r["sent"], "limit": self._get_domain_limit(f"@{d}")}
                    for d, r in self._domain_rates.items()
                },
            }

    async def clear_completed(self) -> int:
        """清理已完成的队列项。"""
        async with self._lock:
            before = len(self._queue)
            self._queue = [
                item for item in self._queue
                if item.status not in (EmailQueueStatus.SENT, EmailQueueStatus.FAILED)
            ]
            self._save_to_redis()
            return before - len(self._queue)


# ═══════════════════════════════════════════════════════════
# FIX-63: 数据飞轮
# ═══════════════════════════════════════════════════════════

class DataFlywheelStage(str, Enum):
    COLLECT = "collect"          # 收集数据
    ANALYZE = "analyze"          # 分析模式
    OPTIMIZE = "optimize"        # 优化策略
    AMPLIFY = "amplify"          # 放量复制


@dataclass
class FlywheelInsight:
    """飞轮洞察"""
    insight_type: str             # pattern / anomaly / opportunity
    description: str
    confidence: float = 0.0
    actionable: bool = False
    impact_estimate: str = ""     # 预估影响
    suggestion: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "type": self.insight_type,
            "description": self.description,
            "confidence": self.confidence,
            "actionable": self.actionable,
            "impact_estimate": self.impact_estimate,
            "suggestion": self.suggestion,
        }


class DataFlywheelEngine:
    """数据飞轮引擎。

    "越用越聪明"的获客系统：
    1. 收集：每次交互都记录数据
    2. 分析：从数据中学习最佳实践
    3. 优化：自动调整策略参数
    4. 放大：将成功模式复制到新线索
    """
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._patterns: dict[str, Any] = {}
        self._insights: list[FlywheelInsight] = []
        self._stage = DataFlywheelStage.COLLECT

    def learn_from_interaction(
        self,
        interaction_type: str,  # "open", "click", "reply", "bounce", "unsubscribe"
        email_data: dict[str, Any],
        lead_data: dict[str, Any],
    ) -> None:
        """从交互中学习。

        Args:
            interaction_type: 交互类型
            email_data: 邮件数据 {subject, body, template, time, day_of_week}
            lead_data: 线索数据 {industry, role, country, company_size}
        """
        # 记录模式
        key_parts = [
            interaction_type,
            lead_data.get("industry", "unknown"),
            lead_data.get("role", "unknown"),
            email_data.get("day_of_week", "unknown"),
        ]
        pattern_key = "|".join(key_parts)
        if pattern_key not in self._patterns:
            self._patterns[pattern_key] = {
                "total": 0,
                "opens": 0,
                "clicks": 0,
                "replies": 0,
                "bounces": 0,
            }

        stats = self._patterns[pattern_key]
        stats["total"] += 1
        if interaction_type in stats:
            stats[interaction_type] += 1

    def analyze_patterns(self) -> list[FlywheelInsight]:
        """分析模式生成洞察。"""
        insights: list[FlywheelInsight] = []
        # 按行业分析
        industry_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "opens": 0, "replies": 0})
        for key, stats in self._patterns.items():
            parts = key.split("|")
            if len(parts) >= 2:
                industry = parts[1]
                industry_stats[industry]["total"] += stats["total"]
                industry_stats[industry]["opens"] += stats["opens"]
                industry_stats[industry]["replies"] += stats["replies"]

        for industry, stats in industry_stats.items():
            if stats["total"] >= 10:
                open_rate = stats["opens"] / max(1, stats["total"])
                reply_rate = stats["replies"] / max(1, stats["total"])
                if open_rate > 0.5:
                    insights.append(FlywheelInsight(
                        insight_type="pattern",
                        description=f"{industry} 行业打开率 {open_rate:.0%}，高于平均水平",
                        confidence=min(0.9, open_rate),
                        actionable=True,
                        impact_estimate=f"增加该行业获客投入可提升 {open_rate:.0%} 打开率",
                        suggestion=f"优先向 {industry} 行业客户发送开发信",
                    ))

                if reply_rate > 0.1:
                    insights.append(FlywheelInsight(
                        insight_type="opportunity",
                        description=f"{industry} 行业回复率 {reply_rate:.0%}，转化潜力高",
                        confidence=min(0.8, reply_rate * 5),
                        actionable=True,
                        impact_estimate=f"该行业预期转化率 {reply_rate:.0%}",
                        suggestion=f"加大 {industry} 行业投入，使用行业定制化模板",
                    ))

        # 按星期分析
        dow_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "opens": 0})
        for key, stats in self._patterns.items():
            parts = key.split("|")
            if len(parts) >= 4:
                dow = parts[3]
                dow_stats[dow]["total"] += stats["total"]
                dow_stats[dow]["opens"] += stats["opens"]

        best_dow = max(dow_stats.items(), key=lambda x: x[1]["opens"] / max(1, x[1]["total"]), default=(None, {}))
        if best_dow[0] and dow_stats[best_dow[0]]["total"] >= 20:
            best_rate = best_dow[1]["opens"] / max(1, best_dow[1]["total"])
            insights.append(FlywheelInsight(
                insight_type="pattern",
                description=f"最佳发送日: {best_dow[0]}，打开率 {best_rate:.0%}",
                confidence=0.7,
                actionable=True,
                impact_estimate="优化发送时间可提升 10-15% 打开率",
                suggestion=f"将主要发送安排在 {best_dow[0]}",
            ))

        self._insights = insights
        self._stage = DataFlywheelStage.OPTIMIZE
        return insights

    def get_optimization_suggestions(self) -> list[dict[str, Any]]:
        """获取优化建议。"""
        if not self._insights:
            self.analyze_patterns()

        return [
            {
                "insight": i.description,
                "action": i.suggestion,
                "expected_impact": i.impact_estimate,
                "confidence": i.confidence,
            }
            for i in self._insights
            if i.actionable
        ]

    def get_stage(self) -> str:
        """get_stage。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self._stage.value

    def reset(self) -> None:
        """reset。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._patterns.clear()
        self._insights.clear()
        self._stage = DataFlywheelStage.COLLECT


# ═══════════════════════════════════════════════════════════
# FIX-64: 敏感字段加密审计
# ═══════════════════════════════════════════════════════════

class EncryptionAlgorithm(str, Enum):
    AES256_GCM = "AES-256-GCM"
    FERNET = "Fernet"


@dataclass
class EncryptedField:
    """加密字段"""
    field_name: str
    original_value: str = ""
    encrypted_value: str = ""
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET
    key_id: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "field_name": self.field_name,
            "encrypted": bool(self.encrypted_value),
            "algorithm": self.algorithm.value,
            "key_id": self.key_id,
        }


class FieldEncryptionService:
    """敏感字段加密服务。

    使用 Fernet（AES-128-CBC + HMAC）进行对称加密。
    密钥派生：PBKDF2HMAC(SHA256) from ENCRYPTION_SECRET_KEY
    """
    SENSITIVE_FIELDS = [
        "email", "phone", "password", "secret_key", "api_key",
        "access_token", "refresh_token", "private_key", "credit_card",
        "passport", "id_number", "address", "ssn", "bank_account",
        "medical_record", "biometric_data",
    ]
    def __init__(self, secret_key: str = ""):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param secret_key: 参数 secret_key
        :return: 返回处理结果。
        """
        self._secret_key = secret_key or os.getenv("ENCRYPTION_SECRET_KEY", "")
        self._fernet: Optional[Fernet] = None
        if self._secret_key:
            self._init_fernet()

    def _init_fernet(self) -> None:
        """初始化 Fernet 加密器。"""
        try:
            # 如果密钥是 base64 格式的 Fernet key
            key = self._secret_key.encode()
            if len(key) == 44 and key.endswith(b"="):
                self._fernet = Fernet(key)
            else:
                # 使用 PBKDF2 派生
                salt = b"uj_salt_2024_fixed"
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=480000,
                )
                derived_key = b64encode(kdf.derive(key))
                self._fernet = Fernet(derived_key)
        except Exception as e:
            logger.error("Failed to init Fernet: %s", e)
            self._fernet = None

    def is_configured(self) -> bool:
        """is_configured。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return self._fernet is not None

    def encrypt(self, plaintext: str) -> str:
        """加密敏感字段。"""
        if not self._fernet or not plaintext:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        """解密敏感字段。"""
        if not self._fernet or not ciphertext:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ciphertext  # 可能未加密

    def is_sensitive_field(self, field_name: str) -> bool:
        """判断是否为敏感字段。"""
        name_lower = field_name.lower()
        return any(
            sensitive in name_lower
            for sensitive in self.SENSITIVE_FIELDS
        )

    def audit_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """审计数据中的敏感字段。

        Args:
            data: 待审计数据

        Returns:
            审计结果
        """
        findings = []
        encrypted_count = 0
        unencrypted_count = 0
        for key, value in data.items():
            if self.is_sensitive_field(key) and value:
                if isinstance(value, str) and len(value) > 100:
                    # 可能是已加密的
                    encrypted_count += 1
                    findings.append({
                        "field": key,
                        "status": "encrypted",
                        "risk": "low",
                    })
                else:
                    unencrypted_count += 1
                    findings.append({
                        "field": key,
                        "status": "unencrypted",
                        "risk": "high",
                        "action": "需要加密",
                    })

        return {
            "total_fields": len(data),
            "sensitive_fields": encrypted_count + unencrypted_count,
            "encrypted": encrypted_count,
            "unencrypted": unencrypted_count,
            "risk_level": "high" if unencrypted_count > 0 else "low",
            "findings": findings,
            "recommendation": (
                "所有敏感字段已加密" if unencrypted_count == 0
                else f"发现 {unencrypted_count} 个未加密敏感字段，建议立即加密"
            ),
        }

    def encrypt_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """加密记录中的所有敏感字段。"""
        encrypted = {}
        for key, value in record.items():
            if self.is_sensitive_field(key) and isinstance(value, str) and value:
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value
        return encrypted

    def decrypt_record(self, record: dict[str, Any]) -> dict[str, Any]:
        """解密记录中的所有敏感字段。"""
        decrypted = {}
        for key, value in record.items():
            if self.is_sensitive_field(key) and isinstance(value, str) and value:
                decrypted[key] = self.decrypt(value)
            else:
                decrypted[key] = value
        return decrypted


# ═══════════════════════════════════════════════════════════
# FIX-65: AI 安全（LLM 输入/输出安全）
# ═══════════════════════════════════════════════════════════

class AISecurityRisk(str, Enum):
    PROMPT_INJECTION = "prompt_injection"
    DATA_LEAKAGE = "data_leakage"
    JAILBREAK = "jailbreak"
    TOXIC_OUTPUT = "toxic_output"
    PII_EXPOSURE = "pii_exposure"
    HALLUCINATION = "hallucination"
    BIAS = "bias"


@dataclass
class AISecurityScanResult:
    """AI 安全扫描结果"""
    input_text: str
    output_text: str = ""
    risks: list[dict] = field(default_factory=list)
    risk_score: float = 0.0       # 0-1
    blocked: bool = False
    sanitized_input: str = ""
    sanitized_output: str = ""
    def to_dict(self) -> dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "input_length": len(self.input_text),
            "output_length": len(self.output_text),
            "risks": self.risks,
            "risk_score": round(self.risk_score, 2),
            "blocked": self.blocked,
            "sanitized": bool(self.sanitized_input),
        }


class AISecurityGuard:
    """AI 安全守卫。

    防护层：
    1. 输入净化：移除 PII、检测注入攻击
    2. 输出过滤：检测有害内容、幻觉标记
    3. 审计日志：记录所有 AI 交互
    """
    # Prompt 注入模式
    INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions?",
        r"you\s+are\s+now\s+(a\s+)?\w+",
        r"system\s*:\s*",
        r"<\|im_start\|>",
        r"<\|system\|>",
        r"\[INST\].*\[/INST\]",
        r"forget\s+(all\s+)?(previous|above|prior)\s+",
        r"new\s+instructions?\s*:",
        r"override\s+(all\s+)?(previous|above|prior)\s+",
        r"you\s+must\s+(always|never)\s+",
        r"pretend\s+you\s+are\s+",
        r"roleplay\s+as\s+",
        r"act\s+as\s+(if\s+)?(you\s+are\s+)?",
        # DAN prompt
        r"do\s+anything\s+now",
        r"DAN\s+mode",
        # 越狱尝试
        r"jailbreak",
        r"bypass\s+(restrictions?|filter|guard)",
        r"without\s+(any\s+)?(restrictions?|limitations?|rules?)",
        r"ethical\s+(guidelines?|restrictions?|rules?)",
    ]
    # PII 模式
    PII_PATTERNS = {
        "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "phone": r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "api_key": r'(api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*[\w-]+',
    }
    # 有害内容关键词
    TOXIC_KEYWORDS = [
        "hate speech", "violence", "self-harm", "suicide",
        "illegal", "exploit", "malware", "phishing",
        "discrimination", "harassment",
    ]
    def scan_input(self, text: str) -> AISecurityScanResult:
        """扫描 AI 输入文本。

        Args:
            text: 用户输入文本

        Returns:
            安全扫描结果
        """
        result = AISecurityScanResult(input_text=text)
        text_lower = text.lower()
        risk_score = 0.0
        # 1. Prompt 注入检测
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result.risks.append({
                    "type": AISecurityRisk.PROMPT_INJECTION.value,
                    "severity": "critical",
                    "pattern": pattern,
                })
                risk_score += 0.4
                break

        # 2. PII 检测
        for pii_type, pattern in self.PII_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                result.risks.append({
                    "type": AISecurityRisk.PII_EXPOSURE.value,
                    "severity": "high",
                    "pii_type": pii_type,
                    "count": len(matches),
                })
                risk_score += 0.15

        # 3. 越狱尝试
        jailbreak_keywords = ["jailbreak", "bypass", "ignore instructions", "pretend"]
        if any(kw in text_lower for kw in jailbreak_keywords):
            result.risks.append({
                "type": AISecurityRisk.JAILBREAK.value,
                "severity": "critical",
            })
            risk_score += 0.5

        # 4. 数据泄露检测
        if len(text) > 5000:
            result.risks.append({
                "type": AISecurityRisk.DATA_LEAKAGE.value,
                "severity": "medium",
                "detail": "输入过长，可能包含大量数据",
            })
            risk_score += 0.1

        result.risk_score = min(1.0, risk_score)
        result.blocked = result.risk_score >= 0.8
        # 净化输入
        if result.risks:
            result.sanitized_input = self._sanitize_text(text)

        return result

    def scan_output(self, text: str) -> AISecurityScanResult:
        """扫描 AI 输出文本。

        Args:
            text: AI 输出文本

        Returns:
            安全扫描结果
        """
        result = AISecurityScanResult(input_text="", output_text=text)
        risk_score = 0.0
        # 1. 有害内容检测
        text_lower = text.lower()
        for keyword in self.TOXIC_KEYWORDS:
            if keyword in text_lower:
                result.risks.append({
                    "type": AISecurityRisk.TOXIC_OUTPUT.value,
                    "severity": "critical",
                    "keyword": keyword,
                })
                risk_score += 0.5
                break

        # 2. PII 泄露
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, text):
                result.risks.append({
                    "type": AISecurityRisk.PII_EXPOSURE.value,
                    "severity": "high",
                    "pii_type": pii_type,
                })
                risk_score += 0.3
                break

        # 3. 幻觉标记
        hallucination_signals = [
            "I don't know for sure", "I'm not certain", "I could be wrong",
            "it's possible that", "some sources say", "according to some",
        ]
        if any(signal in text_lower for signal in hallucination_signals):
            result.risks.append({
                "type": AISecurityRisk.HALLUCINATION.value,
                "severity": "low",
            })
            risk_score += 0.05

        result.risk_score = min(1.0, risk_score)
        result.blocked = result.risk_score >= 0.8
        if result.risks:
            result.sanitized_output = self._sanitize_text(text)

        return result

    def _sanitize_text(self, text: str) -> str:
        """净化文本：移除 PII。"""
        sanitized = text
        for pii_type, pattern in self.PII_PATTERNS.items():
            sanitized = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", sanitized)
        return sanitized

    def audit_log_entry(
        self,
        user_id: str,
        model: str,
        input_text: str,
        output_text: str,
        input_scan: AISecurityScanResult,
        output_scan: AISecurityScanResult,
    ) -> dict[str, Any]:
        """生成 AI 审计日志条目。"""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "model": model,
            "input_length": len(input_text),
            "output_length": len(output_text),
            "input_risk_score": input_scan.risk_score,
            "output_risk_score": output_scan.risk_score,
            "blocked": input_scan.blocked or output_scan.blocked,
            "input_risks": [r["type"] for r in input_scan.risks],
            "output_risks": [r["type"] for r in output_scan.risks],
        }


# 单例
email_send_queue = EmailSendQueue()
data_flywheel_engine = DataFlywheelEngine()
field_encryption_service = FieldEncryptionService()
ai_security_guard = AISecurityGuard()