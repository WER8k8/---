"""官网 ICP 画像 — 改编自 qingchuh/sale_agent_factory WebAnalyzer（MIT）。"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

_CERT_PATTERN = re.compile(
    r"\b(ISO\s?\d+|CE\b|UL\b|FDA|RoHS|REACH|SASO|BSCI|SGS|TUV|认证|certificate)\b",
    re.I,
)
_MOQ_PATTERN = re.compile(r"\b(MOQ|minimum order|最小起订)\b", re.I)
_PRODUCT_KW = re.compile(r"\b(product|products|solution|equipment|machine|设备|产品)\b", re.I)


def _normalize_url(url: str) -> str:
    """实现 normalizeURL 的功能。
    
    :param url: 参数 url（类型: str）
    :return: 返回 str 结果
    """
    raw = (url or "").strip()
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw
    return raw.rstrip("/")


def _clean_text(text: str, limit: int = 4000) -> str:
    """实现 清理文本 的功能。
    
    :param text: 参数 text（类型: str）
    :param limit: 参数 limit（类型: int）
    :return: 返回 str 结果
    """
    t = re.sub(r"\s+", " ", text or "").strip()
    return t[:limit]


def _extract_emails(text: str) -> list[str]:
    """实现 提取emails 的功能。
    
    :param text: 参数 text（类型: str）
    :return: 返回 list[str] 结果
    """
    return list(set(re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", text)))[:5]


def analyze_website_icp(
    website_url: str,
    *,
    max_pages: int = 5,
    timeout: float = 12.0,
) -> dict[str, Any]:
    """抓取官网并生成 ICP 画像摘要（同步，供 onboarding/找客使用）。"""
    base = _normalize_url(website_url)
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    errors: list[str] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ShangXian-ICP/1.0; B2B onboarding)",
        "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
    }
    to_visit = [base]
    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            if url in visited:
                continue
            try:
                resp = client.get(url)
                if resp.status_code >= 400:
                    errors.append(f"{url}: HTTP {resp.status_code}")
                    continue
                soup = BeautifulSoup(resp.text, "html.parser")
                title = (soup.title.string or "").strip() if soup.title else ""
                meta = soup.find("meta", attrs={"name": "description"})
                description = (meta.get("content") or "").strip() if meta else ""
                body_text = _clean_text(soup.get_text(" ", strip=True))
                emails = _extract_emails(body_text)
                certs = list(set(_CERT_PATTERN.findall(body_text)))[:10]
                has_moq = bool(_MOQ_PATTERN.search(body_text))
                page = {
                    "url": url,
                    "title": title[:300],
                    "description": description[:500],
                    "emails": emails,
                    "certifications_mentioned": certs,
                    "has_moq_mention": has_moq,
                    "snippet": body_text[:800],
                }
                pages.append(page)
                visited.add(url)
                if len(visited) < max_pages:
                    for a in soup.find_all("a", href=True):
                        href = urljoin(url, a["href"])
                        parsed = urlparse(href)
                        if parsed.netloc and parsed.netloc != urlparse(base).netloc:
                            continue
                        if any(href.lower().endswith(ext) for ext in (".pdf", ".jpg", ".png", ".zip")):
                            continue
                        if href not in visited and href not in to_visit:
                            to_visit.append(href.split("#")[0])
            except Exception as exc:
                errors.append(f"{url}: {exc}")

    main = pages[0] if pages else {}
    domain = urlparse(base).netloc.replace("www.", "")
    company_name = main.get("title") or domain.split(".")[0].title()
    products_hint: list[str] = []
    for p in pages:
        if _PRODUCT_KW.search(p.get("title", "") + p.get("snippet", "")):
            products_hint.append(p.get("title") or p.get("url", ""))

    icp = {
        "company_name": company_name,
        "website": base,
        "domain": domain,
        "value_props": main.get("description") or main.get("snippet", "")[:400],
        "certifications": list({c for p in pages for c in p.get("certifications_mentioned") or []}),
        "contact_emails": list({e for p in pages for e in p.get("emails") or []}),
        "has_moq_mention": any(p.get("has_moq_mention") for p in pages),
        "product_pages": products_hint[:8],
        "pages_analyzed": len(pages),
    }
    return {
        "icp": icp,
        "pages": pages,
        "errors": errors,
        "gw_task": "factory_onboarding_icp",
        "source": "sale_agent_factory/web_analyzer (adapted)",
        "next_steps": [
            "确认 ICP 行业/地区/MOQ 写入 tenant onboarding",
            "可选：DeerFlow 市场研究验证竞品",
        ],
    }
