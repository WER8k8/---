# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
统一 Prompt 构建管理服务 (Prompt Harness)

统一管理各服务的 Prompt 模板，支持模板版本管理、动态参数注入、Prompt 优化。
解决当前 Prompt 分散在各服务独立管理的问题。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from datetime import datetime

PROMPT_TEMPLATES = {
    "product_description": {
        "version": "1.0.0",
        "category": "content_generation",
        "description": "产品描述生成",
        "template": """你是一位专业的建材产品文案专家。请根据以下信息生成专业、吸引人的产品描述。

【产品信息】
产品名称：{product_name}
产品分类：{category}
干密度：{density}
强度等级：{strength_grade}
导热系数：{thermal_conductivity}
防火等级：{fire_rating}

【要求】
1. 使用专业术语，符合B2B采购场景
2. 包含产品核心优势和应用场景
3. 引用执行标准 {standard}
4. 控制在300-500字
5. 语言风格：专业、可信、简洁

【输出格式】
请直接输出产品描述内容，不要包含其他说明。
""",
        "required_params": ["product_name", "category"],
        "optional_params": ["density", "strength_grade", "thermal_conductivity", "fire_rating", "standard"],
    },
    "seo_title": {
        "version": "1.0.0",
        "category": "seo",
        "description": "SEO标题生成",
        "template": """你是一位专业的SEO优化专家。请根据以下信息生成优化的Meta标题。

【产品信息】
产品名称：{product_name}
产品分类：{category}
核心关键词：{keywords}

【要求】
1. 长度控制在15-30字（中文）
2. 包含核心关键词
3. 符合搜索引擎优化规则
4. 吸引用户点击

【输出格式】
请直接输出标题内容，不要包含其他说明。
""",
        "required_params": ["product_name"],
        "optional_params": ["category", "keywords"],
    },
    "seo_description": {
        "version": "1.0.0",
        "category": "seo",
        "description": "SEO描述生成",
        "template": """你是一位专业的SEO优化专家。请根据以下信息生成优化的Meta描述。

【产品信息】
产品名称：{product_name}
产品分类：{category}
核心关键词：{keywords}

【要求】
1. 长度控制在50-120字（中文）
2. 包含核心关键词
3. 突出产品优势和卖点
4. 吸引用户点击
5. 符合搜索引擎优化规则

【输出格式】
请直接输出描述内容，不要包含其他说明。
""",
        "required_params": ["product_name"],
        "optional_params": ["category", "keywords"],
    },
    "content_polish": {
        "version": "1.0.0",
        "category": "content_optimization",
        "description": "内容润色",
        "template": """你是一位专业的文字编辑和内容优化专家。请根据以下要求润色内容。

【原始内容】
{content}

【润色类型】
{polish_type}

【要求】
1. 保持原意不变
2. 提升语言表达质量
3. 去除冗余内容
4. 增强专业性和可读性

【输出格式】
请直接输出润色后的内容，不要包含其他说明。
""",
        "required_params": ["content", "polish_type"],
        "optional_params": [],
    },
    "market_research": {
        "version": "1.0.0",
        "category": "research",
        "description": "市场研究分析",
        "template": """你是一位专业的市场研究分析师。请根据以下信息进行市场分析。

【研究主题】
{topic}

【目标市场】
{target_market}

【竞争环境】
{competitors}

【要求】
1. 分析市场趋势和发展方向
2. 评估竞争态势
3. 识别机会和挑战
4. 提供战略建议
5. 输出详细的分析报告

【输出格式】
请直接输出分析报告内容，不要包含其他说明。
""",
        "required_params": ["topic"],
        "optional_params": ["target_market", "competitors"],
    },
    "seo_analysis": {
        "version": "1.0.0",
        "category": "seo",
        "description": "SEO健康度分析",
        "template": """你是一位专业的SEO分析师。请分析以下网页的SEO健康状况。

【网页信息】
URL: {url}
内容摘要：{content}

【分析维度】
1. 关键词密度
2. 标题优化建议
3. Meta描述分析
4. 内容结构建议
5. 技术SEO问题
6. 改进建议

【要求】
1. 提供详细的分析报告
2. 给出具体的改进建议
3. 评估SEO健康分数

【输出格式】
请直接输出分析报告内容，不要包含其他说明。
""",
        "required_params": ["url"],
        "optional_params": ["content"],
    },
    "code_generation": {
        "version": "1.0.0",
        "category": "development",
        "description": "代码生成",
        "template": """你是一位专业的软件工程师。请根据以下需求生成高质量代码。

【需求描述】
{requirements}

【编程语言】
{language}

【要求】
1. 代码完整可运行
2. 包含适当注释
3. 遵循最佳实践
4. 考虑错误处理和边界情况

【输出格式】
请直接输出代码，不要包含其他说明。
""",
        "required_params": ["requirements"],
        "optional_params": ["language"],
    },
}


