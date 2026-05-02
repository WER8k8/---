import json
import re
import time
from ipaddress import ip_address, ip_network
from typing import Optional
from urllib.parse import urlparse


PRIVATE_NETWORKS = [
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("::1/128"),
    ip_network("fc00::/7"),
]

BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]", "metadata.google.internal"}


def validate_url_safety(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("仅支持 http/https 协议的URL")
    hostname = parsed.hostname.lower()
    if hostname in BLOCKED_HOSTS:
        raise ValueError("不允许审计内部地址")
    try:
        ip = ip_address(hostname)
        for net in PRIVATE_NETWORKS:
            if ip in net:
                raise ValueError("不允许审计内网地址")
    except ValueError:
        if re.search(r'(10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|127\.)', hostname):
            raise ValueError("不允许审计内网地址")
    return url


AUDIT_DIMENSIONS = [
    {"id": "technical_compliance", "name": "技术合规", "check_count": 8},
    {"id": "ai_search_optimization", "name": "AI搜索优化", "check_count": 6},
    {"id": "meta_tags", "name": "Meta标签", "check_count": 10},
    {"id": "page_structure", "name": "页面结构", "check_count": 8},
    {"id": "mobile_friendly", "name": "移动端适配", "check_count": 6},
    {"id": "performance", "name": "性能优化", "check_count": 8},
    {"id": "link_quality", "name": "链接质量", "check_count": 6},
    {"id": "content_quality", "name": "内容质量", "check_count": 8},
    {"id": "security_compliance", "name": "安全合规", "check_count": 6},
    {"id": "ai_crawler_friendly", "name": "AI爬虫友好", "check_count": 6},
    {"id": "social_media", "name": "社交媒体", "check_count": 4},
]


FORBIDDEN_WORDS_MAP = [
    r"最\d*[好佳优棒级]", r"第[一二三1-3][名位]", r"唯一", r"首个", r"首创",
    r"顶级", r"百分百", r"100%", r"零风险", r"无效退款", r"绝对", r"永不",
    r"全网", r"全球", r"第一", r"冠军",
]


class SiteAuditEngine:
    def __init__(self, ai_engine=None):
        self.ai_engine = ai_engine

    def _check_technical_compliance(self, page_data: dict) -> list[dict]:
        issues = []
        content = page_data.get("content", "")
        html = page_data.get("html", "")

        density_pattern = r"(\d+)\s*(?:kg/m³|kg/m3)"
        density_matches = re.findall(density_pattern, content)
        for val_str in density_matches:
            val = int(val_str)
            if val < 800 or val > 1950:
                issues.append({"severity": "high", "dimension": "technical_compliance", "message": f"密度值{val} kg/m³超出合规范围(800-1950)"})

        strength_pattern = r"LC\d+(?:\.\d+)?"
        valid_grades = ["LC5.0", "LC7.5", "LC10", "LC15", "LC20", "LC25", "LC30", "LC35", "LC40", "LC45", "LC50"]
        strength_matches = re.findall(strength_pattern, content)
        for s in strength_matches:
            if s not in valid_grades:
                issues.append({"severity": "medium", "dimension": "technical_compliance", "message": f"强度等级{s}不在标准列表内"})

        for pattern_str in FORBIDDEN_WORDS_MAP:
            if re.search(pattern_str, content):
                issues.append({"severity": "high", "dimension": "technical_compliance", "message": f"含禁用广告词: {pattern_str}"})

        thermal_pattern = r"(\d+\.?\d*)\s*W/(?:m·K|mK|m\*K)"
        thermal_matches = re.findall(thermal_pattern, content)
        for val_str in thermal_matches:
            val = float(val_str)
            if val < 0.18 or val > 0.50:
                issues.append({"severity": "medium", "dimension": "technical_compliance", "message": f"导热系数{val}超出合规范围(0.18-0.50)"})

        return issues

    def _check_meta_tags(self, page_data: dict) -> list[dict]:
        issues = []
        meta_title = page_data.get("meta_title", "")
        meta_desc = page_data.get("meta_description", "")

        if not meta_title:
            issues.append({"severity": "high", "dimension": "meta_tags", "message": "缺少Meta标题"})
        elif len(meta_title) < 5:
            issues.append({"severity": "medium", "dimension": "meta_tags", "message": f"Meta标题过短({len(meta_title)}字)"})
        elif len(meta_title) > 100:
            issues.append({"severity": "medium", "dimension": "meta_tags", "message": f"Meta标题过长({len(meta_title)}字)"})

        if not meta_desc:
            issues.append({"severity": "high", "dimension": "meta_tags", "message": "缺少Meta描述"})
        elif len(meta_desc) < 20:
            issues.append({"severity": "medium", "dimension": "meta_tags", "message": f"Meta描述过短({len(meta_desc)}字)"})
        elif len(meta_desc) > 200:
            issues.append({"severity": "low", "dimension": "meta_tags", "message": f"Meta描述过长({len(meta_desc)}字)"})

        if meta_title and len(meta_title.split()) < 2:
            issues.append({"severity": "low", "dimension": "meta_tags", "message": "Meta标题关键词密度不足"})

        html = page_data.get("html", "")
        if not re.search(r'<meta\s+name="keywords"', html):
            issues.append({"severity": "low", "dimension": "meta_tags", "message": "缺少Meta Keywords标签"})

        return issues

    def _check_page_structure(self, page_data: dict) -> list[dict]:
        issues = []
        html = page_data.get("html", "")

        h1_tags = re.findall(r"<h1[^>]*>", html)
        if not h1_tags:
            issues.append({"severity": "high", "dimension": "page_structure", "message": "页面缺少H1标签"})
        elif len(h1_tags) > 1:
            issues.append({"severity": "medium", "dimension": "page_structure", "message": f"页面包含多个H1标签({len(h1_tags)}个)"})

        h2_tags = re.findall(r"<h2[^>]*>", html)
        if not h2_tags:
            issues.append({"severity": "low", "dimension": "page_structure", "message": "页面缺少H2标签"})

        if not re.search(r'<html\s', html):
            issues.append({"severity": "high", "dimension": "page_structure", "message": "缺少html根标签"})
        if not re.search(r'<head[^>]*>', html):
            issues.append({"severity": "high", "dimension": "page_structure", "message": "缺少head标签"})

        if not re.search(r'<body[^>]*>', html):
            issues.append({"severity": "high", "dimension": "page_structure", "message": "缺少body标签"})

        if not re.search(r'<meta\s+charset', html):
            issues.append({"severity": "high", "dimension": "page_structure", "message": "缺少charset声明"})

        if not re.search(r'<title[^>]*>', html):
            issues.append({"severity": "high", "dimension": "page_structure", "message": "缺少title标签"})

        return issues

    def _check_security_compliance(self, page_data: dict) -> list[dict]:
        issues = []
        url = page_data.get("url", "")
        html = page_data.get("html", "")

        if not url.startswith("https://"):
            issues.append({"severity": "high", "dimension": "security_compliance", "message": "未使用HTTPS协议"})

        if not re.search(r'<meta\s+http-equiv=["\']Content-Security-Policy["\']', html):
            issues.append({"severity": "medium", "dimension": "security_compliance", "message": "缺少CSP安全策略"})

        if re.search(r"(password|secret|token|key|auth).*?=", html, re.IGNORECASE):
            issues.append({"severity": "high", "dimension": "security_compliance", "message": "页面可能泄露敏感信息"})

        script_tags = re.findall(r"<script[^>]*src=['\"]([^'\"]+)['\"]", html)
        for src in script_tags:
            if src.startswith("http://"):
                issues.append({"severity": "medium", "dimension": "security_compliance", "message": f"外部脚本使用HTTP协议: {src}"})

        return issues

    def _check_ai_crawler_friendly(self, page_data: dict) -> list[dict]:
        issues = []
        html = page_data.get("html", "")

        if not re.search(r'<meta\s+name=["\']robots["\']', html):
            issues.append({"severity": "medium", "dimension": "ai_crawler_friendly", "message": "缺少robots meta标签"})

        if not re.search(r'<link[^>]*rel=["\']canonical["\']', html):
            issues.append({"severity": "medium", "dimension": "ai_crawler_friendly", "message": "缺少规范URL(canonical)标记"})

        if not re.search(r'<script[^>]*type=["\']application/ld\+json["\']', html):
            issues.append({"severity": "low", "dimension": "ai_crawler_friendly", "message": "缺少JSON-LD结构化数据"})

        if not re.search(r'<link[^>]*rel=["\']sitemap["\']', html) and "/sitemap.xml" not in html:
            issues.append({"severity": "low", "dimension": "ai_crawler_friendly", "message": "未引用sitemap.xml"})

        if not re.search(r'<html[^>]*lang=["\']', html):
            issues.append({"severity": "low", "dimension": "ai_crawler_friendly", "message": "html标签缺少lang属性"})

        return issues

    def _check_mobile_friendly(self, page_data: dict) -> list[dict]:
        issues = []
        html = page_data.get("html", "")

        if not re.search(r'<meta\s+name=["\']viewport["\']', html):
            issues.append({"severity": "high", "dimension": "mobile_friendly", "message": "缺少viewport视口设置"})

        if not re.search(r'@media\s*[\(]', html) and not re.search(r'<link[^>]+media=["\']', html):
            issues.append({"severity": "medium", "dimension": "mobile_friendly", "message": "未检测到CSS媒体查询，可能不支持响应式"})

        if re.search(r'width\s*[:=]\s*\d{4,}', html):
            issues.append({"severity": "medium", "dimension": "mobile_friendly", "message": "存在固定宽像素值，可能影响移动端显示"})

        font_size_small = re.findall(r'font-size\s*:\s*(\d+)px', html)
        for size in font_size_small:
            if int(size) < 12:
                issues.append({"severity": "low", "dimension": "mobile_friendly", "message": f"字体大小{size}px过小，移动端阅读困难"})

        if re.search(r'<table[^>]*>', html) and not re.search(r'<meta\s+name=["\']viewport["\']', html):
            issues.append({"severity": "low", "dimension": "mobile_friendly", "message": "页面含表格但无viewport设置，移动端可能错位"})

        if not re.search(r'<meta\s+name=["\']format-detection["\']', html):
            issues.append({"severity": "low", "dimension": "mobile_friendly", "message": "缺少format-detection设置，电话号码可能被错误识别"})

        return issues

    def _check_performance(self, page_data: dict) -> list[dict]:
        issues = []
        html = page_data.get("html", "")

        inline_styles = re.findall(r'style\s*=\s*["\'][^"\']*["\']', html)
        if len(inline_styles) > 20:
            issues.append({"severity": "medium", "dimension": "performance", "message": f"内联样式过多({len(inline_styles)}处)，建议合并到CSS文件"})

        script_tags = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', html)
        style_tags = re.findall(r'<link[^>]*href=["\']([^"\']+)["\'][^>]*rel=["\']stylesheet["\']', html)
        total_resources = len(script_tags) + len(style_tags)
        if total_resources > 20:
            issues.append({"severity": "medium", "dimension": "performance", "message": f"外部资源过多({total_resources}个)，建议合并减少请求数"})

        async_scripts = re.findall(r'<script[^>]*(?:async|defer)[^>]*src=["\']([^"\']+)["\']', html)
        blocking_scripts = len(script_tags) - len(async_scripts)
        if blocking_scripts > 5:
            issues.append({"severity": "low", "dimension": "performance", "message": f"同步阻塞脚本过多({blocking_scripts}个)，建议使用async/defer"})

        large_images = re.findall(r'<img[^>]*src=["\']([^"\']+\.(?:jpg|jpeg|png|gif))["\']', html)
        if len(large_images) > 15:
            issues.append({"severity": "low", "dimension": "performance", "message": f"图片过多({len(large_images)}张)，建议使用懒加载"})

        if re.search(r'<link[^>]*rel=["\']stylesheet["\'][^>]*media=["\']print["\']', html):
            issues.append({"severity": "low", "dimension": "performance", "message": "存在打印样式表，建议使用media=print限制加载"})

        if not re.search(r'<link[^>]*rel=["\']preload["\']', html):
            issues.append({"severity": "low", "dimension": "performance", "message": "未使用preload预加载关键资源"})

        total_size = len(html)
        if total_size > 100000:
            issues.append({"severity": "medium", "dimension": "performance", "message": f"页面体积过大({total_size // 1000}KB)，建议优化"})

        return issues

    def _check_link_quality(self, page_data: dict) -> list[dict]:
        issues = []
        html = page_data.get("html", "")

        internal_links = re.findall(r'<a[^>]*href=["\']/([^"\']+)["\']', html)
        external_links = re.findall(r'<a[^>]*href=["\']https?://(?!.*youding\.com)[^"\']+["\']', html)
        nofollow_links = re.findall(r'<a[^>]*rel=["\'][^"\']*nofollow[^"\']*["\']', html)

        if not internal_links:
            issues.append({"severity": "medium", "dimension": "link_quality", "message": "页面缺少站内链接"})
        elif len(internal_links) < 3:
            issues.append({"severity": "low", "dimension": "link_quality", "message": f"站内链接过少({len(internal_links)}个)，建议增加相关页面互链"})

        if external_links:
            nofollow_external = re.findall(r'<a[^>]*href=["\']https?://(?!.*youding\.com)[^"\']+["\'][^>]*rel=["\'][^"\']*nofollow[^"\']*["\']', html)
            if len(nofollow_external) < len(external_links):
                issues.append({"severity": "medium", "dimension": "link_quality", "message": f"外部链接({len(external_links)}个)未全部使用nofollow"})

        anchor_text_missing = re.findall(r'<a[^>]*href=["\'][^"\']+["\'][^>]*>\s*</a>', html)
        if anchor_text_missing:
            issues.append({"severity": "medium", "dimension": "link_quality", "message": f"存在空锚文本链接({len(anchor_text_missing)}个)"})

        broken_anchors = re.findall(r'<a[^>]*href=["\']#[^"\']*["\']>', html)
        if len(broken_anchors) > 5:
            issues.append({"severity": "low", "dimension": "link_quality", "message": f"页内锚点过多({len(broken_anchors)}个)，可能影响爬虫抓取效率"})

        return issues

    def _check_content_quality(self, page_data: dict) -> list[dict]:
        issues = []
        content = page_data.get("content", "")

        word_count = len(content)
        if word_count < 300:
            issues.append({"severity": "high", "dimension": "content_quality", "message": f"正文内容过少({word_count}字)，建议至少300字"})
        elif word_count < 600:
            issues.append({"severity": "medium", "dimension": "content_quality", "message": f"正文偏少({word_count}字)，建议增至600字以上"})

        paragraphs = content.split("\n")
        non_empty_paras = [p for p in paragraphs if p.strip()]
        if len(non_empty_paras) < 3:
            issues.append({"severity": "medium", "dimension": "content_quality", "message": f"段落过少({len(non_empty_paras)}段)，建议分段提高可读性"})

        keyword = page_data.get("meta_title", "")
        if keyword:
            keyword_count = content.lower().count(keyword[:4].lower())
            if keyword_count == 0:
                issues.append({"severity": "medium", "dimension": "content_quality", "message": "正文未提及标题中的核心关键词"})

        content_chars = len(content.replace(" ", "").replace("\n", ""))
        if content_chars > 0 and word_count < content_chars * 0.5:
            issues.append({"severity": "low", "dimension": "content_quality", "message": "内容中非中文字符比例过高，可能存在乱码"})

        if not re.search(r'[\d]{4}年', content) and not re.search(r'20\d{2}', content):
            issues.append({"severity": "low", "dimension": "content_quality", "message": "内容缺少年份/数据引用，建议增加时效性信息"})

        duplicates = re.findall(r'^(.+)$', content, re.MULTILINE)
        seen = set()
        dup_count = 0
        for line in duplicates:
            stripped = line.strip()
            if len(stripped) > 10 and stripped in seen:
                dup_count += 1
            seen.add(stripped)
        if dup_count > 3:
            issues.append({"severity": "low", "dimension": "content_quality", "message": f"存在重复段落({dup_count}处)，建议去重"})

        return issues

    def _check_social_media(self, page_data: dict) -> list[dict]:
        issues = []
        html = page_data.get("html", "")

        if not re.search(r'<meta\s+property=["\']og:title["\']', html):
            issues.append({"severity": "medium", "dimension": "social_media", "message": "缺少Open Graph标题(og:title)"})

        if not re.search(r'<meta\s+property=["\']og:description["\']', html):
            issues.append({"severity": "medium", "dimension": "social_media", "message": "缺少Open Graph描述(og:description)"})

        if not re.search(r'<meta\s+property=["\']og:image["\']', html):
            issues.append({"severity": "low", "dimension": "social_media", "message": "缺少Open Graph图片(og:image)"})

        if not re.search(r'<meta\s+name=["\']twitter:card["\']', html):
            issues.append({"severity": "low", "dimension": "social_media", "message": "缺少Twitter Card设置"})

        return issues

    def _check_ai_search_optimization(self, page_data: dict) -> list[dict]:
        issues = []
        html = page_data.get("html", "")
        content = page_data.get("content", "")

        structured_data = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>([^<]+)</script>', html)
        if not structured_data:
            issues.append({"severity": "medium", "dimension": "ai_search_optimization", "message": "缺少JSON-LD结构化数据，影响AI搜索引擎理解页面"})
        else:
            for sd in structured_data:
                try:
                    data = json.loads(sd)
                    sd_type = data.get("@type", "")
                    if sd_type not in ("Product", "Article", "Organization", "FAQPage", "BreadcrumbList", "WebPage"):
                        issues.append({"severity": "low", "dimension": "ai_search_optimization", "message": f"结构化数据类型'{sd_type}'非推荐类型"})
                except json.JSONDecodeError:
                    issues.append({"severity": "medium", "dimension": "ai_search_optimization", "message": "JSON-LD结构化数据格式有误"})

        if not re.search(r'<meta\s+name=["\']description["\']', html):
            issues.append({"severity": "high", "dimension": "ai_search_optimization", "message": "缺少Meta Description，AI搜索引擎无法获取页面摘要"})

        if not re.search(r'<title[^>]*>', html):
            issues.append({"severity": "high", "dimension": "ai_search_optimization", "message": "缺少Title标签，影响AI搜索引擎理解页面主题"})

        if re.search(r'<meta\s+name=["\']robots["\'][^>]*content=["\'][^"\']*noindex', html):
            issues.append({"severity": "medium", "dimension": "ai_search_optimization", "message": "页面被设置为noindex，AI搜索引擎将不会索引此页面"})

        if not re.search(r'<a[^>]*href=["\']/?[^"\']+["\']', html):
            issues.append({"severity": "medium", "dimension": "ai_search_optimization", "message": "页面无可抓取链接，AI爬虫无法发现其他页面"})

        content_length = len(content.replace(" ", "").replace("\n", ""))
        if content_length < 200:
            issues.append({"severity": "medium", "dimension": "ai_search_optimization", "message": f"内容过短({content_length}字)，AI搜索引擎难以准确理解主题"})

        return issues

    def _calculate_score(self, issues: list[dict]) -> int:
        severity_weights = {"high": 10, "medium": 5, "low": 2}
        total_penalty = sum(severity_weights.get(i.get("severity", "low"), 2) for i in issues)
        return max(0, min(100, 100 - total_penalty))

    def _calculate_dimension_scores(self, issues: list[dict]) -> dict:
        dimensions = {}
        for i in issues:
            dim = i.get("dimension", "unknown")
            if dim not in dimensions:
                dimensions[dim] = []
            dimensions[dim].append(i)
        scores = {}
        for dim, dim_issues in dimensions.items():
            scores[dim] = self._calculate_score(dim_issues)
        return scores

    def run_basic_audit(self, page_data: dict) -> dict:
        all_issues = []
        all_issues.extend(self._check_technical_compliance(page_data))
        all_issues.extend(self._check_meta_tags(page_data))
        all_issues.extend(self._check_page_structure(page_data))
        all_issues.extend(self._check_security_compliance(page_data))
        all_issues.extend(self._check_ai_crawler_friendly(page_data))
        all_issues.extend(self._check_mobile_friendly(page_data))
        all_issues.extend(self._check_performance(page_data))
        all_issues.extend(self._check_link_quality(page_data))
        all_issues.extend(self._check_content_quality(page_data))
        all_issues.extend(self._check_social_media(page_data))
        all_issues.extend(self._check_ai_search_optimization(page_data))

        score = self._calculate_score(all_issues)
        dimension_scores = self._calculate_dimension_scores(all_issues)
        high_issues = [i for i in all_issues if i["severity"] == "high"]
        medium_issues = [i for i in all_issues if i["severity"] == "medium"]

        recommendations = []
        for issue in sorted(all_issues, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3)):
            recommendations.append({"issue": issue["message"], "priority": issue["severity"]})

        return {
            "score": score,
            "total_issues": len(all_issues),
            "critical_issues": len(high_issues),
            "warning_issues": len(medium_issues),
            "issues": all_issues,
            "recommendations": recommendations[:20],
            "dimension_scores": dimension_scores,
        }

    async def run_full_audit(self, page_data: dict) -> dict:
        basic_result = self.run_basic_audit(page_data)

        if self.ai_engine:
            prompt = f"""作为一个SEO审计专家，请对以下页面进行深度审计分析。
            
页面URL: {page_data.get("url", "未知")}
页面标题: {page_data.get("meta_title", "未知")}
页面描述: {page_data.get("meta_description", "未知")}
内容摘要: {page_data.get("content", "")[:500]}

已发现的问题数量: {basic_result["total_issues"]}个，评分: {basic_result["score"]}

请从内容质量、移动端适配、性能优化、链接质量、社交媒体等维度补充审计建议。
按优先级输出5条建议，每行一个。"""

            ai_result = await self.ai_engine.generate(prompt, max_tokens=1000)
            ai_content = ai_result.get("content", "")
            ai_recommendations = [line.strip("- ").strip() for line in ai_content.split("\n") if line.strip()]
            basic_result["recommendations"].extend(
                {"issue": rec, "priority": "medium", "source": "ai"}
                for rec in ai_recommendations[:10]
            )

        return basic_result

    async def run_audit(self, url: str, audit_type: str = "full") -> dict:
        if audit_type == "quick":
            page_data = await self._fetch_page_data(url)
            result = self.run_basic_audit(page_data)
        else:
            page_data = await self._fetch_page_data(url)
            result = await self.run_full_audit(page_data)

        result["url"] = url
        result["audit_type"] = audit_type
        result["status"] = "completed"
        return result

    async def _fetch_page_data(self, url: str) -> dict:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (compatible; YoudingSEOAudit/1.0)"})
                html = resp.text
                title_match = re.search(r"<title[^>]*>([^<]+)</title>", html)
                desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html)
                content_text = re.sub(r"<[^>]+>", " ", html)
                content_text = re.sub(r"\s+", " ", content_text).strip()

                return {
                    "url": url,
                    "html": html,
                    "content": content_text[:5000],
                    "meta_title": title_match.group(1) if title_match else "",
                    "meta_description": desc_match.group(1) if desc_match else "",
                    "status_code": resp.status_code,
                }
        except Exception as e:
            return {"url": url, "html": "", "content": f"Error: {str(e)}", "meta_title": "", "meta_description": ""}


