"""摸金校尉 · Survival 周报 — 飞书推送（全球累计 + 人格 + 大赛 Top5）。"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings
from app.services.hermes.greedy_avatar_constitution import assert_greedy_action

logger = logging.getLogger("uj-admin.greedy_survival_digest")

_MOOD_TEMPLATE = {
    "ashamed": "orange",
    "redemption": "green",
    "ambitious": "blue",
    "conquest": "purple",
}


def _webhook_url(override: str | None = None) -> str:
    """_webhook_url。

    参数说明：
    :param override: 参数 override
    :return: 返回处理结果。
    """
    return (
        (override or "").strip()
        or os.getenv("HERMES_GREEDY_DIGEST_WEBHOOK_URL", "").strip()
        or os.getenv("HERMES_ALERT_WEBHOOK_URL", "").strip()
        or os.getenv("OPS_READINESS_WEBHOOK_URL", "").strip()
        or (settings.FEISHU_WEBHOOK_URL or "").strip()
    )


def build_survival_digest_markdown() -> dict[str, Any]:
    """组装周报 Markdown 与元数据。"""
    assert_greedy_action("read_greedy_memory")
    from app.services.hermes.greedy_contest_memory_service import contest_status_summary, get_endurance_status
    from app.services.hermes.greedy_cumulative_personality_service import get_cumulative_stats, period_keys
    cumulative = get_cumulative_stats()
    status = contest_status_summary()
    endurance = get_endurance_status()
    pers = cumulative.get("personality") or {}
    display = cumulative.get("display") or {}
    mood = pers.get("mood") or "conquest"
    keys = period_keys()
    top5 = status.get("top5") or []
    lines = [
        f"**周期** {keys['week_key']} · {keys['month_key']} · {keys['year_key']}",
        f"**人格** {pers.get('codename', '摸金打江山')} · **{mood}** — {pers.get('line', '')}",
        "",
        "**全球累计（不限境内外）**",
        f"- 本周 ¥{display.get('week_cny', 0)} · 本月 ¥{display.get('month_cny', 0)} · 今年 ¥{display.get('year_cny', 0)}",
        f"- 终身 ¥{display.get('lifetime_cny', 0)} · 上次结算 ¥{display.get('prev_settlement_cny', 0)} → 本次 ¥{display.get('last_settlement_cny', 0)}",
        f"- 对比上次：{pers.get('vs_last', '—')}",
        "",
        f"**7×24 耐力赛** · {(endurance.get('current_arena') or {}).get('label', '当前擂台')}",
        f"- 距轮转 {endurance.get('days_until_rollover', '—')} 天 · protected {status.get('protected_count', 0)} · champion {status.get('champion_count', 0)}",
        "",
        "**挣钱大赛 Top5**",
    ]
    if top5:
        for i, row in enumerate(top5, 1):
            name = row.get("name") or row.get("role_id") or "—"
            score = row.get("score_arena") or row.get("score_30d") or row.get("total_score") or 0
            tier = row.get("contest_tier") or "rookie"
            prot = "🛡" if row.get("protected") else ""
            lines.append(f"{i}. {prot}{name} · {tier} · {score}分")
    else:
        lines.append("_暂无记分，跑一轮搞钱闭环后更新_")

    mojin_loops = status.get("mojin_loops")
    if mojin_loops is not None:
        lines.extend(["", f"摸金校尉已完成 **{mojin_loops}** 轮闭环"])

    body_md = "\n".join(lines)
    title = f"摸金校尉 Survival 周报 · {mood}"
    return {
        "title": title,
        "body_md": body_md,
        "mood": mood,
        "template": _MOOD_TEMPLATE.get(mood, "blue"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": keys,
        "cumulative": cumulative,
        "contest_status": status,
    }


def send_survival_digest_feishu(*, webhook_url: str | None = None, respect_cooldown: bool = False) -> dict[str, Any]:
    """发送 Survival 周报到飞书群。"""
    assert_greedy_action("emit_greedy_alert")
    digest = build_survival_digest_markdown()
    url = _webhook_url(webhook_url)
    if not url:
        return {"sent": False, "reason": "no_webhook_configured", "digest": digest}

    fp = hashlib.sha256(digest["body_md"].encode()).hexdigest()[:12]
    if respect_cooldown:
        from app.services.hermes.alert_dispatcher import should_send_alert
        if not should_send_alert("greedy_survival_digest", fp, cooldown_minutes=60 * 20):
            return {"sent": False, "reason": "cooldown", "fingerprint": fp, "digest": digest}

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": digest["title"][:120]},
                "template": digest["template"],
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": digest["body_md"][:4000]}},
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "Admin → 摸金累计 / 大赛榜 / L4 发布队列 · 全球收入均计入 survival",
                        }
                    ],
                },
            ],
        },
    }
    try:
        with httpx.Client(timeout=12) as client:
            resp = client.post(url, json=payload)
        ok = resp.status_code < 400
        if ok and respect_cooldown:
            from app.services.hermes.alert_dispatcher import mark_alert_sent
            mark_alert_sent("greedy_survival_digest", fp, cooldown_minutes=60 * 20)
        return {
            "sent": ok,
            "status_code": resp.status_code,
            "fingerprint": fp,
            "digest": digest,
            "response": resp.text[:200] if not ok else "",
        }
    except Exception as exc:
        logger.warning("Greedy survival digest feishu failed: %s", exc)
        return {"sent": False, "reason": str(exc), "digest": digest}


def is_weekly_digest_due(*, tz_name: str = "Asia/Shanghai", weekday: int = 0, hour: int = 9) -> bool:
    """周一 09:00（默认）触发窗口（±30 分钟）。"""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    if now.weekday() != weekday:
        return False
    return hour <= now.hour < hour + 1 and now.minute < 30
