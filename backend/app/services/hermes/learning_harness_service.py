# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
学习更新服务 (Learning Harness)

增强AI系统的自我学习和进化能力，支持：
- 用户反馈学习
- 内容质量反馈
- 市场趋势学习
- 模型性能监控与优化
- 知识图谱更新
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from datetime import datetime, timedelta

FEEDBACK_TYPES = ["quality", "accuracy", "relevance", "completeness", "style"]


class LearningHarnessService:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._feedback_store: Dict[str, List[Dict[str, Any]]] = {}
        self._learning_rules: Dict[str, Dict[str, Any]] = {}
        self._performance_metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._knowledge_updates: List[Dict[str, Any]] = []
        self._init_learning_rules()

    def _init_learning_rules(self):
        """_init_learning_rules。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._learning_rules = {
            "content_quality": {
                "min_feedback_count": 5,
                "threshold": 0.7,
                "action": "optimize_prompt",
                "description": "内容质量低于阈值时优化Prompt",
            },
            "accuracy_improvement": {
                "min_feedback_count": 3,
                "threshold": 0.8,
                "action": "update_knowledge",
                "description": "准确率高于阈值时更新知识",
            },
            "relevance_threshold": {
                "min_feedback_count": 5,
                "threshold": 0.6,
                "action": "adjust_routing",
                "description": "相关性低于阈值时调整路由",
            },
        }

    def record_feedback(
        self,
        content_id: str,
        feedback_type: str,
        score: float,
        user_id: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """record_feedback。

        参数说明：
        :param self: 参数 self
        :param content_id: 参数 content_id
        :param feedback_type: 参数 feedback_type
        :param score: 参数 score
        :param user_id: 参数 user_id
        :param comment: 参数 comment
        :param metadata: 参数 metadata
        :return: 返回处理结果。
        """
        if feedback_type not in FEEDBACK_TYPES:
            return {"success": False, "error": f"无效反馈类型: {feedback_type}"}

        if score < 0 or score > 1:
            return {"success": False, "error": "评分必须在0-1之间"}

        feedback = {
            "feedback_id": f"fb_{content_id}_{datetime.now().timestamp()}",
            "content_id": content_id,
            "feedback_type": feedback_type,
            "score": score,
            "user_id": user_id,
            "comment": comment,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        if content_id not in self._feedback_store:
            self._feedback_store[content_id] = []
        self._feedback_store[content_id].append(feedback)
        self._process_learning(feedback)
        return {"success": True, "feedback_id": feedback["feedback_id"]}

    def _process_learning(self, feedback: Dict[str, Any]):
        """_process_learning。

        参数说明：
        :param self: 参数 self
        :param feedback: 参数 feedback
        :return: 返回处理结果。
        """
        content_id = feedback["content_id"]
        feedback_type = feedback["feedback_type"]
        score = feedback["score"]
        rule = self._learning_rules.get(feedback_type)
        if not rule:
            return

        feedbacks = self._feedback_store.get(content_id, [])
        type_feedbacks = [f for f in feedbacks if f["feedback_type"] == feedback_type]
        if len(type_feedbacks) >= rule["min_feedback_count"]:
            avg_score = sum(f["score"] for f in type_feedbacks) / len(type_feedbacks)
            if avg_score < rule["threshold"]:
                self._trigger_action(rule["action"], {
                    "content_id": content_id,
                    "feedback_type": feedback_type,
                    "avg_score": avg_score,
                    "threshold": rule["threshold"],
                    "feedback_count": len(type_feedbacks),
                })

    def _trigger_action(self, action: str, context: Dict[str, Any]):
        """_trigger_action。

        参数说明：
        :param self: 参数 self
        :param action: 参数 action
        :param context: 参数 context
        :return: 返回处理结果。
        """
        update = {
            "action": action,
            "context": context,
            "triggered_at": datetime.now().isoformat(),
            "status": "pending",
        }
        self._knowledge_updates.append(update)

    def get_content_feedback(self, content_id: str) -> Dict[str, Any]:
        """get_content_feedback。

        参数说明：
        :param self: 参数 self
        :param content_id: 参数 content_id
        :return: 返回处理结果。
        """
        feedbacks = self._feedback_store.get(content_id, [])
        if not feedbacks:
            return {"content_id": content_id, "feedbacks": [], "summary": {}}

        summary = {}
        for feedback_type in FEEDBACK_TYPES:
            type_feedbacks = [f for f in feedbacks if f["feedback_type"] == feedback_type]
            if type_feedbacks:
                summary[feedback_type] = {
                    "count": len(type_feedbacks),
                    "avg_score": sum(f["score"] for f in type_feedbacks) / len(type_feedbacks),
                    "latest": type_feedbacks[-1]["score"],
                }

        return {
            "content_id": content_id,
            "total_feedbacks": len(feedbacks),
            "feedbacks": feedbacks,
            "summary": summary,
        }

    def record_performance(
        self,
        model_type: str,
        task_id: str,
        latency_ms: float,
        success: bool,
        error_message: Optional[str] = None,
        token_usage: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """record_performance。

        参数说明：
        :param self: 参数 self
        :param model_type: 参数 model_type
        :param task_id: 参数 task_id
        :param latency_ms: 参数 latency_ms
        :param success: 参数 success
        :param error_message: 参数 error_message
        :param token_usage: 参数 token_usage
        :param metadata: 参数 metadata
        :return: 返回处理结果。
        """
        metric = {
            "task_id": task_id,
            "model_type": model_type,
            "latency_ms": latency_ms,
            "success": success,
            "error_message": error_message,
            "token_usage": token_usage,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        if model_type not in self._performance_metrics:
            self._performance_metrics[model_type] = []
        self._performance_metrics[model_type].append(metric)
        return {"success": True, "recorded": metric}

    def get_performance_stats(self, model_type: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """get_performance_stats。

        参数说明：
        :param self: 参数 self
        :param model_type: 参数 model_type
        :param days: 参数 days
        :return: 返回处理结果。
        """
        cutoff = datetime.now() - timedelta(days=days)
        results = {}
        types = [model_type] if model_type else self._performance_metrics.keys()
        for mt in types:
            metrics = self._performance_metrics.get(mt, [])
            recent_metrics = [
                m for m in metrics
                if datetime.fromisoformat(m["created_at"].replace("Z", "+00:00")) >= cutoff
            ]
            if not recent_metrics:
                continue

            total = len(recent_metrics)
            success_count = sum(1 for m in recent_metrics if m["success"])
            avg_latency = sum(m["latency_ms"] for m in recent_metrics) / total
            avg_tokens = sum(m["token_usage"] or 0 for m in recent_metrics) / total
            errors = [m["error_message"] for m in recent_metrics if m["error_message"]]
            error_counts: Dict[str, int] = {}
            for error in errors:
                error_counts[error] = error_counts.get(error, 0) + 1

            results[mt] = {
                "total_tasks": total,
                "success_rate": success_count / total,
                "avg_latency_ms": avg_latency,
                "avg_token_usage": avg_tokens,
                "error_counts": error_counts,
                "period_days": days,
            }

        return results

    def suggest_optimizations(self, days: int = 7) -> List[Dict[str, Any]]:
        """suggest_optimizations。

        参数说明：
        :param self: 参数 self
        :param days: 参数 days
        :return: 返回处理结果。
        """
        optimizations = []
        stats = self.get_performance_stats(days=days)
        for model_type, stat in stats.items():
            if stat["success_rate"] < 0.9:
                optimizations.append({
                    "model_type": model_type,
                    "type": "reliability",
                    "severity": "high" if stat["success_rate"] < 0.8 else "medium",
                    "message": f"成功率 {stat['success_rate']*100:.1f}% 低于阈值",
                    "suggestion": "检查API密钥配置、网络连接或切换备用模型",
                    "data": stat,
                })

            if stat["avg_latency_ms"] > 5000:
                optimizations.append({
                    "model_type": model_type,
                    "type": "performance",
                    "severity": "medium",
                    "message": f"平均延迟 {stat['avg_latency_ms']:.0f}ms 过高",
                    "suggestion": "考虑使用更快的模型或优化请求参数",
                    "data": stat,
                })

        for content_id, feedbacks in self._feedback_store.items():
            summary = self.get_content_feedback(content_id)["summary"]
            for feedback_type, stats in summary.items():
                if stats["avg_score"] < 0.7:
                    optimizations.append({
                        "content_id": content_id,
                        "type": "quality",
                        "severity": "medium",
                        "message": f"{feedback_type} 平均评分 {stats['avg_score']*100:.1f}% 低于阈值",
                        "suggestion": "优化相关Prompt模板或调整内容生成策略",
                        "data": stats,
                    })

        return optimizations

    def apply_knowledge_update(self, update_id: str, changes: Dict[str, Any]) -> Dict[str, Any]:
        """apply_knowledge_update。

        参数说明：
        :param self: 参数 self
        :param update_id: 参数 update_id
        :param changes: 参数 changes
        :return: 返回处理结果。
        """
        for update in self._knowledge_updates:
            if update["action"] == update_id:
                update["status"] = "applied"
                update["applied_at"] = datetime.now().isoformat()
                update["changes"] = changes
                return {"success": True, "update": update}

        return {"success": False, "error": "更新不存在"}

    def get_pending_updates(self) -> List[Dict[str, Any]]:
        """get_pending_updates。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return [u for u in self._knowledge_updates if u["status"] == "pending"]

    def get_learning_summary(self) -> Dict[str, Any]:
        """get_learning_summary。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        total_feedbacks = sum(len(f) for f in self._feedback_store.values())
        total_performance_records = sum(len(p) for p in self._performance_metrics.values())
        pending_updates = len(self.get_pending_updates())
        return {
            "total_feedbacks": total_feedbacks,
            "total_performance_records": total_performance_records,
            "pending_updates": pending_updates,
            "feedback_types": FEEDBACK_TYPES,
            "learning_rules": len(self._learning_rules),
            "timestamp": datetime.now().isoformat(),
        }

    def export_learning_data(self) -> str:
        """export_learning_data。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return json.dumps({
            "feedback_store": self._feedback_store,
            "performance_metrics": self._performance_metrics,
            "knowledge_updates": self._knowledge_updates,
            "learning_rules": self._learning_rules,
        }, ensure_ascii=False, indent=2)

    def import_learning_data(self, data_json: str) -> Dict[str, Any]:
        """import_learning_data。

        参数说明：
        :param self: 参数 self
        :param data_json: 参数 data_json
        :return: 返回处理结果。
        """
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "JSON格式错误"}

        if "feedback_store" in data:
            self._feedback_store = data["feedback_store"]

        if "performance_metrics" in data:
            self._performance_metrics = data["performance_metrics"]

        if "knowledge_updates" in data:
            self._knowledge_updates = data["knowledge_updates"]

        if "learning_rules" in data:
            self._learning_rules = data["learning_rules"]

        return {"success": True}
