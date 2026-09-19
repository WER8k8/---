# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""
谷歌 B2B 全球高阶 Dorking 语法生成器与商机雷达 (Google B2B Dorking Engine)。

利用谷歌搜索引擎的顶级高级运算符 (Search Operators)，穿透公开互联网挖掘隐藏的采购商：
1. LinkedIn 企业与采购决策人穿透 (`site:linkedin.com/in OR site:linkedin.com/company`)
2. 海关关单与提单公开索引穿透 (`filetype:pdf "bill of lading" OR "commercial invoice"`)
3. 全球 B2B 批发商与建材分销商穿透 (`inurl:contact OR inurl:about "distributor"`)
4. 政府与商业项目招标书穿透 (`"request for proposal" OR "tender" "building materials"`)
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List


class GoogleB2BDorkingEngine:
    """谷歌全球外贸 Dorking 矩阵生成器。"""

    @staticmethod
    def generate_dork_matrix(keyword: str, country: str = "Global") -> dict[str, Any]:
        """为特定建材品类和目标国家生成 4 维高精准谷歌穿透搜索向量。"""
        kw = keyword.strip()
        cntry = country.strip() if country and country.lower() != "global" else ""
        c_filter = f'("{cntry}")' if cntry else ""

        dorks = [
            {
                "id": "dork_linkedin_buyers",
                "category": "LinkedIn 决策人穿透",
                "purpose": "直接定位目标国家企业采购经理、供应链总监与创始人",
                "query": f'site:linkedin.com/in ("purchasing manager" OR "procurement manager" OR "buyer" OR "import manager") "{kw}" {c_filter}'.strip(),
            },
            {
                "id": "dork_importer_websites",
                "category": "独立建材进口商/批发商穿透",
                "purpose": "跳过中介黄页，直挖拥有独立官网的海外一级分销商与批发商",
                "query": f'("{kw}") ("importer" OR "distributor" OR "wholesaler") ("contact us" OR "about us") -directory -b2bplatform {c_filter}'.strip(),
            },
            {
                "id": "dork_customs_manifests",
                "category": "公开提单与海关单证穿透",
                "purpose": "检索搜索引擎已公开索引的真实清关提单 (B/L) 与出运记录",
                "query": f'filetype:pdf ("bill of lading" OR "commercial invoice" OR "packing list") "{kw}" {c_filter}'.strip(),
            },
            {
                "id": "dork_project_tenders",
                "category": "海外建筑工程与采购招标穿透",
                "purpose": "捕获正在进行中的大型商业地产、住宅与基建材料招标书 (RFP/Tender)",
                "query": f'("tender" OR "RFP" OR "request for quotation") "{kw}" ("contractor" OR "architectural") {c_filter}'.strip(),
            },
        ]

        # 转换为带直接可点击直达谷歌搜索的 URL
        for d in dorks:
            encoded = urllib.parse.quote_plus(d["query"])
            d["google_search_url"] = f"https://www.google.com/search?q={encoded}"

        return {
            "keyword": kw,
            "target_country": country or "Global",
            "dork_count": len(dorks),
            "dorks": dorks,
            "operator_guidance": "将生成的 Google Dork 语法直接贴入 Google 搜索框，或由后台 Browser Runtime 自动抓取并清洗去重入库。",
        }
