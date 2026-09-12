"""百度搜索资源平台（站长平台）API 集成服务"""
from typing import Any, Optional

import httpx

from app.core.no_fake_delivery import mock_allowed, stamp_mock


class BaiduWebmasterService:
    """百度站长平台：sitemap 提交 / 收录查询 / 搜索词分析

    使用百度搜索资源平台 API：
    - Sitemap 提交: https://api.baidu.com/api/sitemap/add
    - 索引量查询: https://api.baidu.com/api/indexs/count
    - 搜索词分析: https://api.baidu.com/api/searchWord/count

    注意：百度 API 需要真实的 site_token 和站点验证才能对接。
         无 token 时仅开发环境可返回显式 mock（mode=mock），生产须配置 token。
    """
    API_BASE = "https://api.baidu.com/api"
    # ---------- 模拟数据 ----------
    _MOCK_INDEX_COUNT = {
        "total_index": 1280,
        "daily_change": 12,
        "today_crawl": 45,
        "crawl_frequency": "正常",
        "last_crawl_time": "2026-05-21 08:30:00",
    }
    _MOCK_SEARCH_QUERIES = [
        {"keyword": "轻集料混凝土", "impressions": 4560, "clicks": 189, "ctr": 4.14, "position": 3.2},
        {"keyword": "保温建材厂家", "impressions": 2340, "clicks": 98, "ctr": 4.19, "position": 5.1},
        {"keyword": "陶粒混凝土价格", "impressions": 1890, "clicks": 76, "ctr": 4.02, "position": 4.5},
        {"keyword": "轻质混凝土施工", "impressions": 1340, "clicks": 55, "ctr": 4.10, "position": 6.8},
        {"keyword": "泡沫混凝土配合比", "impressions": 980, "clicks": 41, "ctr": 4.18, "position": 7.3},
        {"keyword": "保温隔热材料", "impressions": 870, "clicks": 35, "ctr": 4.02, "position": 8.0},
        {"keyword": "建筑节能方案", "impressions": 650, "clicks": 28, "ctr": 4.31, "position": 9.1},
        {"keyword": "外墙保温施工", "impressions": 520, "clicks": 22, "ctr": 4.23, "position": 10.2},
    ]
    @staticmethod
    def _no_token_response(*, mock_payload: dict[str, Any]) -> dict[str, Any]:
        """_no_token_response。

        参数说明：
        :param mock_payload: 参数 mock_payload
        :return: 返回处理结果。
        """
        if not mock_allowed("BAIDU_WEBMASTER_ALLOW_MOCK"):
            return {
                "success": False,
                "message": "百度站长 token 未配置",
                "data": None,
                "error_code": "BAIDU_TOKEN_NOT_CONFIGURED",
            }
        return {
            "success": True,
            "message": "[dev mock] 需配置百度站长 token 后对接真实 API",
            "data": stamp_mock(dict(mock_payload), reason="baidu_token_missing"),
        }

    @staticmethod
    async def submit_sitemap(
        site_url: str,
        sitemap_url: str,
        token: Optional[str] = None,
    ) -> dict[str, Any]:
        """提交 sitemap 到百度搜索资源平台。

        Args:
            site_url: 站点 URL（如 https://youding.com）
            sitemap_url: sitemap 完整 URL
            token: 百度站长平台的 site_token，为空时返回模拟数据

        Returns:
            {"success": bool, "message": str, "data": dict}
        """
        if not token:
            return BaiduWebmasterService._no_token_response(
                mock_payload={
                    "remain": 99,
                    "success": 1,
                    "site_url": site_url,
                    "sitemap_url": sitemap_url,
                }
            )

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.post(
                    f"{BaiduWebmasterService.API_BASE}/sitemap/add",
                    json={
                        "site": site_url,
                        "sitemap": sitemap_url,
                        "token": token,
                    },
                )
                resp.raise_for_status()
                return {"success": True, "data": resp.json()}
            except httpx.HTTPError as exc:
                return {"success": False, "message": f"百度API请求失败: {exc}", "data": None}

    @staticmethod
    async def get_index_count(
        site_url: str,
        token: Optional[str] = None,
    ) -> dict[str, Any]:
        """查询百度索引量。

        Args:
            site_url: 站点 URL
            token: 百度站长平台的 site_token，为空时返回模拟数据
        """
        if not token:
            return BaiduWebmasterService._no_token_response(
                mock_payload=dict(BaiduWebmasterService._MOCK_INDEX_COUNT)
            )

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{BaiduWebmasterService.API_BASE}/indexs/count",
                    params={"site": site_url, "token": token},
                )
                resp.raise_for_status()
                return {"success": True, "data": resp.json()}
            except httpx.HTTPError as exc:
                return {"success": False, "message": f"百度API请求失败: {exc}", "data": None}

    @staticmethod
    async def get_search_queries(
        site_url: str,
        token: Optional[str] = None,
        days: int = 30,
    ) -> dict[str, Any]:
        """获取百度搜索词数据（流量与关键词）。

        Args:
            site_url: 站点 URL
            token: 百度站长平台的 site_token，为空时返回模拟数据
            days: 统计天数，默认 30
        """
        if not token:
            return BaiduWebmasterService._no_token_response(
                mock_payload={
                    "total_impressions": sum(q["impressions"] for q in BaiduWebmasterService._MOCK_SEARCH_QUERIES),
                    "total_clicks": sum(q["clicks"] for q in BaiduWebmasterService._MOCK_SEARCH_QUERIES),
                    "avg_ctr": round(
                        sum(q["impressions"] * q["ctr"] for q in BaiduWebmasterService._MOCK_SEARCH_QUERIES)
                        / sum(q["impressions"] for q in BaiduWebmasterService._MOCK_SEARCH_QUERIES),
                        2,
                    ),
                    "days": days,
                    "queries": BaiduWebmasterService._MOCK_SEARCH_QUERIES,
                }
            )

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(
                    f"{BaiduWebmasterService.API_BASE}/searchWord/count",
                    params={"site": site_url, "token": token, "days": days},
                )
                resp.raise_for_status()
                return {"success": True, "data": resp.json()}
            except httpx.HTTPError as exc:
                return {"success": False, "message": f"百度API请求失败: {exc}", "data": None}
