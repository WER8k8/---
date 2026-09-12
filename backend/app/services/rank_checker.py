"""
真实的搜索引擎排名查询服务

支持百度、Google、Bing 三个搜索引擎。
百度采用的是真实爬取方式（模拟浏览器请求），如果IP被封或反爬拦截，
自动降级返回带 [模拟] 标记的结果。
"""

import logging
import random
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ──────────────────────────── User-Agent 池 ────────────────────────────
_DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

_BAIDU_MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.6778.200 Mobile Safari/537.36"
)

_ACCEPT_LANGUAGE = "zh-CN,zh;q=0.9,en;q=0.8"
_REQUEST_TIMEOUT = 15  # seconds


def _random_ua() -> str:
    """_random_ua。
    :return: 返回处理结果。
    """
    return random.choice(_DESKTOP_USER_AGENTS)


def _common_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """_common_headers。

    参数说明：
    :param extra: 参数 extra
    :return: 返回处理结果。
    """
    h = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": _ACCEPT_LANGUAGE,
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": _random_ua(),
    }
    if extra:
        h.update(extra)
    return h


# ──────────────────────────── 结果数据类 ────────────────────────────

class RankResult:
    """单条排名结果"""
    __slots__ = ("rank", "url", "title", "snippet")
    def __init__(self, rank: int, url: str, title: str = "", snippet: str = ""):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param rank: 参数 rank
        :param url: 参数 url
        :param title: 参数 title
        :param snippet: 参数 snippet
        :return: 返回处理结果。
        """
        self.rank = rank
        self.url = url
        self.title = title
        self.snippet = snippet

    def to_dict(self) -> Dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "rank": self.rank,
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
        }


class CheckResult:
    """单次排名查询的整体结果"""
    __slots__ = ("keyword", "engine", "domain", "results", "best_rank",
                 "total_results", "is_simulated", "checked_at", "error")

    def __init__(
        self,
        keyword: str,
        engine: str,
        domain: str,
        results: Optional[List[RankResult]] = None,
        is_simulated: bool = False,
        error: Optional[str] = None,
    ):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param keyword: 参数 keyword
        :param engine: 参数 engine
        :param domain: 参数 domain
        :param results: 参数 results
        :param is_simulated: 参数 is_simulated
        :param error: 参数 error
        :return: 返回处理结果。
        """
        self.keyword = keyword
        self.engine = engine
        self.domain = domain
        self.results = results or []
        self.best_rank = min((r.rank for r in self.results), default=None)
        self.total_results = len(self.results)
        self.is_simulated = is_simulated
        self.checked_at = datetime.now(timezone.utc).isoformat()
        self.error = error

    def to_dict(self) -> Dict:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "keyword": self.keyword,
            "engine": self.engine,
            "domain": self.domain,
            "results": [r.to_dict() for r in self.results],
            "best_rank": self.best_rank,
            "total_results": self.total_results,
            "is_simulated": self.is_simulated,
            "checked_at": self.checked_at,
            "error": self.error,
        }


# ──────────────────────────── 辅助函数 ────────────────────────────

def _extract_domain(url: str) -> str:
    """从URL中提取干净域名"""
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower().replace("www.", "")
    except Exception:
        return url.lower().replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]


# ──────────────────────────── 百度爬取 ────────────────────────────

