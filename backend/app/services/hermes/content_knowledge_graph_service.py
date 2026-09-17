# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
内容知识图谱服务 (Content Knowledge Graph)

构建产品、行业、技术参数之间的知识关联网络。
支持：产品分类体系、技术参数关联、行业标准映射、内容推荐。
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set

from datetime import datetime

PRODUCT_CATEGORIES = {
    "轻集料混凝土": {
        "parent": "保温材料",
        "subcategories": ["LC5.0", "LC10", "LC15", "LC20", "LC25", "LC30", "LC35", "LC40", "LC45", "LC50"],
        "standards": ["JGJ/T 12-2019"],
        "related_products": ["EPS聚苯板", "XPS挤塑板", "岩棉板"],
    },
    "EPS聚苯板": {
        "parent": "保温材料",
        "subcategories": ["B1级", "B2级", "阻燃型"],
        "standards": ["GB/T 10801.1-2021"],
        "related_products": ["轻集料混凝土", "XPS挤塑板"],
    },
    "XPS挤塑板": {
        "parent": "保温材料",
        "subcategories": ["B1级", "B2级", "阻燃型", "高强度"],
        "standards": ["GB/T 10801.2-2002"],
        "related_products": ["EPS聚苯板", "轻集料混凝土"],
    },
    "岩棉板": {
        "parent": "保温材料",
        "subcategories": ["A级", "憎水型", "高强度"],
        "standards": ["GB/T 11835-2016"],
        "related_products": ["玻璃棉", "轻集料混凝土"],
    },
    "玻璃棉": {
        "parent": "保温材料",
        "subcategories": ["A级", "憎水型", "超细"],
        "standards": ["GB/T 13350-2017"],
        "related_products": ["岩棉板"],
    },
}

TECHNICAL_PARAMS = {
    "密度": {
        "unit": "kg/m³",
        "ranges": {
            "轻集料混凝土": "800-1950",
            "EPS聚苯板": "15-30",
            "XPS挤塑板": "25-50",
            "岩棉板": "80-200",
        },
    },
    "强度等级": {
        "unit": "",
        "ranges": {
            "轻集料混凝土": "LC5.0-LC50",
            "EPS聚苯板": "B1/B2",
            "XPS挤塑板": "B1/B2",
            "岩棉板": "A级",
        },
    },
    "导热系数": {
        "unit": "W/m·K",
        "ranges": {
            "轻集料混凝土": "0.18-0.28",
            "EPS聚苯板": "0.033-0.039",
            "XPS挤塑板": "0.028-0.032",
            "岩棉板": "0.035-0.044",
        },
    },
    "防火等级": {
        "unit": "",
        "ranges": {
            "轻集料混凝土": "A级",
            "EPS聚苯板": "B1/B2",
            "XPS挤塑板": "B1/B2",
            "岩棉板": "A级",
        },
    },
}

INDUSTRY_STANDARDS = {
    "JGJ/T 12-2019": {
        "name": "轻集料混凝土应用技术标准",
        "products": ["轻集料混凝土"],
        "category": "行业标准",
        "year": 2019,
    },
    "GB/T 10801.1-2021": {
        "name": "绝热用模塑聚苯乙烯泡沫塑料",
        "products": ["EPS聚苯板"],
        "category": "国家标准",
        "year": 2021,
    },
    "GB/T 10801.2-2002": {
        "name": "绝热用挤塑聚苯乙烯泡沫塑料(XPS)",
        "products": ["XPS挤塑板"],
        "category": "国家标准",
        "year": 2002,
    },
    "GB/T 11835-2016": {
        "name": "绝热用岩棉、矿渣棉及其制品",
        "products": ["岩棉板"],
        "category": "国家标准",
        "year": 2016,
    },
    "GB/T 13350-2017": {
        "name": "绝热用玻璃棉及其制品",
        "products": ["玻璃棉"],
        "category": "国家标准",
        "year": 2017,
    },
}


