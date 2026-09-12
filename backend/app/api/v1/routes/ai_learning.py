"""AI深度学习与自我进化路由 - 模块化架构"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.response import error_response, success_response
from app.core.security import get_current_user, require_admin
from app.db.session import get_db
from app.models.user import User
from app.services.ai_learning_service import AiLearningService


# FIX-30 自动注入：保留原有的自定义前缀与标签
ROUTE_PREFIX = "/ai-learning"
ROUTE_TAGS = ["AI深度学习"]

router = APIRouter()

_auto_ab_tests: list[dict] = []
_auto_ab_seq = 1


@router.get("/")
def get_ai_learning_overview(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)):
    """获取AI学习概览"""
    return success_response(data=AiLearningService(db).overview())


@router.get("/behavior")
def get_behavior_analysis(
        period: str = "7d",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取用户行为分析（流量看板聚合，T-P2-07）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    from app.services.traffic_analytics_service import resolve_tenant_id
    tid = resolve_tenant_id(db, user=current_user)
    data = AiLearningService(db).behavior_analysis(
        tenant_id=tid,
        period=period,
    )
    return success_response(data=data)


@router.get("/conversion-funnel")
def get_conversion_funnel(
        period: str = "7d",
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取转化漏斗数据（流量看板真实埋点，非固定 mock）。"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    from app.services.traffic_analytics_service import resolve_tenant_id
    tid = resolve_tenant_id(db, user=current_user)
    data = AiLearningService(db).behavior_analysis(tenant_id=tid, period=period)
    summary = data.get("summary") or {}
    raw = data.get("conversion_funnel") or []
    visitors = int(summary.get("unique_visitors") or _count_stage(raw, "访问"))
    clicks = int(summary.get("total_clicks") or _count_stage(raw, "点击"))
    form_opens = int(summary.get("form_opens") or _count_stage(raw, "打开表单"))
    inquiries = int(summary.get("inquiries") or _count_stage(raw, "提交询盘/电话"))
    stages = [
        {"name": "访问页面", "count": visitors},
        {"name": "浏览内容", "count": clicks},
        {"name": "提交询盘", "count": form_opens},
        {"name": "成交转化", "count": inquiries},
    ]
    borders = [
        "border-blue-500",
        "border-indigo-500",
        "border-violet-500",
        "border-pink-500",
    ]
    funnel = _build_funnel(visitors, stages, borders)
    loss_reasons = _build_loss_reasons(visitors, clicks, form_opens, inquiries)
    return success_response(
        data={
            "period": period,
            "funnel": funnel,
            "loss_reasons": loss_reasons,
            "summary": summary,
            "data_source": data.get("source", "traffic_analytics_service"),
            "is_empty": visitors == 0,
            "disclaimer": "基于租户站点真实埋点；无访问时各阶段为 0",
        }
    )


def _count_stage(raw: list, stage: str, fallback: int = 0) -> int:
    """根据阶段名称从埋点数据中统计对应计数，未命中时返回兜底值。

    :param raw: 入参 (list)。
    :param stage: 入参 (str)。
    :param fallback: 入参 (int)。

    :return: 返回 int 类型的结果。
    """
    for row in raw:
        if row.get("stage") == stage:
            return int(row.get("count") or 0)
    return fallback


def _build_funnel(visitors: int, stages: list, borders: list) -> list:
    """构建转化漏斗各阶段数据，计算每个阶段的转化率、流失率与配色边框。

    :param visitors: 入参 (int)。
    :param stages: 入参 (list)。
    :param borders: 入参 (list)。

    :return: 返回 list 类型的结果。
    """
    base = visitors or 1
    funnel = []
    prev = visitors or 1
    for i, row in enumerate(stages):
        cnt = row["count"]
        rate = round(cnt / base * 100, 1) if base else 0.0
        loss = round((1 - cnt / prev) * 100) if i > 0 and prev else 0
        funnel.append(
            {
                **row,
                "rate": rate,
                "loss": max(0, loss),
                "border": borders[i],
            }
        )
        if cnt > 0:
            prev = cnt
    return funnel


def _build_loss_reasons(visitors: int, clicks: int, form_opens: int, inquiries: int) -> list:
    """根据各阶段人数生成流失原因与优化建议列表。

    :param visitors: 入参 (int)。
    :param clicks: 入参 (int)。
    :param form_opens: 入参 (int)。
    :param inquiries: 入参 (int)。

    :return: 返回 list 类型的结果。
    """
    loss_reasons: list[dict] = []
    if visitors and clicks < visitors * 0.5:
        loss_reasons.append(
            {
                "id": 1,
                "s": "访问→浏览",
                "r": "访客点击深度不足，首屏 CTA 或加载可能有问题",
                "n": visitors - clicks,
                "a": "检查移动端首屏与产品入口点击率",
            }
        )
    if clicks and form_opens < clicks * 0.3:
        loss_reasons.append(
            {
                "id": 2,
                "s": "浏览→询盘",
                "r": "浏览后未打开留资表单",
                "n": clicks - form_opens,
                "a": "产品详情补充参考价、运费说明与「获取报价」按钮",
            }
        )
    if form_opens and inquiries < form_opens:
        loss_reasons.append(
            {
                "id": 3,
                "s": "表单→提交",
                "r": "打开表单但未提交（字段过多或验证失败）",
                "n": form_opens - inquiries,
                "a": "缩短表单字段并检查必填项提示",
            }
        )
    return loss_reasons


@router.get("/auto-ab-test")
def get_auto_ab_test_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """获取A/B自动化测试状态"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    active = [t for t in _auto_ab_tests if t["s"] == "running"]
    done = [t for t in _auto_ab_tests if t["s"] == "done"]
    winners = [t for t in _auto_ab_tests if t.get("winner")]
    return success_response(
        data={
            "active_tests": len(active),
            "completed_tests": len(done),
            "winning_variants": len(winners),
            "confidence_threshold": 95,
            "tests": list(_auto_ab_tests),
        })


@router.post("/auto-ab-test")
def create_auto_ab_test(
        req: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """创建自动化A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    global _auto_ab_seq
    test = {
        "id": _auto_ab_seq,
        "n": req.get("name") or "新实验",
        "p": req.get("page") or "",
        "aRate": 0,
        "bRate": 0,
        "conf": 0,
        "s": "draft",
        "winner": "",
        "variants": f"A: {(req.get('variantA') or '')[:20]} / B: {(req.get('variantB') or '')[:20]}",
    }
    _auto_ab_seq += 1
    _auto_ab_tests.insert(0, test)
    return success_response(data=test, message="自动化A/B测试已创建")


@router.post("/auto-ab-test/{test_id}/start")
def start_auto_ab_test(
        test_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """启动自动化A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    for t in _auto_ab_tests:
        if t["id"] == test_id:
            t["s"] = "running"
            return success_response(data=t, message="实验已启动（尚无转化数据，待埋点回传）")
    return error_response(404, "实验不存在")


@router.post("/auto-ab-test/{test_id}/stop")
def stop_auto_ab_test(
        test_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)):
    """停止自动化A/B测试"""
    if current_user.role not in ["admin", "super_admin", "tenant_admin"]:
        return error_response(403, "权限不足")
    for t in _auto_ab_tests:
        if t["id"] == test_id:
            t["s"] = "done"
            if (t.get("bRate") or 0) > (t.get("aRate") or 0):
                t["winner"] = "B方案"
            elif (t.get("aRate") or 0) > 0:
                t["winner"] = "A方案"
            return success_response(data=t, message="实验已停止")
    return error_response(404, "实验不存在")