class BaiduChecker:
    """百度搜索引擎排名查询（真实爬取）"""
    SEARCH_URL = "https://www.baidu.com/s"
    _last_request_time = 0.0
    @classmethod
    def _rate_limit(cls):
        """简单的请求速率限制：两次请求间隔至少1.5秒"""
        now = time.monotonic()
        elapsed = now - cls._last_request_time
        if elapsed < 1.5:
            time.sleep(1.5 - elapsed + random.uniform(0, 0.5))
        cls._last_request_time = time.monotonic()

    @classmethod
    def search(cls, keyword: str, domain: str, max_pages: int = 5) -> Tuple[List[RankResult], bool, Optional[str]]:
        """
        真实爬取百度搜索结果，遍历前 max_pages 页。

        Returns:
            (results, is_simulated, error_message)
            is_simulated=True 说明爬取失败，返回模拟数据
        """
        target_domain = _extract_domain(domain)
        if not target_domain:
            return [], True, "缺少目标域名"

        results: List[RankResult] = []
        session = requests.Session()
        session.headers.update(_common_headers({"Referer": "https://www.baidu.com/"}))
        try:
            for page in range(max_pages):
                cls._rate_limit()
                pn = page * 10  # 百度每页10条结果
                params = {
                    "wd": keyword,
                    "pn": pn,
                    "rn": 10,
                    "ie": "utf-8",
                }
                try:
                    resp = session.get(
                        cls.SEARCH_URL,
                        params=params,
                        timeout=_REQUEST_TIMEOUT,
                        allow_redirects=True,
                    )
                    resp.raise_for_status()
                except requests.RequestException as e:
                    logger.warning("百度搜索请求失败 page=%d keyword=%s: %s", page, keyword, e)
                    break

                # 判断是否被反爬
                html = resp.text
                if cls._is_blocked(html):
                    logger.warning("百度反爬拦截 page=%d keyword=%s", page, keyword)
                    return [], True, "IP可能被百度暂时屏蔽"

                # 解析搜索结果
                page_results = cls._parse(html, keyword, target_domain, pn)
                results.extend(page_results)
                if not cls._has_next_page(html):
                    break

        except Exception as e:
            logger.error("百度搜索整体异常 keyword=%s: %s", keyword, e)
            return [], True, str(e)
        finally:
            session.close()

        return results, False, None

    @classmethod
    def _is_blocked(cls, html: str) -> bool:
        """判断百度是否返回了反爬/验证页面"""
        blocked_signals = [
            "请输入验证码",
            "反爬虫",
            "百度安全验证",
            "您的访问出错了",
            "请点击输入验证码",
        ]
        return any(signal in html for signal in blocked_signals)

    @classmethod
    def _has_next_page(cls, html: str) -> bool:
        """判断搜索结果是否还有下一页"""
        return "下一页" in html

    @classmethod
    def _parse(cls, html: str, keyword: str, target_domain: str, offset: int) -> List[RankResult]:
        """
        解析百度搜索结果HTML。

        百度搜索结果结构：
        - 每个结果在 class="result c-container" 的 div 中
        - 标题在 h3 > a 中
        - URL 在 data-showurl 属性或链接 URL 中
        - 摘要通常在 class="c-abstract" 中
        """
        results: List[RankResult] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            # 查找所有搜索结果容器
            result_divs = soup.select(".result, .c-container, div[tpl]")
            if not result_divs:
                # 尝试更宽泛的选择器
                result_divs = soup.select("div.result, div.c-result, div.c-container")

            rank_position = offset
            for div in result_divs:
                rank_position += 1
                # 提取标题和URL
                link = div.select_one("h3 a, h3.t a, a[href*='http']")
                if not link:
                    continue

                url = link.get("href", "")
                title = link.get_text(strip=True)
                # 某些情况下百度用 data-showurl 存储展示URL
                show_url = div.get("data-showurl", "") or link.get("data-showurl", "")
                # 提取摘要
                snippet_el = div.select_one(
                    ".c-abstract, .c-span-last, .content-right_8Zs40, .c-row, span.content-right_8Zs40"
                )
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                # 判断是否匹配目标域名
                result_domain = _extract_domain(url) or _extract_domain(show_url)
                if result_domain and target_domain in result_domain:
                    results.append(RankResult(
                        rank=rank_position,
                        url=url if url.startswith("http") else show_url or url,
                        title=title,
                        snippet=snippet,
                    ))
        except Exception as e:
            logger.error("百度HTML解析异常: %s", e)

        return results


# ──────────────────────────── Google 爬取 ────────────────────────────

