# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""知识库自动沉淀服务

将调研结果、GEO 探测数据、竞品分析自动沉淀到 knowledge_base/，
供 KnowledgeService 做 RAG 检索。
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


class KnowledgeIngestionService:
    """知识库自动沉淀服务"""
    # 知识库根目录
    _BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "knowledge_base"
    # 分类目录映射
    _CATEGORY_DIRS = {
        "market": "market_intelligence",
        "buyer": "buyer_personas",
        "product": "products",
        "geo": "geo_seo_knowledge",
        "competitor": "competitors",
        "compliance": "compliance",
        "supply_chain": "supply_chain",
        "email_template": "email_templates",
        "research_report": "research_reports",
    }
    def __init__(self, base_dir: Optional[str] = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param base_dir: 参数 base_dir
        :return: 返回处理结果。
        """
        if base_dir:
            self._BASE_DIR = Path(base_dir)

    def ingest_market_report(
        self,
        country: str,
        content: str,
        source: str = "foreign-trade-research",
        metadata: Optional[Dict] = None,
    ) -> str:
        """沉淀市场调研报告

        Args:
            country: 目标国家
            content: Markdown 格式的调研内容
            source: 来源（foreign-trade-research / deerflow / manual）
            metadata: 附加元数据

        Returns:
            保存的文件路径
        """
        dir_path = self._BASE_DIR / "market_intelligence"
        dir_path.mkdir(parents=True, exist_ok=True)
        filename = f"{country}_{datetime.now().strftime('%Y%m%d')}.md"
        file_path = dir_path / filename
        header = f"""# {country} 建材市场调研

> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
> 来源: {source}
> 数据时效: 调研日期当日有效，请结合最新政策使用

---

"""
        file_path.write_text(header + content, encoding="utf-8")
        return str(file_path)

    def ingest_buyer_persona(
        self,
        persona_name: str,
        content: str,
        target_country: str = "",
        source: str = "foreign-trade-research",
    ) -> str:
        """沉淀买家画像

        Args:
            persona_name: 画像名称（如 "沙特开发商采购总监"）
            content: Markdown 格式的画像内容
            target_country: 目标国家
            source: 来源

        Returns:
            保存的文件路径
        """
        dir_path = self._BASE_DIR / "buyer_personas"
        dir_path.mkdir(parents=True, exist_ok=True)
        safe_name = persona_name.replace("/", "_").replace("\\", "_")
        filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d')}.md"
        file_path = dir_path / filename
        header = f"""# 买家画像: {persona_name}

> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
> 目标市场: {target_country}
> 来源: {source}

---

"""
        file_path.write_text(header + content, encoding="utf-8")
        return str(file_path)

    def ingest_competitor_analysis(
        self,
        competitor_name: str,
        content: str,
        platform: str = "",
        source: str = "foreign-trade-research",
    ) -> str:
        """沉淀竞品分析

        Args:
            competitor_name: 竞品名称
            content: Markdown 格式的分析内容
            platform: 平台（alibaba / made-in-china / globalsources）
            source: 来源

        Returns:
            保存的文件路径
        """
        dir_path = self._BASE_DIR / "competitors"
        dir_path.mkdir(parents=True, exist_ok=True)
        safe_name = competitor_name.replace("/", "_").replace("\\", "_")
        filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d')}.md"
        file_path = dir_path / filename
        header = f"""# 竞品分析: {competitor_name}

> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
> 平台: {platform or '综合'}
> 来源: {source}

---

"""
        file_path.write_text(header + content, encoding="utf-8")
        return str(file_path)

    def ingest_geo_strategy(
        self,
        product_name: str,
        content: str,
        ai_engines: Optional[List[str]] = None,
        source: str = "geo_writing_policy",
    ) -> str:
        """沉淀 GEO 优化策略

        Args:
            product_name: 产品名称
            content: Markdown 格式的策略内容
            ai_engines: 目标 AI 搜索引擎列表
            source: 来源

        Returns:
            保存的文件路径
        """
        dir_path = self._BASE_DIR / "geo_strategies"
        dir_path.mkdir(parents=True, exist_ok=True)
        safe_name = product_name.replace("/", "_").replace("\\", "_")
        filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d')}.md"
        file_path = dir_path / filename
        engines = ", ".join(ai_engines or ["DeepSeek", "ChatGPT", "Gemini", "Perplexity"])
        header = f"""# GEO 策略: {product_name}

> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
> 目标 AI 引擎: {engines}
> 来源: {source}

---

"""
        file_path.write_text(header + content, encoding="utf-8")
        return str(file_path)

    def ingest_email_template(
        self,
        template_name: str,
        content: str,
        language: str = "en",
        scenario: str = "cold_outreach",
    ) -> str:
        """沉淀邮件模板

        Args:
            template_name: 模板名称
            content: 邮件内容（Markdown 格式）
            language: 语言（en / zh / both）
            scenario: 场景（cold_outreach / follow_up / sample_confirm / holiday）

        Returns:
            保存的文件路径
        """
        dir_path = self._BASE_DIR / "email_templates"
        dir_path.mkdir(parents=True, exist_ok=True)
        safe_name = template_name.replace("/", "_").replace("\\", "_")
        filename = f"{safe_name}_{language}_{datetime.now().strftime('%Y%m%d')}.md"
        file_path = dir_path / filename
        scenario_names = {
            "cold_outreach": "冷启动触达",
            "follow_up": "跟进催促",
            "sample_confirm": "样品确认",
            "holiday": "节日问候",
            "quote_follow": "报价跟进",
        }
        header = f"""# 邮件模板: {template_name}

> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
> 语言: {language}
> 场景: {scenario_names.get(scenario, scenario)}

---

"""
        file_path.write_text(header + content, encoding="utf-8")
        return str(file_path)

    def ingest_compliance_info(
        self,
        country: str,
        product: str,
        content: str,
        source: str = "foreign-trade-research",
    ) -> str:
        """沉淀合规认证信息

        Args:
            country: 目标国家
            product: 产品名称
            content: Markdown 格式的合规信息
            source: 来源

        Returns:
            保存的文件路径
        """
        dir_path = self._BASE_DIR / "compliance"
        dir_path.mkdir(parents=True, exist_ok=True)
        filename = f"{country}_{product}_{datetime.now().strftime('%Y%m%d')}.md"
        file_path = dir_path / filename
        header = f"""# 合规认证: {product} 出口 {country}

> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
> 来源: {source}
> 重要提示: 认证要求可能随时更新，请以官方最新发布为准

---

"""
        file_path.write_text(header + content, encoding="utf-8")
        return str(file_path)

    def ingest_research_report(
        self,
        title: str,
        content: str,
        report_type: str = "general",
        source: str = "deerflow",
    ) -> str:
        """沉淀通用调研报告

        Args:
            title: 报告标题
            content: Markdown 格式的报告内容
            report_type: 报告类型（market / competitor / supply_chain / geo / general）
            source: 来源

        Returns:
            保存的文件路径
        """
        dir_path = self._BASE_DIR / "research_reports" / report_type
        dir_path.mkdir(parents=True, exist_ok=True)
        safe_title = title.replace("/", "_").replace("\\", "_")[:80]
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d%H%M')}.md"
        file_path = dir_path / filename
        header = f"""# {title}

> 生成时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
> 报告类型: {report_type}
> 来源: {source}

---

"""
        file_path.write_text(header + content, encoding="utf-8")
        return str(file_path)

    def list_knowledge_files(self, category: Optional[str] = None) -> List[Dict]:
        """列出知识库文件

        Args:
            category: 可选分类过滤

        Returns:
            文件信息列表
        """
        if category and category in self._CATEGORY_DIRS:
            search_dir = self._BASE_DIR / self._CATEGORY_DIRS[category]
        else:
            search_dir = self._BASE_DIR

        if not search_dir.exists():
            return []

        results = []
        for f in sorted(search_dir.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
            rel = f.relative_to(self._BASE_DIR)
            results.append({
                "path": str(rel),
                "name": f.stem,
                "size_bytes": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
                "category": str(rel.parts[0]) if len(rel.parts) > 1 else "root",
            })

        return results

    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        if not self._BASE_DIR.exists():
            return {"total_files": 0, "categories": {}}

        categories = {}
        total = 0
        for cat_name, cat_dir in self._CATEGORY_DIRS.items():
            dir_path = self._BASE_DIR / cat_dir
            if dir_path.exists():
                count = len(list(dir_path.rglob("*.md")))
                categories[cat_name] = count
                total += count

        # 统计根目录文件
        root_files = len([f for f in self._BASE_DIR.glob("*.md")])
        total += root_files
        return {
            "total_files": total,
            "root_files": root_files,
            "categories": categories,
            "base_dir": str(self._BASE_DIR),
        }
