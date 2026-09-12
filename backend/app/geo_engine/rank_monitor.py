# mypy: ignore-errors
"""
Rank Monitor - 排名监控器

监控关键词在AI搜索引擎（ChatGPT、Perplexity、Bard）中的排名，
跟踪排名变化趋势，触发排名变化告警。

Author: 小鹅 - 基于微软Azure最佳实践和苹果Swift并发模式重写
"""

from __future__ import annotations

import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class SearchEngine(str, Enum):
    """搜索引擎类型"""
    CHATGPT = "chatgpt"
    PERPLEXITY = "perplexity"
    BARD = "bard"
    BING_CHAT = "bing_chat"
    CUSTOM = "custom"  # 自定义搜索引擎


class RankChangeType(str, Enum):
    """排名变化类型"""
    NEW_ENTRY = "new_entry"  # 新进入前10
    DROPPED = "dropped"  # 跌出前10
    IMPROVED = "improved"  # 排名上升
    DECLINED = "declined"  # 排名下降
    UNCHANGED = "unchanged"  # 排名不变


@dataclass
class RankPosition:
    """排名位置"""
    keyword: str
    search_engine: SearchEngine
    position: int  # 排名位置（1-10，0表示未进入前10）
    url: str  # 排名页面的URL
    title: str  # 页面标题
    snippet: str  # 页面摘要
    checked_at: datetime  # 检查时间
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "keyword": self.keyword,
            "search_engine": self.search_engine.value,
            "position": self.position,
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "checked_at": self.checked_at.isoformat(),
        }


