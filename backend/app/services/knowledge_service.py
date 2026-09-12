"""建材行业知识库 - RAG检索服务

基于向量化检索，让AI能回答建材行业的专业问题。
当前使用Mock实现（关键词匹配+预设答案），后续可接入真实AI引擎。
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class KnowledgeService:
    """知识库检索服务"""
    def __init__(self, knowledge_dir: Optional[str] = None):
        """初始化知识库服务

        Args:
            knowledge_dir: 知识库根目录，默认为项目根下的 knowledge_base/
        """
        if knowledge_dir:
            self.knowledge_dir = knowledge_dir
        else:
            # 自动定位到项目根目录的 knowledge_base/
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.knowledge_dir = os.path.join(base_dir, "knowledge_base")

        # 知识库文件索引（懒加载）
        self._file_index: List[Dict] = []
        self._segments: List[Dict] = []

    def _ensure_indexed(self):
        """确保知识库文件已被索引"""
        if self._segments:
            return

        knowledge_dir = Path(self.knowledge_dir)
        if not knowledge_dir.exists():
            return

        # 遍历所有 .md 文件
        md_files = list(knowledge_dir.rglob("*.md"))
        for file_path in md_files:
            rel_path = str(file_path.relative_to(knowledge_dir))
            category = rel_path.split(os.sep)[0] if os.sep in rel_path else "other"
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            self._file_index.append({
                "path": rel_path,
                "category": category,
                "title": file_path.stem,
                "content": content,
            })
            # 按标题分割为段落（段落级索引）
            paragraphs = self._split_paragraphs(content)
            for i, para in enumerate(paragraphs):
                self._segments.append({
                    "file": rel_path,
                    "category": category,
                    "title": file_path.stem,
                    "paragraph_index": i,
                    "content": para,
                })

    def _split_paragraphs(self, content: str) -> List[str]:
        """将 Markdown 内容按标题分割为段落"""
        # 按 ## 或 ### 标题分割
        parts = re.split(r'(?=^#{2,3}\s)', content, flags=re.MULTILINE)
        result = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 20:  # 过滤过短的片段
                result.append(part)
        return result if result else [content]

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索相关知识（Mock实现：关键词匹配）

        Args:
            query: 搜索关键词
            top_k: 返回结果数量上限

        Returns:
            匹配的知识段落列表，按相关度降序排列
        """
        self._ensure_indexed()
        if not self._segments:
            return []

        # 将查询拆分为关键词
        keywords = self._extract_keywords(query)
        if not keywords:
            return self._segments[:top_k]

        # 为每个段落计算匹配得分
        scored: List[Tuple[float, Dict]] = []
        for seg in self._segments:
            score = self._compute_match_score(seg["content"], keywords)
            # 标题匹配加权
            title_score = self._compute_match_score(seg["title"], keywords)
            score += title_score * 2.0
            if score > 0:
                scored.append((score, seg))

        # 按得分降序排列
        scored.sort(key=lambda x: x[0], reverse=True)
        return [seg for _, seg in scored[:top_k]]

    def _extract_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词"""
        # 去除标点，按空格拆分
        clean = re.sub(r'[，。！？、；：""''【】《》（）?+*.,!;:-]', ' ', query)
        words = clean.split()
        # 过滤过短的词
        return [w for w in words if len(w) >= 2]

    def _compute_match_score(self, text: str, keywords: List[str]) -> float:
        """计算文本与关键词的匹配得分"""
        score = 0.0
        text_lower = text.lower()
        for kw in keywords:
            kw_lower = kw.lower()
            # 精确匹配
            count = text_lower.count(kw_lower)
            if count > 0:
                # 根据关键词长度加权
                score += count * (1.0 + len(kw) * 0.1)
        return score

    def search_multi(
        self,
        queries: List[Dict[str, float]],
        top_k: int = 5,
        strategy: str = "weighted_sum",
    ) -> List[Dict]:
        """多关键词加权搜索

        支持为每个查询关键词分配独立权重，通过加权求和或取最高分的策略合并结果。

        Args:
            queries: 关键词与权重列表，格式 [{"query": "陶粒混凝土", "weight": 1.0}, ...]
            top_k: 返回结果数量上限
            strategy: 合并策略
                - "weighted_sum": 加权求和（默认），适用于综合匹配多个维度
                - "max": 取每个段落各查询中的最高得分，适用于任一关键词匹配即可

        Returns:
            匹配的知识段落列表，按相关度降序排列

        Example:
            >>> service.search_multi([
            ...     {"query": "陶粒混凝土 密度", "weight": 1.5},
            ...     {"query": "强度等级", "weight": 1.0},
            ...     {"query": "配合比", "weight": 1.2},
            ... ])
        """
        self._ensure_indexed()
        if not self._segments:
            return []

        if not queries:
            return self._segments[:top_k]

        # 为每段累积多查询得分
        seg_scores: Dict[int, Dict[str, float]] = {}
        for qi, item in enumerate(queries):
            query_text = item.get("query", "")
            weight = item.get("weight", 1.0)
            keywords = self._extract_keywords(query_text)
            if not keywords:
                continue

            for seg_idx, seg in enumerate(self._segments):
                content_score = self._compute_match_score(seg["content"], keywords)
                title_score = self._compute_match_score(seg["title"], keywords)
                raw = content_score + title_score * 2.0
                weighted = raw * weight
                if seg_idx not in seg_scores:
                    seg_scores[seg_idx] = {"scores": {}, "seg": seg}

                # 按查询索引记录分数
                key = f"q{qi}"
                seg_scores[seg_idx]["scores"][key] = weighted

        # 按策略合并
        scored: List[Tuple[float, Dict]] = []
        for seg_idx, data in seg_scores.items():
            if strategy == "max":
                merged = max(data["scores"].values()) if data["scores"] else 0.0
            else:
                # weighted_sum (default)
                merged = sum(data["scores"].values())

            if merged > 0:
                scored.append((merged, data["seg"]))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [seg for _, seg in scored[:top_k]]

    def search_with_boost(
        self,
        query: str,
        category_boost: Optional[Dict[str, float]] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """带类别加权的搜索

        在标准关键词匹配基础上，允许按知识类别加权。

        Args:
            query: 搜索关键词
            category_boost: 类别加权，如 {"standards": 2.0, "products": 1.5}
            top_k: 返回结果数量上限

        Returns:
            匹配的知识段落列表，按相关度降序排列
        """
        self._ensure_indexed()
        if not self._segments:
            return []

        keywords = self._extract_keywords(query)
        if not keywords:
            return self._segments[:top_k]

        scored: List[Tuple[float, Dict]] = []
        for seg in self._segments:
            score = self._compute_match_score(seg["content"], keywords)
            title_score = self._compute_match_score(seg["title"], keywords)
            score += title_score * 2.0
            # 类别加权
            if category_boost and seg["category"] in category_boost:
                score *= category_boost[seg["category"]]

            if score > 0:
                scored.append((score, seg))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [seg for _, seg in scored[:top_k]]

    def get_categories(self) -> List[Dict]:
        """获取知识分类及统计"""
        self._ensure_indexed()
        # 按类别统计文件数
        category_map: Dict[str, int] = {}
        for file_info in self._file_index:
            cat = file_info["category"]
            category_map[cat] = category_map.get(cat, 0) + 1

        # 中文类别名称映射
        category_names = {
            "standards": "国家标准",
            "product": "产品参数",
            "products": "产品参数",
            "construction": "施工规范",
            "policy": "政策法规",
            "market_intelligence": "市场情报",
            "buyer_personas": "买家画像",
            "geo_seo_knowledge": "GEO/SEO 知识",
            "building_materials": "建材产品知识",
        }
        result = []
        for cat_id, count in category_map.items():
            result.append({
                "id": cat_id,
                "name": category_names.get(cat_id, cat_id),
                "count": count,
            })
        return result

    def get_knowledge_base_info(self) -> Dict:
        """获取知识库概览信息"""
        self._ensure_indexed()
        return {
            "total_files": len(self._file_index),
            "total_segments": len(self._segments),
            "categories": self.get_categories(),
            "files": [
                {"path": f["path"], "title": f["title"], "category": f["category"]}
                for f in self._file_index
            ],
        }

    # ========== 预设问答（Mock实现） ==========
    _PRESET_QA: Dict[str, Dict] = {
        # ========== 建材产品知识 ==========
        "陶粒混凝土密度": {
            "answer": (
                "根据GB/T 17431.1-2010标准，陶粒混凝土的干表观密度范围为800～1600 kg/m³。"
                "具体分为多个密度等级：800级（760～850 kg/m³）、1000级（960～1050 kg/m³）、"
                "1200级（1160～1250 kg/m³）、1400级（1360～1450 kg/m³）、"
                "1600级（1560～1650 kg/m³）。\n\n"
                "陶粒混凝土的密度主要受陶粒种类、级配和配合比影响。"
                "高强陶粒混凝土通常密度较高（1400 kg/m³以上），而保温型陶粒混凝土密度较低（800～1000 kg/m³）。"
            ),
            "sources": [
                {"file": "standards/轻集料混凝土.md", "title": "轻集料混凝土国标规范"},
                {"file": "products/陶粒混凝土.md", "title": "陶粒混凝土产品参数"},
            ],
        },
        "陶粒混凝土强度": {
            "answer": (
                "陶粒混凝土的强度等级以LC表示，范围为LC5.0至LC40。结构用陶粒混凝土强度等级不应低于LC15。\n\n"
                "常用等级对应用途：\n"
                "- LC5.0～LC10：保温填充，非承重构件\n"
                "- LC15～LC20：结构保温，围护结构\n"
                "- LC20～LC40：承重结构，梁板柱\n\n"
                "陶粒本身的筒压强度是影响混凝土强度的关键因素。"
                "普通陶粒筒压强度≥1.0 MPa，高强陶粒≥4.0 MPa。"
            ),
            "sources": [
                {"file": "standards/轻集料混凝土.md", "title": "轻集料混凝土国标规范"},
                {"file": "products/陶粒混凝土.md", "title": "陶粒混凝土产品参数"},
            ],
        },
        "保温材料燃烧等级": {
            "answer": (
                "根据GB 8624-2012《建筑材料及制品燃烧性能分级》，保温材料的燃烧性能分为四个等级：\n\n"
                "1. **A级（不燃材料）**：岩棉、泡沫玻璃、无机保温砂浆等\n"
                "2. **B1级（难燃材料）**：阻燃EPS、阻燃XPS、阻燃聚氨酯等\n"
                "3. **B2级（可燃材料）**：普通EPS、普通XPS\n"
                "4. **B3级（易燃材料）**：未阻燃的有机保温材料\n\n"
                "工程选用原则：\n"
                "- 民用建筑外墙保温应选用A级或B1级\n"
                "- 高度＞100m住宅及＞50m公建，必须使用A级\n"
                "- 岩棉是防火要求高时的首选材料"
            ),
            "sources": [
                {"file": "standards/保温材料.md", "title": "保温材料标准"},
            ],
        },
        "保温砂浆施工": {
            "answer": (
                "保温砂浆施工工艺要点如下：\n\n"
                "**施工条件**：环境温度5℃～35℃，风力≤5级，禁止雨天施工。\n\n"
                "**施工流程**：基层处理 → 吊垂线弹控制线 → 做灰饼 → 界面处理 → 分层抹保温砂浆 → 压入网格布 → 抹面层砂浆 → 养护 → 质量验收\n\n"
                "**分层施工**：每遍抹灰厚度不宜超过20mm，间隔时间≥24h，总厚度不宜超过50mm。\n\n"
                "**网格布铺设**：耐碱玻纤网格布搭接宽度不小于100mm，阴阳角应增设附加网格布。\n\n"
                "**养护**：施工后24h内避免水冲，自然养护7天。"
            ),
            "sources": [
                {"file": "construction/施工工艺.md", "title": "施工工艺指南"},
                {"file": "products/保温砂浆.md", "title": "保温砂浆产品参数"},
            ],
        },
        "保温砂浆导热系数": {
            "answer": (
                "根据GB/T 20473-2021标准：\n"
                "- 玻化微珠保温砂浆导热系数 ≤ 0.070 W/(m·K)\n"
                "- 膨胀珍珠岩保温砂浆导热系数 ≤ 0.085 W/(m·K)\n\n"
                "保温砂浆的燃烧性能等级均为A级（不燃材料），安全性优异。"
            ),
            "sources": [
                {"file": "products/保温砂浆.md", "title": "保温砂浆产品参数"},
            ],
        },
        "轻集料混凝土配合比": {
            "answer": (
                "轻集料混凝土的配合比设计应满足强度、密度、和易性和耐久性要求。主要设计步骤：\n\n"
                "1. 确定配制强度\n"
                "2. 选择水泥品种和强度等级\n"
                "3. 确定水灰比\n"
                "4. 选定单位用水量\n"
                "5. 计算水泥用量\n"
                "6. 选择砂率\n"
                "7. 计算粗细集料用量\n"
                "8. 确定密度并进行试配调整\n\n"
                "以C25等级参考配合比为例：水泥（P.O42.5）380～420 kg/m³，水160～180 kg/m³，"
                "陶粒（5~20mm）500～600 kg/m³，中砂550～650 kg/m³。"
            ),
            "sources": [
                {"file": "standards/轻集料混凝土.md", "title": "轻集料混凝土国标规范"},
            ],
        },
        # ========== 外贸业务知识 ==========
        "出口印尼建材": {
            "answer": (
                "印尼是东南亚最大建材市场，主要需求集中在：\n\n"
                "**认证要求**：SNI（印尼国家标准）强制认证，特别是钢材、水泥、防水材料。\n"
                "**热门品类**：钢结构件、陶瓷砖、防水涂料、保温材料、五金配件。\n"
                "**主要港口**：雅加达丹戎不碌港、泗水丹戎佩拉港。\n"
                "**支付方式**：L/C（大额）、T/T（中小额，30% 预付 + 70% 见提单副本）。\n"
                "**关税参考**：水泥 15-20%、钢材 0-15%、陶瓷 15-25%。\n\n"
                "**市场特点**：基建投资持续增长，中国品牌价格优势明显，但需注意当地代理渠道。"
            ),
            "sources": [
                {"file": "market_intelligence.md", "title": "市场情报"},
                {"file": "building_materials.md", "title": "建材产品知识"},
            ],
        },
        "出口沙特建材": {
            "answer": (
                "沙特 Vision 2030 带动万亿基建投资，建材需求旺盛：\n\n"
                "**认证要求**：SASO 认证（沙特标准局），出口前需获得 Product Conformity Certificate。\n"
                "**热门品类**：保温材料（岩棉/XPS）、钢结构、幕墙、管材管件、电线电缆。\n"
                "**主要港口**：吉达港、达曼港、延布工业港。\n"
                "**支付方式**：L/C 为主，部分接受 T/T。\n"
                "**特殊要求**：清真认证不适用于建材，但需注意伊斯兰历节假日影响交期。\n\n"
                "**市场特点**：NEOM 等超级项目带动高端建材需求，中国产品性价比受认可。"
            ),
            "sources": [
                {"file": "market_intelligence.md", "title": "市场情报"},
            ],
        },
        "GEO优化策略": {
            "answer": (
                "GEO（Generative Engine Optimization）是针对 AI 搜索引擎的内容优化：\n\n"
                "**目标 AI 搜索引擎**：DeepSeek、ChatGPT Search、Perplexity、Google AI Overview、百度AI。\n\n"
                "**核心策略**（基于 Princeton KDD 2024 + arXiv 2026 最新论文）：\n"
                "1. **FAQ 吸收**：结构化 FAQ 问答对，AI 更容易引用\n"
                "2. **品牌锚定**：在行业内容中自然嵌入品牌名\n"
                "3. **统计引用**：包含具体数字和数据来源\n"
                "4. **权威引用**：引用标准号、论文、官方数据\n"
                "5. **Schema.org 标记**：Product + FAQPage JSON-LD\n"
                "6. **双语内容**：中英文同步发布，覆盖更多 AI 搜索\n\n"
                "**评分维度**：可读性、权威性、FAQ 吸收率、品牌锚定率、Schema 覆盖度。"
            ),
            "sources": [
                {"file": "geo_seo_knowledge.md", "title": "GEO/SEO 知识"},
            ],
        },
        "买家画像分析": {
            "answer": (
                "建材出口主要买家类型：\n\n"
                "1. **大型开发商采购总监** — 关注质量认证 > 交期 > 价格，订单集装箱级，周期 3-6 月\n"
                "2. **建材超市采购经理** — 关注品类齐全 > 价格 > 包装，混装柜，周期 1-3 月\n"
                "3. **承包商/工程公司** — 关注交期 > 价格 > 技术参数，项目制，周期 1-4 周\n"
                "4. **贸易商/进口商** — 关注利润率 > MOQ > 认证，持续采购，多柜/月\n\n"
                "**决策链路**：技术评估 → 样品确认 → 商务谈判 → 合同签订 → 验货出货。\n"
                "**沟通渠道**：展会面谈（信任建立）→ 邮件/WhatsApp（日常沟通）→ 视频验厂（下单前）。"
            ),
            "sources": [
                {"file": "buyer_personas.md", "title": "买家画像库"},
            ],
        },
    }
    def ask(self, question: str) -> Dict:
        """基于知识库回答问题

        当前使用Mock实现（预设问答+关键词匹配），
        AI引擎模式留接口后续接入。

        Args:
            question: 用户问题

        Returns:
            包含 answer 和 sources 的响应
        """
        # 第一步：尝试精确匹配预设问答
        for key, qa in self._PRESET_QA.items():
            if key in question:
                # 同步搜索相关知识段落作为补充来源
                related = self.search(question, top_k=3)
                extra_sources = [
                    {"file": s["file"], "title": s["title"]}
                    for s in related
                    if s["file"] not in [src["file"] for src in qa["sources"]]
                ]
                return {
                    "answer": qa["answer"],
                    "sources": qa["sources"] + extra_sources[:2],
                }

        # 第二步：关键词匹配搜索
        related = self.search(question, top_k=5)
        if not related:
            return {
                "answer": "抱歉，知识库中暂未找到与您问题相关的信息。请尝试换一种问法，或浏览知识库分类查找。",
                "sources": [],
            }

        # 拼接搜索结果生成回答
        context = "\n\n".join([r["content"][:300] for r in related[:3]])
        answer = (
            f"根据知识库中的相关内容，为您找到以下信息：\n\n"
            f"{context}\n\n"
            f"以上信息来自知识库中的相关文档，建议您查阅完整文件获取更详细的内容。"
        )
        sources = [
            {"file": s["file"], "title": s["title"]}
            for s in related[:5]
        ]
        return {
            "answer": answer,
            "sources": sources,
        }