class ContentKnowledgeGraphService:
    def __init__(self):
        """__init__。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        self._graph_cache: Dict[str, Dict[str, Any]] = {}
        self._product_relations: Dict[str, Set[str]] = {}
        self._build_initial_graph()

    def _build_initial_graph(self):
        """_build_initial_graph。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        for product, info in PRODUCT_CATEGORIES.items():
            self._graph_cache[product] = {
                "type": "product",
                "category": info["parent"],
                "subcategories": info["subcategories"],
                "standards": info["standards"],
                "related_products": info["related_products"],
                "technical_params": {},
            }
            for param_name, param_info in TECHNICAL_PARAMS.items():
                if product in param_info["ranges"]:
                    self._graph_cache[product]["technical_params"][param_name] = {
                        "unit": param_info["unit"],
                        "range": param_info["ranges"][product],
                    }

            for related in info["related_products"]:
                if related not in self._product_relations:
                    self._product_relations[related] = set()
                self._product_relations[related].add(product)

    def get_product_info(self, product_name: str) -> Optional[Dict[str, Any]]:
        """get_product_info。

        参数说明：
        :param self: 参数 self
        :param product_name: 参数 product_name
        :return: 返回处理结果。
        """
        return self._graph_cache.get(product_name)

    def get_related_products(self, product_name: str) -> List[str]:
        """get_related_products。

        参数说明：
        :param self: 参数 self
        :param product_name: 参数 product_name
        :return: 返回处理结果。
        """
        info = self._graph_cache.get(product_name)
        if not info:
            return []
        return info.get("related_products", [])

    def get_product_standards(self, product_name: str) -> List[Dict[str, Any]]:
        """get_product_standards。

        参数说明：
        :param self: 参数 self
        :param product_name: 参数 product_name
        :return: 返回处理结果。
        """
        info = self._graph_cache.get(product_name)
        if not info:
            return []
        standards = []
        for standard_code in info.get("standards", []):
            if standard_code in INDUSTRY_STANDARDS:
                standards.append(INDUSTRY_STANDARDS[standard_code])
        return standards

    def get_technical_param_range(self, product_name: str, param_name: str) -> Optional[Dict[str, Any]]:
        """get_technical_param_range。

        参数说明：
        :param self: 参数 self
        :param product_name: 参数 product_name
        :param param_name: 参数 param_name
        :return: 返回处理结果。
        """
        info = self._graph_cache.get(product_name)
        if not info:
            return None
        return info.get("technical_params", {}).get(param_name)

    def search_by_param(self, param_name: str, param_value: str) -> List[Dict[str, Any]]:
        """search_by_param。

        参数说明：
        :param self: 参数 self
        :param param_name: 参数 param_name
        :param param_value: 参数 param_value
        :return: 返回处理结果。
        """
        results = []
        for product_name, info in self._graph_cache.items():
            params = info.get("technical_params", {})
            if param_name in params:
                param_range = params[param_name].get("range", "")
                if param_value in param_range or self._value_in_range(param_value, param_range):
                    results.append({
                        "product_name": product_name,
                        "category": info.get("category"),
                        "param_name": param_name,
                        "param_value": param_value,
                        "param_range": param_range,
                    })
        return results

    def _value_in_range(self, value: str, range_str: str) -> bool:
        """_value_in_range。

        参数说明：
        :param self: 参数 self
        :param value: 参数 value
        :param range_str: 参数 range_str
        :return: 返回处理结果。
        """
        try:
            val = float(value)
            if "-" in range_str:
                parts = range_str.split("-")
                if len(parts) == 2:
                    min_val = float(parts[0])
                    max_val = float(parts[1])
                    return min_val <= val <= max_val
            return False
        except ValueError:
            return False

    def get_category_tree(self) -> Dict[str, Any]:
        """get_category_tree。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        categories: Dict[str, Any] = {}
        for product, info in PRODUCT_CATEGORIES.items():
            parent = info["parent"]
            if parent not in categories:
                categories[parent] = {
                    "name": parent,
                    "products": [],
                    "subcategories": [],
                }
            categories[parent]["products"].append(product)
            for subcat in info["subcategories"]:
                if subcat not in categories[parent]["subcategories"]:
                    categories[parent]["subcategories"].append(subcat)
        return categories

    def recommend_products(self, current_product: str, limit: int = 5) -> List[Dict[str, Any]]:
        """recommend_products。

        参数说明：
        :param self: 参数 self
        :param current_product: 参数 current_product
        :param limit: 参数 limit
        :return: 返回处理结果。
        """
        related = self.get_related_products(current_product)
        recommendations = []
        for product_name in related[:limit]:
            info = self.get_product_info(product_name)
            if info:
                recommendations.append({
                    "product_name": product_name,
                    "category": info.get("category"),
                    "standards": info.get("standards"),
                    "technical_params": info.get("technical_params"),
                    "reason": "相关产品推荐",
                })
        return recommendations

    def build_content_context(self, product_name: str) -> Dict[str, Any]:
        """build_content_context。

        参数说明：
        :param self: 参数 self
        :param product_name: 参数 product_name
        :return: 返回处理结果。
        """
        info = self.get_product_info(product_name)
        if not info:
            return {}

        standards = self.get_product_standards(product_name)
        return {
            "product_name": product_name,
            "category": info.get("category"),
            "subcategories": info.get("subcategories"),
            "technical_params": info.get("technical_params"),
            "standards": standards,
            "related_products": info.get("related_products"),
            "content_tags": self._generate_content_tags(product_name, info),
        }

    def _generate_content_tags(self, product_name: str, info: Dict[str, Any]) -> List[str]:
        """_generate_content_tags。

        参数说明：
        :param self: 参数 self
        :param product_name: 参数 product_name
        :param info: 参数 info
        :return: 返回处理结果。
        """
        tags = [product_name, info.get("category", "")]
        tags.extend(info.get("subcategories", []))
        for std in info.get("standards", []):
            tags.append(std)
        params = info.get("technical_params", {})
        for param_name, param_info in params.items():
            tags.append(f"{param_name}: {param_info.get('range', '')}{param_info.get('unit', '')}")
        return tags

    def validate_technical_params(self, product_name: str, params: Dict[str, str]) -> Dict[str, Any]:
        """validate_technical_params。

        参数说明：
        :param self: 参数 self
        :param product_name: 参数 product_name
        :param params: 参数 params
        :return: 返回处理结果。
        """
        info = self.get_product_info(product_name)
        if not info:
            return {"valid": False, "errors": ["产品不存在"]}

        errors = []
        warnings = []
        valid_params = {}
        for param_name, param_value in params.items():
            expected_range = info.get("technical_params", {}).get(param_name)
            if not expected_range:
                warnings.append(f"未知参数: {param_name}")
                valid_params[param_name] = param_value
                continue

            range_str = expected_range.get("range", "")
            unit = expected_range.get("unit", "")
            if unit and not param_value.endswith(unit):
                warnings.append(f"参数 {param_name} 缺少单位 {unit}")

            try:
                val = float(param_value.replace(unit, "").replace(" ", ""))
                if "-" in range_str:
                    parts = range_str.split("-")
                    if len(parts) == 2:
                        min_val = float(parts[0])
                        max_val = float(parts[1])
                        if val < min_val or val > max_val:
                            errors.append(f"{param_name} 值 {param_value} 超出范围 {range_str}{unit}")
                        else:
                            valid_params[param_name] = param_value
            except ValueError:
                warnings.append(f"参数 {param_name} 值格式不正确: {param_value}")
                valid_params[param_name] = param_value

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "valid_params": valid_params,
            "product_name": product_name,
        }

    def get_graph_summary(self) -> Dict[str, Any]:
        """get_graph_summary。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "total_products": len(self._graph_cache),
            "total_categories": len(set(info["category"] for info in self._graph_cache.values())),
            "total_standards": len(INDUSTRY_STANDARDS),
            "total_params": len(TECHNICAL_PARAMS),
            "product_count_by_category": self._count_by_category(),
            "timestamp": datetime.now().isoformat(),
        }

    def _count_by_category(self) -> Dict[str, int]:
        """_count_by_category。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        counts: Dict[str, int] = {}
        for info in self._graph_cache.values():
            category = info.get("category", "未知")
            counts[category] = counts.get(category, 0) + 1
        return counts

    def export_graph(self) -> str:
        """export_graph。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return json.dumps({
            "products": self._graph_cache,
            "standards": INDUSTRY_STANDARDS,
            "technical_params": TECHNICAL_PARAMS,
            "product_relations": {k: list(v) for k, v in self._product_relations.items()},
        }, ensure_ascii=False, indent=2)