def run_full_audit_service(db, audit_data) -> "SiteAudit":
    import asyncio
    from app.models.seo import SiteAudit as SiteAuditModel
    from datetime import datetime, timezone

    try:
        validate_url_safety(audit_data.url)
    except ValueError as e:
        record = SiteAuditModel(
            url=audit_data.url,
            status="failed",
            audit_type=audit_data.audit_type,
            report_data=json.dumps({"error": str(e)}, ensure_ascii=False),
            started_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    record = SiteAuditModel(
        url=audit_data.url,
        status="running",
        audit_type=audit_data.audit_type,
        started_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        engine = SiteAuditEngine()
        result = asyncio.run(engine.run_audit(audit_data.url, "full"))
        record.score = result.get("score", 0)
        record.total_issues = result.get("total_issues", 0)
        record.critical_issues = result.get("critical_issues", 0)
        record.warning_issues = result.get("warning_issues", 0)
        record.report_data = json.dumps(result, ensure_ascii=False)
        record.status = "completed"
        record.completed_at = datetime.now(timezone.utc)
    except Exception as e:
        record.status = "failed"
        record.report_data = json.dumps({"error": str(e)}, ensure_ascii=False)

    db.commit()
    db.refresh(record)
    return record


def run_quick_audit_service(db, audit_data) -> "SiteAudit":
    import asyncio
    from app.models.seo import SiteAudit as SiteAuditModel
    from datetime import datetime, timezone

    try:
        validate_url_safety(audit_data.url)
    except ValueError as e:
        record = SiteAuditModel(
            url=audit_data.url,
            status="failed",
            audit_type=audit_data.audit_type,
            report_data=json.dumps({"error": str(e)}, ensure_ascii=False),
            started_at=datetime.now(timezone.utc),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    record = SiteAuditModel(
        url=audit_data.url,
        status="running",
        audit_type=audit_data.audit_type,
        started_at=datetime.now(timezone.utc),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        engine = SiteAuditEngine()
        result = asyncio.run(engine.run_audit(audit_data.url, "quick"))
        record.score = result.get("score", 0)
        record.total_issues = result.get("total_issues", 0)
        record.critical_issues = result.get("critical_issues", 0)
        record.warning_issues = result.get("warning_issues", 0)
        record.report_data = json.dumps(result, ensure_ascii=False)
        record.status = "completed"
        record.completed_at = datetime.now(timezone.utc)
    except Exception as e:
        record.status = "failed"
        record.report_data = json.dumps({"error": str(e)}, ensure_ascii=False)

    db.commit()
    db.refresh(record)
    return record