class PromptHarnessService:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._templates = PROMPT_TEMPLATES
        self._template_history: Dict[str, List[Dict[str, Any]]] = {}
        self._usage_stats: Dict[str, int] = {}

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """get_template。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :return: 返回处理结果。
        """
        return self._templates.get(template_id)

    def list_templates(self) -> List[Dict[str, Any]]:
        """list_templates。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        templates = []
        for template_id, template in self._templates.items():
            templates.append({
                "template_id": template_id,
                "version": template.get("version"),
                "category": template.get("category"),
                "description": template.get("description"),
                "required_params": template.get("required_params", []),
                "optional_params": template.get("optional_params", []),
            })
        return templates

    def build_prompt(self, template_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """build_prompt。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :param params: 参数 params
        :return: 返回处理结果。
        """
        template = self._templates.get(template_id)
        if not template:
            return {
                "success": False,
                "error": f"模板不存在: {template_id}",
            }

        required_params = template.get("required_params", [])
        missing_params = [p for p in required_params if p not in params]
        if missing_params:
            return {
                "success": False,
                "error": f"缺少必需参数: {', '.join(missing_params)}",
            }

        try:
            prompt = template["template"].format(**params)
        except KeyError as e:
            return {
                "success": False,
                "error": f"参数缺失: {e}",
            }

        self._record_usage(template_id)
        return {
            "success": True,
            "prompt": prompt,
            "template_id": template_id,
            "version": template.get("version"),
            "params_used": {k: v for k, v in params.items() if k in required_params + template.get("optional_params", [])},
        }

    def validate_params(self, template_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """validate_params。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :param params: 参数 params
        :return: 返回处理结果。
        """
        template = self._templates.get(template_id)
        if not template:
            return {"valid": False, "errors": [f"模板不存在: {template_id}"]}

        required_params = template.get("required_params", [])
        optional_params = template.get("optional_params", [])
        errors = []
        warnings = []
        for param in required_params:
            if param not in params:
                errors.append(f"缺少必需参数: {param}")

        for param in params:
            if param not in required_params and param not in optional_params:
                warnings.append(f"多余参数: {param}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "required_params": required_params,
            "optional_params": optional_params,
        }

    def create_template(self, template_id: str, template: Dict[str, Any]) -> Dict[str, Any]:
        """create_template。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :param template: 参数 template
        :return: 返回处理结果。
        """
        if template_id in self._templates:
            return {"success": False, "error": "模板已存在"}

        if "template" not in template:
            return {"success": False, "error": "缺少模板内容"}

        self._templates[template_id] = {
            "version": template.get("version", "1.0.0"),
            "category": template.get("category", "general"),
            "description": template.get("description", ""),
            "template": template["template"],
            "required_params": template.get("required_params", []),
            "optional_params": template.get("optional_params", []),
            "created_at": datetime.now().isoformat(),
        }
        return {"success": True, "template_id": template_id}

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """update_template。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :param updates: 参数 updates
        :return: 返回处理结果。
        """
        if template_id not in self._templates:
            return {"success": False, "error": "模板不存在"}

        template = self._templates[template_id]
        old_version = template.get("version", "1.0.0")
        if "template" in updates:
            template["template"] = updates["template"]

        if "category" in updates:
            template["category"] = updates["category"]

        if "description" in updates:
            template["description"] = updates["description"]

        if "required_params" in updates:
            template["required_params"] = updates["required_params"]

        if "optional_params" in updates:
            template["optional_params"] = updates["optional_params"]

        template["version"] = self._bump_version(old_version)
        template["updated_at"] = datetime.now().isoformat()
        if template_id not in self._template_history:
            self._template_history[template_id] = []
        self._template_history[template_id].append({
            "version": old_version,
            "updated_at": datetime.now().isoformat(),
        })
        return {"success": True, "template_id": template_id, "old_version": old_version, "new_version": template["version"]}

    def _bump_version(self, version: str) -> str:
        """_bump_version。

        参数说明：
        :param self: 参数 self
        :param version: 参数 version
        :return: 返回处理结果。
        """
        parts = version.split(".")
        if len(parts) == 3:
            try:
                major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
                patch += 1
                return f"{major}.{minor}.{patch}"
            except ValueError:
                return f"{version}.1"
        return f"{version}.1"

    def delete_template(self, template_id: str) -> Dict[str, Any]:
        """delete_template。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :return: 返回处理结果。
        """
        if template_id not in self._templates:
            return {"success": False, "error": "模板不存在"}

        del self._templates[template_id]
        return {"success": True, "template_id": template_id}

    def _record_usage(self, template_id: str):
        """_record_usage。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :return: 返回处理结果。
        """
        self._usage_stats[template_id] = self._usage_stats.get(template_id, 0) + 1

    def get_usage_stats(self) -> Dict[str, Any]:
        """get_usage_stats。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "total_usage": sum(self._usage_stats.values()),
            "templates_used": len(self._usage_stats),
            "top_templates": sorted(self._usage_stats.items(), key=lambda x: x[1], reverse=True)[:5],
            "timestamp": datetime.now().isoformat(),
        }

    def get_template_history(self, template_id: str) -> List[Dict[str, Any]]:
        """get_template_history。

        参数说明：
        :param self: 参数 self
        :param template_id: 参数 template_id
        :return: 返回处理结果。
        """
        return self._template_history.get(template_id, [])

    def export_templates(self) -> str:
        """export_templates。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return json.dumps(self._templates, ensure_ascii=False, indent=2)

    def import_templates(self, templates_json: str) -> Dict[str, Any]:
        """import_templates。

        参数说明：
        :param self: 参数 self
        :param templates_json: 参数 templates_json
        :return: 返回处理结果。
        """
        try:
            templates = json.loads(templates_json)
        except json.JSONDecodeError:
            return {"success": False, "error": "JSON格式错误"}

        imported_count = 0
        updated_count = 0
        for template_id, template in templates.items():
            if "template" not in template:
                continue

            if template_id in self._templates:
                self._templates[template_id] = template
                updated_count += 1
            else:
                self._templates[template_id] = template
                imported_count += 1

        return {"success": True, "imported": imported_count, "updated": updated_count}

    def search_templates(self, keyword: str) -> List[Dict[str, Any]]:
        """search_templates。

        参数说明：
        :param self: 参数 self
        :param keyword: 参数 keyword
        :return: 返回处理结果。
        """
        results = []
        for template_id, template in self._templates.items():
            if (keyword.lower() in template_id.lower() or
                keyword.lower() in template.get("description", "").lower() or
                keyword.lower() in template.get("category", "").lower()):
                results.append({
                    "template_id": template_id,
                    "version": template.get("version"),
                    "category": template.get("category"),
                    "description": template.get("description"),
                })
        return results