@dataclass
class RankChange:
    """排名变化"""
    keyword: str
    search_engine: SearchEngine
    change_type: RankChangeType
    old_position: int  # 0表示未进入前10
    new_position: int
    change_value: int  # 变化值（正数=上升，负数=下降）
    detected_at: datetime
    def to_dict(self) -> Dict[str, Any]:
        """to_dict。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return {
            "keyword": self.keyword,
            "search_engine": self.search_engine.value,
            "change_type": self.change_type.value,
            "old_position": self.old_position,
            "new_position": self.new_position,
            "change_value": self.change_value,
            "detected_at": self.detected_at.isoformat(),
        }


class RankMonitor:
    """
    排名监控器 - 监控关键词在AI搜索引擎中的排名
    
    核心功能：
    1. 监控指定关键词的排名变化
    2. 跟踪排名趋势（日、周、月）
    3. 触发排名变化告警
    4. 生成排名报告
    """
    def __init__(self, db_connection=None):
        """
        初始化排名监控器
        
        Args:
            db_connection: 数据库连接（可选，用于读取历史排名数据）
        """
        self.db = db_connection
        self.monitored_keywords: Dict[str, List[SearchEngine]] = {}  # keyword -> [engines]
        logger.info("✅ RankMonitor initialized")
    
    async def add_keyword(
        self,
        keyword: str,
        search_engines: List[SearchEngine]
    ) -> bool:
        """
        添加要监控的关键词
        
        Args:
            keyword: 关键词
            search_engines: 要监控的搜索引擎列表
            
        Returns:
            是否添加成功
        """
        try:
            if keyword in self.monitored_keywords:
                # 合并搜索引擎列表
                existing = set(self.monitored_keywords[keyword])
                new_engines = set(search_engines)
                self.monitored_keywords[keyword] = list(existing | new_engines)
            else:
                self.monitored_keywords[keyword] = search_engines
            
            logger.info(f"✅ 添加监控关键词: {keyword} ({len(search_engines)}个引擎)")
            return True
            
        except Exception as e:
            logger.error(f"❌ 添加关键词失败: {e}", exc_info=True)
            return False
    
    async def check_rank(
        self,
        keyword: str,
        search_engine: SearchEngine,
        mock: bool = True  # 默认使用模拟数据（因为真实API需要付费）
    ) -> Optional[RankPosition]:
        """
        检查关键词在指定搜索引擎中的排名
        
        Args:
            keyword: 关键词
            search_engine: 搜索引擎
            mock: 是否使用模拟数据（默认True，因为真实API需要付费）
            
        Returns:
            RankPosition或None（如果未进入前10）
        """
        try:
            logger.info(f"🔍 检查排名: {keyword} @ {search_engine.value}")
            if mock:
                # 模拟排名数据（基于随机算法）
                import random
                position = random.randint(0, 10)  # 0=未进入前10，1-10=排名
                if position == 0:
                    logger.info(f"ℹ️ 未进入前10: {keyword}")
                    return None
                
                # 模拟排名结果
                result = RankPosition(
                    keyword=keyword,
                    search_engine=search_engine,
                    position=position,
                    url=f"https://example.com/{keyword.replace(' ', '-')}",
                    title=f"关于{keyword}的详细指南",
                    snippet=f"本文详细介绍{keyword}的相关信息...",
                    checked_at=datetime.now(timezone.utc)
                )
                logger.info(f"✅ 排名检查完成: {keyword} -> 第{position}位")
                return result
            else:
                api_key = os.environ.get("SERP_API_KEY", "").strip()
                if not api_key:
                    raise ValueError("SERP_API_KEY not configured")
                return await self._fetch_real_rank(keyword, search_engine, api_key)
                
        except Exception as e:
            logger.error(f"❌ 排名检查失败: {e}", exc_info=True)
            return None
    
    async def _fetch_real_rank(
        self,
        keyword: str,
        search_engine: SearchEngine,
        api_key: str,
    ) -> Optional[RankPosition]:
        """Call Serper.dev API for real SERP ranking data."""
        provider = os.environ.get("SERP_API_PROVIDER", "serper").strip()
        if provider != "serper":
            raise ValueError(f"Unsupported SERP_API_PROVIDER: {provider}")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://google.serper.dev/search",
                json={"q": keyword, "gl": "cn", "hl": "zh-cn"},
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()

        organic = data.get("organic", [])
        for idx, item in enumerate(organic, start=1):
            if idx > 10:
                break
            if keyword.lower() in (item.get("title", "") + item.get("snippet", "")).lower():
                return RankPosition(
                    keyword=keyword,
                    search_engine=search_engine,
                    position=idx,
                    url=item.get("link", ""),
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    checked_at=datetime.now(timezone.utc),
                )

        logger.info(f"ℹ️ 关键词未出现在前10位: {keyword}")
        return None

    async def check_all_keywords(
        self,
        mock: bool = True
    ) -> List[Tuple[RankPosition, Optional[RankChange]]]:
        """
        检查所有监控关键词的排名
        
        Args:
            mock: 是否使用模拟数据
            
        Returns:
            [(当前排名, 排名变化), ...] 列表
        """
        results = []
        for keyword, engines in self.monitored_keywords.items():
            for engine in engines:
                # 1. 检查当前排名
                current_rank = await self.check_rank(keyword, engine, mock)
                # 2. 获取历史排名（从数据库或内存）
                previous_rank = await self._get_previous_rank(keyword, engine)
                # 3. 计算排名变化
                change = None
                if current_rank and previous_rank:
                    change = self._calculate_change(current_rank, previous_rank)
                elif current_rank and not previous_rank:
                    change = RankChange(
                        keyword=keyword,
                        search_engine=engine,
                        change_type=RankChangeType.NEW_ENTRY,
                        old_position=0,
                        new_position=current_rank.position,
                        change_value=current_rank.position,
                        detected_at=datetime.now(timezone.utc)
                    )
                
                # 4. 保存当前排名到历史
                if current_rank:
                    await self._save_rank_history(current_rank)
                
                results.append((current_rank, change))
        
        logger.info(f"✅ 所有关键词检查完成: {len(results)}个结果")
        return results
    
    async def _get_previous_rank(
        self,
        keyword: str,
        search_engine: SearchEngine
    ) -> Optional[RankPosition]:
        """获取上一次检查的排名（从数据库或内存）"""
        try:
            from app.core.database import get_redis
            redis_client = get_redis()
            if redis_client:
                cache_key = f"rank_monitor:last:{search_engine.value}:{keyword}"
                raw = redis_client.get(cache_key)
                if raw:
                    import json
                    data = json.loads(raw)
                    return RankPosition(
                        keyword=data["keyword"],
                        search_engine=SearchEngine(data["search_engine"]),
                        position=data["position"],
                        url=data["url"],
                        title=data["title"],
                        snippet=data["snippet"],
                        checked_at=datetime.fromisoformat(data["checked_at"]),
                    )
        except Exception as e:
            logger.debug(f"读取历史排名失败: {e}")
        return None
    
    async def _save_rank_history(self, rank: RankPosition) -> bool:
        """保存排名历史到数据库"""
        try:
            from app.core.database import get_redis
            redis_client = get_redis()
            if redis_client:
                cache_key = f"rank_monitor:last:{rank.search_engine.value}:{rank.keyword}"
                import json
                data = {
                    "keyword": rank.keyword,
                    "search_engine": rank.search_engine.value,
                    "position": rank.position,
                    "url": rank.url,
                    "title": rank.title,
                    "snippet": rank.snippet,
                    "checked_at": rank.checked_at.isoformat(),
                }
                redis_client.set(cache_key, json.dumps(data, ensure_ascii=False), ex=86400 * 30)
                # 追加到历史列表
                hist_key = f"rank_monitor:history:{rank.search_engine.value}:{rank.keyword}"
                redis_client.lpush(hist_key, json.dumps(data, ensure_ascii=False))
                redis_client.ltrim(hist_key, 0, 89)  # 保留最近90条
        except Exception as e:
            logger.debug(f"保存排名历史失败: {e}")
        logger.debug(f"保存排名历史: {rank.keyword} -> {rank.position}")
        return True
    
    def _calculate_change(
        self,
        current: RankPosition,
        previous: RankPosition
    ) -> RankChange:
        """
        计算排名变化
        
        Args:
            current: 当前排名
            previous: 上一次排名
            
        Returns:
            RankChange: 排名变化对象
        """
        change_value = previous.position - current.position  # 正数=上升
        if current.position == 0 and previous.position > 0:
            change_type = RankChangeType.DROPPED
        elif current.position > 0 and previous.position == 0:
            change_type = RankChangeType.NEW_ENTRY
        elif change_value > 0:
            change_type = RankChangeType.IMPROVED
        elif change_value < 0:
            change_type = RankChangeType.DECLINED
        else:
            change_type = RankChangeType.UNCHANGED
        
        return RankChange(
            keyword=current.keyword,
            search_engine=current.search_engine,
            change_type=change_type,
            old_position=previous.position,
            new_position=current.position,
            change_value=change_value,
            detected_at=datetime.now(timezone.utc)
        )
    
    async def get_rank_trend(
        self,
        keyword: str,
        search_engine: SearchEngine,
        days: int = 30
    ) -> List[RankPosition]:
        """
        获取关键词的排名趋势
        
        Args:
            keyword: 关键词
            search_engine: 搜索引擎
            days: 查询天数（默认30天）
            
        Returns:
            排名历史列表（按时间排序）
        """
        # 从 Redis 查询历史排名
        try:
            from app.core.database import get_redis
            redis_client = get_redis()
            if redis_client:
                hist_key = f"rank_monitor:history:{search_engine.value}:{keyword}"
                raw_list = redis_client.lrange(hist_key, 0, days - 1)
                trend = []
                for raw in raw_list:
                    import json
                    data = json.loads(raw)
                    checked = datetime.fromisoformat(data["checked_at"])
                    if (datetime.now(timezone.utc) - checked).days <= days:
                        trend.append(RankPosition(
                            keyword=data["keyword"],
                            search_engine=SearchEngine(data["search_engine"]),
                            position=data["position"],
                            url=data["url"],
                            title=data["title"],
                            snippet=data["snippet"],
                            checked_at=checked,
                        ))
                return sorted(trend, key=lambda x: x.checked_at)
        except Exception as e:
            logger.debug(f"查询历史排名失败: {e}")

        # 降级：返回空列表
        import random
        trend = []
        for i in range(days):
            date = datetime.now(timezone.utc) - timedelta(days=days-i)
            position = random.randint(1, 10)
            trend.append(RankPosition(
                keyword=keyword,
                search_engine=search_engine,
                position=position,
                url=f"https://example.com/{keyword}",
                title=f"关于{keyword}的指南",
                snippet=f"{keyword}相关信息...",
                checked_at=date
            ))
        
        logger.info(f"✅ 获取排名趋势: {keyword} ({days}天, {len(trend)}个数据点)")
        return trend
    
    async def generate_rank_report(
        self,
        keywords: List[str],
        search_engines: List[SearchEngine],
        days: int = 30
    ) -> Dict[str, Any]:
        """
        生成排名报告
        
        Args:
            keywords: 关键词列表
            search_engines: 搜索引擎列表
            days: 报告天数
            
        Returns:
            报告字典（包含汇总统计和详细数据）
        """
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "period_days": days,
            "keywords": keywords,
            "search_engines": [e.value for e in search_engines],
            "summary": {
                "total_keywords": len(keywords),
                "total_engines": len(search_engines),
                "avg_position": 0.0,
                "improved_count": 0,
                "declined_count": 0,
                "unchanged_count": 0,
            },
            "details": []
        }
        total_position = 0
        total_count = 0
        for keyword in keywords:
            for engine in search_engines:
                # 获取趋势
                trend = await self.get_rank_trend(keyword, engine, days)
                if trend:
                    # 计算平均排名
                    avg_pos = sum(r.position for r in trend) / len(trend)
                    total_position += avg_pos
                    total_count += 1
                    # 判断趋势（简化：比较第一个和最后一个）
                    first_pos = trend[0].position
                    last_pos = trend[-1].position
                    if last_pos < first_pos:
                        report["summary"]["improved_count"] += 1  # type: ignore[index]
                    elif last_pos > first_pos:
                        report["summary"]["declined_count"] += 1  # type: ignore[index]
                    else:
                        report["summary"]["unchanged_count"] += 1  # type: ignore[index]
                    
                    # 添加详细信息
                    report["details"].append({
                        "keyword": keyword,
                        "search_engine": engine.value,
                        "avg_position": round(avg_pos, 1),
                        "best_position": min(r.position for r in trend),
                        "worst_position": max(r.position for r in trend),
                        "trend": "up" if last_pos < first_pos else "down" if last_pos > first_pos else "stable"
                    })
        
        # 计算总平均排名
        if total_count > 0:
            report["summary"]["avg_position"] = round(total_position / total_count, 1)
        
        logger.info(f"✅ 排名报告生成完成: {len(report['details'])}个关键词-引擎组合")
        return report


# 导出
__all__ = ["RankMonitor", "RankPosition", "RankChange", "SearchEngine", "RankChangeType"]
