import asyncio
import logging
from typing import Optional
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class Spider:
    def __init__(self, timeout: int = 30, max_concurrent: int = 5):
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers={
            "User-Agent": "Mozilla/5.0 (compatible; YoudingSEO/1.0; +https://youding.com/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        })
        return self

    async def __aexit__(self, *args):
        if self.client:
            await self.client.aclose()

    async def fetch(self, url: str) -> Optional[str]:
        async with self.semaphore:
            try:
                response = await self.client.get(url)
                response.raise_for_status()
                return response.text
            except httpx.TimeoutException:
                logger.warning(f"请求超时: {url}")
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP错误 {e.response.status_code}: {url}")
            except Exception as e:
                logger.error(f"请求失败 {url}: {e}")
            return None

    async def fetch_batch(self, urls: list[str]) -> list[dict]:
        tasks = [self._fetch_with_meta(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def _fetch_with_meta(self, url: str) -> dict:
        html = await self.fetch(url)
        if not html:
            return {"url": url, "success": False, "html": None}
        soup = BeautifulSoup(html, "html.parser")
        return {
            "url": url,
            "success": True,
            "html": html,
            "title": soup.title.string.strip() if soup.title else "",
            "meta_description": soup.find("meta", attrs={"name": "description"})["content"] if soup.find("meta", attrs={"name": "description"}) else "",
            "meta_keywords": soup.find("meta", attrs={"name": "keywords"})["content"] if soup.find("meta", attrs={"name": "keywords"}) else "",
            "text_length": len(soup.get_text(strip=True)),
        }

    def extract_links(self, html: str, base_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            full_url = href if href.startswith("http") else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
            links.append({
                "url": full_url,
                "text": a.get_text(strip=True),
                "nofollow": "nofollow" in a.get("rel", []),
                "external": not base_url.startswith(urlparse(full_url).netloc),
            })
        return links
