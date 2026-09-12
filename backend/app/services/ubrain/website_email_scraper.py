"""
零成本网站邮箱抓取服务 — 从目标公司网站提取邮箱

策略：
1. 抓取首页 + Contact + About 页面
2. 用正则提取所有邮箱
3. 过滤掉 info@ / support@ / admin@ 等通用邮箱（可选）
4. 去重 + 初步验证

零成本原理：
- 使用 httpx 直接 HTTP 请求（不需要付费爬虫 API）
- 解析 HTML 用 BeautifulSoup（免费库）
- 邮箱提取用正则（零成本）
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Optional, Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedEmail:
    """抓取到的邮箱信息"""
    email: str
    source_page: str  # 从哪个页面抓取的
    confidence: float  # 0.0-1.0，置信度


@dataclass
class WebsiteEmailResult:
    """网站邮箱抓取结果"""
    domain: str
    emails: list[ScrapedEmail] = field(default_factory=list)
    pages_scraped: list[str] = field(default_factory=list)
    error: Optional[str] = None


# 邮箱正则（宽松版，用于从 HTML 文本中提取）
_EMAIL_RE = re.compile(
    r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"
)

# 低价值通用邮箱（置信度低）
_GENERIC_LOCAL_PARTS = {
    "info", "contact", "support", "sales", "admin", "hello",
    "office", "team", "enquiry", "inquiry", "service", "help",
    "webmaster", "postmaster", "noreply", "no-reply", "marketing",
    "hr", "career", "jobs", "press", "media", "billing", "finance",
    "accounts", "legal", "privacy", "abuse",
}

# 优先抓取的页面路径
_PRIORITY_PATHS = [
    "/contact", "/contact-us", "/contact-us.html", "/contact.html",
    "/about", "/about-us", "/about-us.html", "/about.html",
    "/team", "/our-team", "/people",
    "/imprint", "/impressum", "/legal", "/privacy",
]

# User-Agent
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


async def scrape_website_emails(
    domain: str,
    *,
    max_pages: int = 5,
    timeout: int = 15,
) -> WebsiteEmailResult:
    """从目标公司网站抓取邮箱。

    Args:
        domain: 公司域名（如 example.com，自动加 https://）
        max_pages: 最多抓取多少个页面
        timeout: 单页请求超时（秒）

    Returns:
        WebsiteEmailResult
    """
    result = WebsiteEmailResult(domain=domain)
    # 规范化 base URL
    base_url = domain if domain.startswith("http") else f"https://{domain}"
    base_url = base_url.rstrip("/")
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": _UA},
        ) as client:
            # 1. 先抓首页
            home_html = await _fetch_page(client, base_url)
            if home_html:
                result.pages_scraped.append(base_url)
                result.emails.extend(_extract_emails(home_html, base_url))
                # 2. 从首页找联系页面链接
                contact_links = _find_contact_links(home_html, base_url)
                # 3. 抓取优先路径 + 找到的联系页
                visited = {base_url}
                to_visit: list[str] = []
                # 优先路径
                for path in _PRIORITY_PATHS:
                    url = urljoin(base_url, path)
                    if url not in visited:
                        to_visit.append(url)

                # 首页找到的链接
                for link in contact_links:
                    if link not in visited and link not in to_visit:
                        to_visit.append(link)

                # 抓取页面（限制数量）
                tasks = []
                for url in to_visit[:max_pages - 1]:
                    if url in visited:
                        continue
                    visited.add(url)
                    tasks.append(_fetch_and_extract(client, url))

                if tasks:
                    page_results = await asyncio.gather(*tasks, return_exceptions=True)
                    for pr in page_results:
                        if isinstance(pr, tuple) and pr[0]:
                            page_url, emails = pr
                            result.pages_scraped.append(page_url)
                            result.emails.extend(emails)

    except Exception as e:
        result.error = str(e)
        logger.warning(f"抓取 {domain} 邮箱失败: {e}")

    # 去重 + 排序
    result.emails = _deduplicate_and_rank(result.emails)
    return result


async def _fetch_page(client: httpx.AsyncClient, url: str) -> str | None:
    """抓取单个页面 HTML。"""
    try:
        resp = await client.get(url)
        if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
            return resp.text
    except Exception:
        pass
    return None


async def _fetch_and_extract(
    client: httpx.AsyncClient, url: str
) -> tuple[str, list[ScrapedEmail]]:
    """抓取页面并提取邮箱。"""
    html = await _fetch_page(client, url)
    if not html:
        return url, []
    return url, _extract_emails(html, url)


def _extract_emails(html: str, source_url: str) -> list[ScrapedEmail]:
    """从 HTML 中提取邮箱。"""
    # 先去掉 script/style 标签内容
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(" ", strip=True)
    emails = _EMAIL_RE.findall(text)
    results = []
    seen = set()
    for email in emails:
        email = email.lower().rstrip(".,;:!?)(")
        if email in seen:
            continue
        seen.add(email)
        local = email.split("@", 1)[0]
        # 计算置信度
        if local in _GENERIC_LOCAL_PARTS:
            confidence = 0.3  # 通用邮箱
        elif len(local) < 3:
            confidence = 0.4
        elif "." in local or "-" in local:
            confidence = 0.8  # 可能是人名
        else:
            confidence = 0.6

        results.append(ScrapedEmail(
            email=email,
            source_page=source_url,
            confidence=confidence,
        ))

    # 按置信度降序
    results.sort(key=lambda e: e.confidence, reverse=True)
    return results


def _find_contact_links(html: str, base_url: str) -> list[str]:
    """从首页 HTML 中找联系页面链接。"""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        text = a.get_text().lower().strip()
        if any(kw in href for kw in ["contact", "about", "team", "imprint"]) or \
           any(kw in text for kw in ["contact", "about us", "our team", "联系"]):
            full_url = urljoin(base_url, a["href"])
            # 确保同源
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                links.append(full_url)
    return links[:5]


def _deduplicate_and_rank(emails: list[ScrapedEmail]) -> list[ScrapedEmail]:
    """去重（取最高置信度）+ 排序。"""
    best: dict[str, ScrapedEmail] = {}
    for e in emails:
        if e.email not in best or e.confidence > best[e.email].confidence:
            best[e.email] = e
    return sorted(best.values(), key=lambda e: e.confidence, reverse=True)


class WebsiteEmailScraper:
    """企业官网邮箱抓取器封装类。"""

    async def scrape(self, url: str, max_depth: int = 2) -> list[dict[str, Any]]:
        """从企业官网自动抓取联系方式。"""
        res = await scrape_website(url, max_depth=max_depth)
        return [
            {
                "email": e.email,
                "source_page": e.source_page,
                "confidence": e.confidence,
            }
            for e in res.emails
        ]