class GoogleChecker:
    """Google搜索引擎排名查询"""
    SEARCH_URL = "https://www.google.com/search"
    @classmethod
    def search(cls, keyword: str, domain: str, max_pages: int = 5) -> Tuple[List[RankResult], bool, Optional[str]]:
        """search。

        参数说明：
        :param cls: 参数 cls
        :param keyword: 参数 keyword
        :param domain: 参数 domain
        :param max_pages: 参数 max_pages
        :return: 返回处理结果。
        """
        target_domain = _extract_domain(domain)
        if not target_domain:
            return [], True, "缺少目标域名"

        results: List[RankResult] = []
        session = requests.Session()
        session.headers.update(_common_headers())
        try:
            for page in range(max_pages):
                start = page * 10
                params = {"q": keyword, "start": start, "hl": "zh-CN"}
                try:
                    resp = session.get(
                        cls.SEARCH_URL,
                        params=params,
                        timeout=_REQUEST_TIMEOUT,
                        allow_redirects=True,
                    )
                    resp.raise_for_status()
                except requests.RequestException as e:
                    logger.warning("Google搜索请求失败 page=%d keyword=%s: %s", page, keyword, e)
                    break

                html = resp.text
                if "关于该请求的验证码" in html or "unusual traffic" in html.lower():
                    return [], True, "Google请求验证码"

                page_results = cls._parse(html, keyword, target_domain, start)
                results.extend(page_results)
                if "下一页" not in html and "next" not in html.lower():
                    break

                time.sleep(random.uniform(1, 2))
        except Exception as e:
            logger.error("Google搜索整体异常 keyword=%s: %s", keyword, e)
            return [], True, str(e)
        finally:
            session.close()

        return results, False, None

    @classmethod
    def _parse(cls, html: str, keyword: str, target_domain: str, offset: int) -> List[RankResult]:
        """_parse。

        参数说明：
        :param cls: 参数 cls
        :param html: 参数 html
        :param keyword: 参数 keyword
        :param target_domain: 参数 target_domain
        :param offset: 参数 offset
        :return: 返回处理结果。
        """
        results: List[RankResult] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            result_divs = soup.select("div.g, div[data-sokoban-container]")
            rank_position = offset
            for div in result_divs:
                rank_position += 1
                link = div.select_one("a[href^='http']")
                if not link:
                    continue
                url = link.get("href", "")
                title = div.select_one("h3")
                title_text = title.get_text(strip=True) if title else ""
                snippet_el = div.select_one("div.VwiC3b, span.aCOpRe, div.yXK7lf")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                result_domain = _extract_domain(url)
                if result_domain and target_domain in result_domain:
                    results.append(RankResult(
                        rank=rank_position,
                        url=url,
                        title=title_text,
                        snippet=snippet,
                    ))
        except Exception as e:
            logger.error("Google HTML解析异常: %s", e)

        return results


# ──────────────────────────── Bing 爬取 ────────────────────────────

class BingChecker:
    """Bing搜索引擎排名查询"""
    SEARCH_URL = "https://www.bing.com/search"
    @classmethod
    def search(cls, keyword: str, domain: str, max_pages: int = 3) -> Tuple[List[RankResult], bool, Optional[str]]:
        """search。

        参数说明：
        :param cls: 参数 cls
        :param keyword: 参数 keyword
        :param domain: 参数 domain
        :param max_pages: 参数 max_pages
        :return: 返回处理结果。
        """
        target_domain = _extract_domain(domain)
        if not target_domain:
            return [], True, "缺少目标域名"

        results: List[RankResult] = []
        session = requests.Session()
        session.headers.update(_common_headers())
        try:
            for page in range(max_pages):
                first = page * 10 + 1
                params = {
                    "q": keyword,
                    "first": first,
                    "setmkt": "zh-CN",
                }
                try:
                    resp = session.get(
                        cls.SEARCH_URL,
                        params=params,
                        timeout=_REQUEST_TIMEOUT,
                        allow_redirects=True,
                    )
                    resp.raise_for_status()
                except requests.RequestException as e:
                    logger.warning("Bing搜索请求失败 page=%d keyword=%s: %s", page, keyword, e)
                    break

                html = resp.text
                page_results = cls._parse(html, keyword, target_domain, first - 1)
                results.extend(page_results)
                if "下一页" not in html:
                    break

                time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logger.error("Bing搜索整体异常 keyword=%s: %s", keyword, e)
            return [], True, str(e)
        finally:
            session.close()

        return results, False, None

    @classmethod
    def _parse(cls, html: str, keyword: str, target_domain: str, offset: int) -> List[RankResult]:
        """_parse。

        参数说明：
        :param cls: 参数 cls
        :param html: 参数 html
        :param keyword: 参数 keyword
        :param target_domain: 参数 target_domain
        :param offset: 参数 offset
        :return: 返回处理结果。
        """
        results: List[RankResult] = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            result_items = soup.select("li.b_algo")
            rank_position = offset
            for item in result_items:
                rank_position += 1
                link = item.select_one("h2 a")
                if not link:
                    continue
                url = link.get("href", "")
                title = link.get_text(strip=True)
                snippet_el = item.select_one(".b_caption p, div.b_caption p")
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                result_domain = _extract_domain(url)
                if result_domain and target_domain in result_domain:
                    results.append(RankResult(
                        rank=rank_position,
                        url=url,
                        title=title,
                        snippet=snippet,
                    ))
        except Exception as e:
            logger.error("Bing HTML解析异常: %s", e)

        return results


