"""获客引擎领域 — FIX-31: 首个完整领域模块迁移

包揽所有获客相关功能：
- 零成本邮箱验证（MX + SMTP）
- 网站邮箱抓取
- 邮件发送（Resend + SMTP）
- 线索管理（ProspectLead + 去重）
- 邮件外展（状态机 + 序列）
- 异步搜索
"""

from app.domains.lead.routes import router as lead_router
from app.domains.base import DomainModule


class LeadDomain(DomainModule):
    """获客引擎领域模块。

    对外接口：
    - POST /lead/search        - 搜索潜在客户
    - POST /lead/verify-email  - 验证邮箱
    - POST /lead/scrape-emails - 抓取网站邮箱
    - POST /lead/send          - 发送邮件
    - GET  /lead/prospects     - 查询线索
    - POST /lead/outreach      - 创建外展任务
    """
    name = "lead"
    label = "获客引擎"
    @property
    def router(self):
        """router。

        参数说明：
        :param self: 参数 self
        :return: 返回处理结果。
        """
        return lead_router


__all__ = ["LeadDomain"]