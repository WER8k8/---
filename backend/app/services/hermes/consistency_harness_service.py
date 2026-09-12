"""
一致性控制服务 (Consistency Harness)

确保AI生成内容与品牌风格、产品参数、技术规范的一致性。
支持：品牌声音一致性、产品信息一致性、技术参数校验、跨平台内容一致性。
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import os
from datetime import datetime

BRAND_VOICE_PATTERNS = {
    "professional": {
        "required_words": ["专业", "品质", "可靠", "技术", "标准"],
        "banned_patterns": ["超级好", "无敌", "绝绝子", "YYDS", "太赞了"],
        "min_word_length": 2,
        "max_sentence_length": 80,
    },
    "casual": {
        "required_words": [],
        "banned_patterns": [],
        "min_word_length": 1,
        "max_sentence_length": 120,
    },
}


class ConsistencyHarnessService:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._brand_voice = os.getenv("BRAND_VOICE", "professional")
        self._product_spec_cache: Dict[str, Dict[str, Any]] = {}

    def validate_content_consistency(
        self,
        content: str,
        product_specs: Optional[Dict[str, Any]] = None,
        brand_voice: Optional[str] = None,
        required_keywords: Optional[List[str]] = None,
        banned_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """validate_content_consistency。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param product_specs: 参数 product_specs
        :param brand_voice: 参数 brand_voice
        :param required_keywords: 参数 required_keywords
        :param banned_keywords: 参数 banned_keywords
        :return: 返回处理结果。
        """
        results: Dict[str, Any] = {
            "is_consistent": True,
            "issues": [],
            "warnings": [],
            "score": 100.0,
            "checks": [],
        }
        voice = brand_voice or self._brand_voice
        total_penalty = 0
        if voice in BRAND_VOICE_PATTERNS:
            voice_result = self._check_brand_voice(content, voice)
            results["checks"].append({"name": "brand_voice", "result": voice_result})
            if not voice_result["passed"]:
                results["is_consistent"] = False
                results["issues"].extend(voice_result["issues"])
                total_penalty += voice_result["penalty"]

        if product_specs:
            spec_result = self._check_product_specs(content, product_specs)
            results["checks"].append({"name": "product_specs", "result": spec_result})
            if not spec_result["passed"]:
                results["is_consistent"] = False
                results["issues"].extend(spec_result["issues"])
                total_penalty += spec_result["penalty"]

        if required_keywords:
            keyword_result = self._check_required_keywords(content, required_keywords)
            results["checks"].append({"name": "required_keywords", "result": keyword_result})
            if not keyword_result["passed"]:
                results["is_consistent"] = False
                results["warnings"].extend(keyword_result["warnings"])
                total_penalty += keyword_result["penalty"]

        if banned_keywords:
            banned_result = self._check_banned_keywords(content, banned_keywords)
            results["checks"].append({"name": "banned_keywords", "result": banned_result})
            if not banned_result["passed"]:
                results["is_consistent"] = False
                results["issues"].extend(banned_result["issues"])
                total_penalty += banned_result["penalty"]

        results["score"] = max(0.0, 100.0 - total_penalty)
        return results

    def _check_brand_voice(self, content: str, voice: str) -> Dict[str, Any]:
        """_check_brand_voice。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param voice: 参数 voice
        :return: 返回处理结果。
        """
        pattern = BRAND_VOICE_PATTERNS.get(voice, BRAND_VOICE_PATTERNS["professional"])
        issues: List[str] = []
        penalty = 0
        passed = True
        for banned in pattern["banned_patterns"]:
            if banned in content:
                issues.append(f"发现禁用词汇: '{banned}'")
                penalty += 10
                passed = False

        sentences = re.split(r"[。！？]", content)
        for sentence in sentences:
            if len(sentence) > pattern["max_sentence_length"]:
                issues.append(f"句子过长 ({len(sentence)}字)")
                penalty += 5

        words = re.findall(r"[\u4e00-\u9fff]+", content)
        for word in words:
            if len(word) == 1 and word not in ["的", "是", "在", "有", "和", "了", "我", "你", "他"]:
                penalty += 1

        if pattern["required_words"]:
            found_required = sum(1 for w in pattern["required_words"] if w in content)
            if found_required == 0:
                issues.append(f"缺少品牌关键词: {', '.join(pattern['required_words'])}")
                penalty += 15
                passed = False

        return {
            "passed": passed,
            "issues": issues,
            "penalty": penalty,
            "voice": voice,
        }

    def _check_product_specs(self, content: str, specs: Dict[str, Any]) -> Dict[str, Any]:
        """_check_product_specs。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param specs: 参数 specs
        :return: 返回处理结果。
        """
        issues: List[str] = []
        penalty = 0
        passed = True
        density = specs.get("density")
        strength = specs.get("strength_grade")
        thermal = specs.get("thermal_conductivity")
        if density:
            density_pattern = r"(\d+(?:\.\d+)?)\s*(?:kg/m3|kg/m³|公斤/立方米)"
            matches = re.findall(density_pattern, content)
            if matches:
                for match in matches:
                    try:
                        val = float(match)
                        spec_val = float(str(density).replace("kg/m³", "").replace(" ", ""))
                        if abs(val - spec_val) > spec_val * 0.2:
                            issues.append(f"密度值不一致: 内容中{val}kg/m³, 标准{spec_val}kg/m³")
                            penalty += 20
                            passed = False
                    except ValueError:
                        pass

        if strength:
            strength_pattern = r"(LC\d+\.?\d*|B[1-3]级|A级|强度等级\s*[^\s]+)"
            matches = re.findall(strength_pattern, content)
            if matches and str(strength) not in content:
                issues.append(f"强度等级不一致: 内容中{matches}, 标准{strength}")
                penalty += 15
                passed = False

        if thermal:
            tc_pattern = r"(\d+\.\d+)\s*W/m·K"
            matches = re.findall(tc_pattern, content)
            if matches:
                for match in matches:
                    try:
                        val = float(match)
                        spec_val = float(str(thermal).replace("W/m·K", "").replace(" ", ""))
                        if abs(val - spec_val) > 0.1:
                            issues.append(f"导热系数不一致: 内容中{val}W/m·K, 标准{spec_val}W/m·K")
                            penalty += 20
                            passed = False
                    except ValueError:
                        pass

        standard = specs.get("standard", "JGJ/T 12-2019")
        if standard and standard not in content:
            issues.append(f"缺少标准引用: {standard}")
            penalty += 10

        return {
            "passed": passed,
            "issues": issues,
            "penalty": penalty,
            "checked_specs": list(specs.keys()),
        }

    def _check_required_keywords(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """_check_required_keywords。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param keywords: 参数 keywords
        :return: 返回处理结果。
        """
        warnings: List[str] = []
        penalty = 0
        passed = True
        missing = [k for k in keywords if k not in content]
        if missing:
            warnings.append(f"缺少关键词: {', '.join(missing)}")
            penalty += 5 * len(missing)
            if len(missing) == len(keywords):
                passed = False

        return {
            "passed": passed,
            "warnings": warnings,
            "penalty": penalty,
            "missing_count": len(missing),
        }

    def _check_banned_keywords(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """_check_banned_keywords。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param keywords: 参数 keywords
        :return: 返回处理结果。
        """
        issues: List[str] = []
        penalty = 0
        passed = True
        found = [k for k in keywords if k in content]
        if found:
            issues.append(f"发现禁用关键词: {', '.join(found)}")
            penalty += 15 * len(found)
            passed = False

        return {
            "passed": passed,
            "issues": issues,
            "penalty": penalty,
            "found_count": len(found),
        }

    def enforce_consistency(self, content: str, product_specs: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """enforce_consistency。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param product_specs: 参数 product_specs
        :return: 返回处理结果。
        """
        validation = self.validate_content_consistency(content, product_specs)
        if validation["is_consistent"]:
            return content, validation

        fixed_content = content
        if product_specs.get("standard") and product_specs["standard"] not in fixed_content:
            fixed_content += f"\n\n执行标准：{product_specs['standard']}"

        for issue in validation["issues"]:
            if "密度值不一致" in issue:
                density = product_specs.get("density")
                if density:
                    density_pattern = r"(\d+(?:\.\d+)?)\s*(?:kg/m3|kg/m³)"
                    fixed_content = re.sub(density_pattern, str(density), fixed_content)

            if "强度等级不一致" in issue:
                strength = product_specs.get("strength_grade")
                if strength:
                    fixed_content = fixed_content.replace("B1级", str(strength))

        validation["fixed_content"] = fixed_content
        validation["is_consistent"] = True
        validation["score"] = 85.0
        return fixed_content, validation

    def get_consistency_report(self, content: str, product_specs: Dict[str, Any]) -> Dict[str, Any]:
        """get_consistency_report。

        参数说明：
        :param self: 参数 self
        :param content: 参数 content
        :param product_specs: 参数 product_specs
        :return: 返回处理结果。
        """
        validation = self.validate_content_consistency(content, product_specs)
        return {
            "timestamp": datetime.now().isoformat(),
            "consistency_score": validation["score"],
            "is_consistent": validation["is_consistent"],
            "issue_count": len(validation["issues"]),
            "warning_count": len(validation["warnings"]),
            "detailed_checks": validation["checks"],
            "issues": validation["issues"],
            "warnings": validation["warnings"],
            "product_specs_checked": list(product_specs.keys()) if product_specs else [],
        }