# ──────────────────────────── 模拟数据降级 ────────────────────────────

def _generate_mock_results(keyword: str, domain: str, engine: str,
                           max_count: int = 5) -> List[RankResult]:
    """当真实爬取失败时，生成带 [模拟] 标记的降级数据"""
    results = []
    base_rank = 3
    snippets = [
        f"与{keyword}相关的搜索结果展示，涵盖产品介绍、价格信息与施工方案……",
        f"提供{keyword}的完整技术方案与工程案例，包含性能指标与检测报告……",
        f"{keyword}厂家直销，现货供应，全国发货，支持定制……",
        f"关于{keyword}的最新行业标准与施工规范解读……",
        f"{keyword}价格行情、市场动态与采购指南……",
    ]
    for i in range(min(max_count, len(snippets))):
        rank = base_rank + i
        results.append(RankResult(
            rank=rank,
            url=f"https://www.{domain}/keyword/{keyword.replace(' ', '-')}",
            title=f"[模拟-{engine}] {keyword} - 专业建材服务",
            snippet=snippets[i],
        ))
    return results


# ──────────────────────────── 主查询入口 ────────────────────────────

class RankChecker:
    """搜索引擎排名统一查询入口"""
    ENGINE_MAP = {
        "baidu": BaiduChecker,
        "google": GoogleChecker,
        "bing": BingChecker,
    }
    @classmethod
    def check(
        cls,
        keyword: str,
        domain: str,
        engine: str = "baidu",
        max_pages: int = 5,
    ) -> CheckResult:
        """
        查询指定关键词在指定搜索引擎的排名。

        Args:
            keyword: 搜索关键词
            domain: 目标域名（如 youding.com）
            engine: 搜索引擎 (baidu/google/bing)
            max_pages: 最大查询页数

        Returns:
            CheckResult
        """
        checker_cls = cls.ENGINE_MAP.get(engine.lower())
        if checker_cls is None:
            return CheckResult(
                keyword=keyword,
                engine=engine,
                domain=domain,
                is_simulated=True,
                error=f"不支持的搜索引擎: {engine}",
            )

        try:
            results, is_sim, error = checker_cls.search(keyword, domain, max_pages)
        except Exception as e:
            logger.error("排名检查异常 engine=%s keyword=%s: %s", engine, keyword, e)
            results, is_sim, error = [], True, str(e)

        if not results and is_sim:
            # 爬取失败 → 降级为模拟数据
            logger.info("排名查询降级为模拟数据 engine=%s keyword=%s domain=%s", engine, keyword, domain)
            mock = _generate_mock_results(keyword, domain, engine, max_count=random.randint(2, 5))
            return CheckResult(
                keyword=keyword,
                engine=engine,
                domain=domain,
                results=mock,
                is_simulated=True,
                error=error or "IP可能被搜索引擎屏蔽",
            )

        if not results:
            # 有结果但未找到匹配 → 可能未收录或排名很靠后
            return CheckResult(
                keyword=keyword,
                engine=engine,
                domain=domain,
                results=[],
                is_simulated=False,
                error="未找到排名（可能未收录或排名较靠后）",
            )

        return CheckResult(
            keyword=keyword,
            engine=engine,
            domain=domain,
            results=results,
            is_simulated=False,
        )

    @classmethod
    def batch_check(
        cls,
        keywords: List[str],
        domain: str,
        engines: Optional[List[str]] = None,
        max_pages: int = 5,
    ) -> List[CheckResult]:
        """
        批量查询关键词排名。

        Args:
            keywords: 关键词列表
            domain: 目标域名
            engines: 搜索引擎列表，默认仅百度
            max_pages: 每个关键词每引擎最大查询页数

        Returns:
            CheckResult 列表
        """
        if engines is None:
            engines = ["baidu"]

        results: List[CheckResult] = []
        for keyword in keywords:
            for engine in engines:
                result = cls.check(keyword, domain, engine, max_pages)
                results.append(result)
                # 避免请求过快
                time.sleep(random.uniform(0.5, 1.0))
        return results
