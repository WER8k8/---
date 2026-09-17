# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
评分分发服务 (Scoring Harness)

扩展现有评分能力，支持多维度评分、评分规则管理、评分分发策略。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from datetime import datetime

SCORING_DIMENSIONS = {
    "content_quality": {
        "name": "内容质量",
        "weight": 0.25,
        "min_score": 0,
        "max_score": 100,
        "description": "评估内容的专业度、准确性和完整性",
    },
    "seo_relevance": {
        "name": "SEO相关性",
        "weight": 0.20,
        "min_score": 0,
        "max_score": 100,
        "description": "评估内容与关键词的相关性和SEO优化程度",
    },
    "brand_consistency": {
        "name": "品牌一致性",
        "weight": 0.15,
        "min_score": 0,
        "max_score": 100,
        "description": "评估内容与品牌声音和风格的一致性",
    },
    "technical_accuracy": {
        "name": "技术准确性",
        "weight": 0.25,
        "min_score": 0,
        "max_score": 100,
        "description": "评估技术参数和标准引用的准确性",
    },
    "readability": {
        "name": "可读性",
        "weight": 0.15,
        "min_score": 0,
        "max_score": 100,
        "description": "评估内容的阅读体验和表达清晰度",
    },
}


class ScoringHarnessService:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._dimensions = SCORING_DIMENSIONS
        self._score_history: Dict[str, List[Dict[str, Any]]] = {}
        self._score_rules: Dict[str, Dict[str, Any]] = {}
        self._init_score_rules()

    def _init_score_rules(self):
        """_init_score_rules。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._score_rules = {
            "auto_approve": {
                "condition": "total_score >= 80",
                "action": "auto_approve",
                "description": "总分>=80自动通过",
            },
            "manual_review": {
                "condition": "total_score >= 60 && total_score < 80",
                "action": "manual_review",
                "description": "总分60-80需人工审核",
            },
            "revision_required": {
                "condition": "total_score < 60",
                "action": "revision_required",
                "description": "总分<60需要修改",
            },
            "technical_failure": {
                "condition": "technical_accuracy < 50",
                "action": "block",
                "description": "技术准确性<50直接拒绝",
            },
        }

    def calculate_score(self, content_id: str, scores: Dict[str, float]) -> Dict[str, Any]:
        """calculate_score。

        参数说明：
        :param self: 参数 self
        :param content_id: 参数 content_id
        :param scores: 参数 scores
        :return: 返回处理结果。
        """
        total_weight = sum(dim["weight"] for dim in self._dimensions.values())
        total_score = 0.0
        dimension_scores = {}
        for dimension_key, dim in self._dimensions.items():
            raw_score = scores.get(dimension_key, 0)
            clamped_score = max(dim["min_score"], min(dim["max_score"], raw_score))
            weighted_score = clamped_score * dim["weight"]
            total_score += weighted_score
            dimension_scores[dimension_key] = {
                "raw_score": raw_score,
                "clamped_score": clamped_score,
                "weight": dim["weight"],
                "weighted_score": weighted_score,
                "name": dim["name"],
            }

        normalized_score = (total_score / total_weight) if total_weight > 0 else 0
        result = {
            "content_id": content_id,
            "total_score": round(normalized_score, 2),
            "dimension_scores": dimension_scores,
            "score_rules_applied": [],
            "action": self._determine_action(normalized_score, dimension_scores),
            "calculated_at": datetime.now().isoformat(),
        }
        self._record_score(content_id, result)
        return result

    def _determine_action(self, total_score: float, dimension_scores: Dict[str, Any]) -> str:
        """_determine_action。

        参数说明：
        :param self: 参数 self
        :param total_score: 参数 total_score
        :param dimension_scores: 参数 dimension_scores
        :return: 返回处理结果。
        """
        if dimension_scores.get("technical_accuracy", {}).get("clamped_score", 0) < 50:
            return "block"

        if total_score >= 80:
            return "auto_approve"

        if total_score >= 60:
            return "manual_review"

        return "revision_required"

    def _record_score(self, content_id: str, score_result: Dict[str, Any]):
        """_record_score。

        参数说明：
        :param self: 参数 self
        :param content_id: 参数 content_id
        :param score_result: 参数 score_result
        :return: 返回处理结果。
        """
        if content_id not in self._score_history:
            self._score_history[content_id] = []
        self._score_history[content_id].append(score_result)

    def get_score_history(self, content_id: str) -> Dict[str, Any]:
        """get_score_history。

        参数说明：
        :param self: 参数 self
        :param content_id: 参数 content_id
        :return: 返回处理结果。
        """
        history = self._score_history.get(content_id, [])
        if not history:
            return {"content_id": content_id, "history": [], "latest": None}

        latest = history[-1]
        avg_scores = {}
        for dim in self._dimensions:
            dim_scores = [h["dimension_scores"].get(dim, {}).get("clamped_score", 0) for h in history]
            if dim_scores:
                avg_scores[dim] = sum(dim_scores) / len(dim_scores)

        return {
            "content_id": content_id,
            "total_scores": len(history),
            "history": history,
            "latest": latest,
            "average_scores": avg_scores,
        }

    def get_dimensions(self) -> List[Dict[str, Any]]:
        """get_dimensions。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        dimensions = []
        for key, dim in self._dimensions.items():
            dimensions.append({
                "key": key,
                "name": dim["name"],
                "weight": dim["weight"],
                "min_score": dim["min_score"],
                "max_score": dim["max_score"],
                "description": dim["description"],
            })
        return dimensions

    def update_dimension_weight(self, dimension_key: str, weight: float) -> Dict[str, Any]:
        """update_dimension_weight。

        参数说明：
        :param self: 参数 self
        :param dimension_key: 参数 dimension_key
        :param weight: 参数 weight
        :return: 返回处理结果。
        """
        if dimension_key not in self._dimensions:
            return {"success": False, "error": "维度不存在"}

        if weight < 0 or weight > 1:
            return {"success": False, "error": "权重必须在0-1之间"}

        self._dimensions[dimension_key]["weight"] = weight
        total_weight = sum(dim["weight"] for dim in self._dimensions.values())
        if total_weight != 1.0:
            return {
                "success": True,
                "warning": f"总权重为 {total_weight:.2f}，建议调整为1.0",
                "dimension_key": dimension_key,
                "weight": weight,
            }

        return {"success": True, "dimension_key": dimension_key, "weight": weight}

    def get_score_rules(self) -> List[Dict[str, Any]]:
        """get_score_rules。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        rules = []
        for key, rule in self._score_rules.items():
            rules.append({
                "key": key,
                "condition": rule["condition"],
                "action": rule["action"],
                "description": rule["description"],
            })
        return rules

    def add_score_rule(self, rule_key: str, rule: Dict[str, Any]) -> Dict[str, Any]:
        """add_score_rule。

        参数说明：
        :param self: 参数 self
        :param rule_key: 参数 rule_key
        :param rule: 参数 rule
        :return: 返回处理结果。
        """
        if rule_key in self._score_rules:
            return {"success": False, "error": "规则已存在"}

        if "condition" not in rule or "action" not in rule:
            return {"success": False, "error": "缺少条件或动作"}

        self._score_rules[rule_key] = {
            "condition": rule["condition"],
            "action": rule["action"],
            "description": rule.get("description", ""),
            "created_at": datetime.now().isoformat(),
        }
        return {"success": True, "rule_key": rule_key}

    def remove_score_rule(self, rule_key: str) -> Dict[str, Any]:
        """remove_score_rule。

        参数说明：
        :param self: 参数 self
        :param rule_key: 参数 rule_key
        :return: 返回处理结果。
        """
        if rule_key not in self._score_rules:
            return {"success": False, "error": "规则不存在"}

        del self._score_rules[rule_key]
        return {"success": True, "rule_key": rule_key}

    def get_score_summary(self) -> Dict[str, Any]:
        """get_score_summary。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        total_scores = sum(len(h) for h in self._score_history.values())
        total_contents = len(self._score_history)
        action_counts: Dict[str, int] = {"auto_approve": 0, "manual_review": 0, "revision_required": 0, "block": 0}
        for history in self._score_history.values():
            for score in history:
                action = score.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + 1

        avg_total_score = 0.0
        count = 0
        for history in self._score_history.values():
            for score in history:
                avg_total_score += score.get("total_score", 0)
                count += 1
        if count > 0:
            avg_total_score /= count

        return {
            "total_scores": total_scores,
            "total_contents": total_contents,
            "average_total_score": round(avg_total_score, 2),
            "action_distribution": action_counts,
            "dimensions_count": len(self._dimensions),
            "rules_count": len(self._score_rules),
            "timestamp": datetime.now().isoformat(),
        }

    def export_scores(self) -> str:
        """export_scores。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return json.dumps({
            "dimensions": self._dimensions,
            "score_rules": self._score_rules,
            "score_history": self._score_history,
        }, ensure_ascii=False, indent=2)

    def import_scores(self, scores_json: str) -> Dict[str, Any]:
        """import_scores。

        参数说明：
        :param self: 参数 self
        :param scores_json: 参数 scores_json
        :return: 返回处理结果。
        """
        try:
            data = json.loads(scores_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "JSON格式错误"}

        if "dimensions" in data:
            self._dimensions = data["dimensions"]

        if "score_rules" in data:
            self._score_rules = data["score_rules"]

        if "score_history" in data:
            self._score_history = data["score_history"]

        return {"success": True}
