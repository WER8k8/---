"""
关键词排名追踪服务 - Phase 4
用于追踪百度、360、搜狗等搜索引擎的关键词排名
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from sqlalchemy.orm import Session

from app.models.seo import KeywordRanking, Keyword as KeywordModel
from app.core.database import get_db

logger = logging.getLogger(__name__)


@dataclass
class KeywordData:
    """关键词数据"""
    keyword: str
    search_engine: str  # baidu, 360, sogou, google
    target_position: int
    current_position: Optional[int] = None
    previous_position: Optional[int] = None
    search_volume: int = 0
    difficulty: str = "medium"  # easy, medium, hard
    url: str = ""
    last_checked: Optional[datetime] = None


class KeywordTracker:
    """关键词排名追踪器"""

    def __init__(self, db: Session):
        self.db = db
        self.user_agents = {
            "baidu": "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
            "360": "Mozilla/5.0 (compatible; 360Spider; +http://www.so.com/help/spider.html)",
            "sogou": "Mozilla/5.0 (compatible; Sogou web spider/4.0; +http://www.sogou.com/docs/help/webmasters.htm)",
            "google": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }

    async def check_keyword_ranking(
        self,
        keyword: str,
        search_engine: str = "baidu",
        max_pages: int = 10
    ) -> Optional[int]:
        """
        检查关键词排名

        Args:
            keyword: 搜索关键词
            search_engine: 搜索引擎 (baidu, 360, sogou, google)
            max_pages: 最大检查页数

        Returns:
            排名位置，未找到返回None
        """
        try:
            headers = {
                "User-Agent": self.user_agents.get(search_engine, self.user_agents["baidu"]),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            }

            # 构建搜索URL
            search_url = self._get_search_url(search_engine, keyword)

            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.warning(f"搜索请求失败: {search_engine} - {keyword}, 状态码: {response.status}")
                        return None

                    html = await response.text()

                    # 解析排名（简化版，实际需要更复杂的HTML解析）
                    position = self._parse_ranking(html, keyword, search_engine)

                    return position

        except Exception as e:
            logger.error(f"检查关键词排名失败: {keyword}, 错误: {str(e)}")
            return None

    def _get_search_url(self, search_engine: str, keyword: str) -> str:
        """获取搜索引擎URL"""
        from urllib.parse import quote

        encoded_keyword = quote(keyword)

        urls = {
            "baidu": f"https://www.baidu.com/s?wd={encoded_keyword}",
            "360": f"https://www.so.com/s?q={encoded_keyword}",
            "sogou": f"https://www.sogou.com/web?query={encoded_keyword}",
            "google": f"https://www.google.com/search?q={encoded_keyword}"
        }

        return urls.get(search_engine, urls["baidu"])

    def _parse_ranking(self, html: str, keyword: str, search_engine: str) -> Optional[int]:
        """
        解析排名位置

        注意：这是一个简化实现，实际生产环境需要使用专门的SERP API
        如百度站长平台API、第三方SEO工具API等
        """
        # 这里需要根据不同搜索引擎的HTML结构进行解析
        # 建议使用官方API或第三方SERP API服务

        # 示例：查找包含目标域名的结果
        target_domain = "youding.com"

        if target_domain in html:
            # 简化逻辑：假设找到就是前10名
            return 1

        return None

    async def track_keywords(
        self,
        keywords: List[str],
        search_engine: str = "baidu"
    ) -> List[Dict]:
        """
        批量追踪关键词排名

        Args:
            keywords: 关键词列表
            search_engine: 搜索引擎

        Returns:
            排名结果列表
        """
        results = []

        for keyword in keywords:
            position = await self.check_keyword_ranking(keyword, search_engine)

            result = {
                "keyword": keyword,
                "search_engine": search_engine,
                "position": position,
                "checked_at": datetime.utcnow().isoformat()
            }

            results.append(result)

            # 保存历史记录
            self._save_ranking_history(keyword, search_engine, position)

            # 避免请求过快，添加延迟
            await asyncio.sleep(2)

        return results

    def _save_ranking_history(
        self,
        keyword: str,
        search_engine: str,
        position: Optional[int]
    ):
        """保存排名历史记录"""
        try:
            history = KeywordRankingHistory(
                keyword=keyword,
                search_engine=search_engine,
                position=position,
                checked_at=datetime.utcnow()
            )

            self.db.add(history)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"保存排名历史失败: {str(e)}")

    def get_ranking_trend(
        self,
        keyword: str,
        days: int = 30
    ) -> List[Dict]:
        """
        获取排名趋势

        Args:
            keyword: 关键词
            days: 天数

        Returns:
            趋势数据列表
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        histories = self.db.query(KeywordRankingHistory).filter(
            KeywordRankingHistory.keyword == keyword,
            KeywordRankingHistory.checked_at >= start_date,
            KeywordRankingHistory.checked_at <= end_date
        ).order_by(KeywordRankingHistory.checked_at).all()

        return [
            {
                "date": h.checked_at.strftime("%Y-%m-%d"),
                "position": h.position
            }
            for h in histories
        ]


# 默认关键词列表 - 轻集料混凝土行业
DEFAULT_KEYWORDS = [
    "轻集料混凝土",
    "LC5.0轻集料混凝土",
    "LC7.5轻集料混凝土",
    "LC10轻集料混凝土",
    "LC15轻集料混凝土",
    "LC20轻集料混凝土",
    "轻质混凝土",
    "泡沫混凝土",
    "陶粒混凝土",
    "保温混凝土",
    "A型轻集料混凝土",
    "B型轻集料混凝土",
    "干拌复合轻集料混凝土",
    "现浇泡沫混凝土",
    "轻集料混凝土价格",
    "轻集料混凝土厂家",
    "轻集料混凝土施工",
    "屋面找坡轻集料混凝土",
    "地面垫层轻集料混凝土",
    "墙体保温轻集料混凝土",
]


async def main():
    """测试运行"""
    from app.core.database import SessionLocal

    db = SessionLocal()
    tracker = KeywordTracker(db)

    print("开始追踪关键词排名...")
    results = await tracker.track_keywords(DEFAULT_KEYWORDS[:5], "baidu")

    for result in results:
        position_str = f"第{result['position']}名" if result['position'] else "未收录"
        print(f"  {result['keyword']}: {position_str}")

    db.close()


if __name__ == "__main__":
    asyncio.run(main())
