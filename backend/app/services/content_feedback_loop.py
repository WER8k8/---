"""内容反馈闭环 — publish -> rank probe -> feedback -> adjust tactics

Content Feedback Loop (CFL):
  Content Published -> GEO/SEO Probe (3 days later) ->
    If indexed: record success pattern -> reinforce tactics
    If not indexed: record failure pattern -> adjust tactics
    If rank improved: boost similar content
    If rank declined: trigger content refresh
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.content_feedback import ContentFeedbackCheck, IndustryPattern

logger = logging.getLogger("uj-admin.content_feedback_loop")

# ──────────────────────────────────────────────
# Tactics changelog path
# ──────────────────────────────────────────────

_TACTICS_CHANGELOG_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "tactics_changelog.json"
)


def _ensure_changelog_file() -> Path:
    """_ensure_changelog_file。
    :return: 返回处理结果。
    """
    _TACTICS_CHANGELOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _TACTICS_CHANGELOG_PATH.exists():
        _TACTICS_CHANGELOG_PATH.write_text(
            json.dumps({"entries": []}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return _TACTICS_CHANGELOG_PATH


def _append_changelog(entry: dict[str, Any]) -> None:
    """_append_changelog。

    参数说明：
    :param entry: 参数 entry
    :return: 返回处理结果。
    """
    path = _ensure_changelog_file()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = {"entries": []}
    data["entries"].append(entry)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


# ──────────────────────────────────────────────
# Rank check helpers
# ──────────────────────────────────────────────


def _probe_inclusion_rank(
    publish_url: str, keyword: str = "", engine: str = "baidu"
) -> dict[str, Any]:
    """Probe whether a published URL is indexed and its rank position.

    Returns dict with keys: is_indexed, rank_position, engine, checked_at, error.
    Falls back gracefully when the rank checker is unavailable.
    """
    from urllib.parse import urlparse
    domain = urlparse(publish_url).netloc or ""
    checked_at = datetime.now(timezone.utc).isoformat()
    try:
        from app.services.rank_checker import RankChecker
        kw = keyword or domain.split(".")[0]
        result = RankChecker.check(kw, domain, engine, max_pages=5)
        is_included = result.best_rank is not None and result.best_rank > 0
        return {
            "is_indexed": is_included,
            "rank_position": result.best_rank,
            "engine": engine,
            "checked_at": checked_at,
            "error": None,
        }
    except Exception as exc:
        logger.warning("inclusion probe failed url=%s: %s", publish_url, exc)
        return {
            "is_indexed": False,
            "rank_position": None,
            "engine": engine,
            "checked_at": checked_at,
            "error": str(exc)[:300],
        }


# ──────────────────────────────────────────────
# Core service
# ──────────────────────────────────────────────


class ContentFeedbackLoop:
    """Closed-loop content quality feedback system.

    Flow: publish -> schedule check -> probe rank -> analyze -> adjust tactics.
    """
    def __init__(self, db: Session):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param db: 参数 db
        :return: 返回处理结果。
        """
        self.db = db

    # ── 1. Schedule a feedback check ──────────
    def schedule_feedback_check(
        self,
        content_id: str,
        publish_url: str,
        *,
        platform: str = "",
        tenant_id: str = "",
        keyword: str = "",
        tactics_version: str = "",
        check_after_days: int = 3,
    ) -> ContentFeedbackCheck:
        """Store a pending feedback check for a published content piece."""
        now = datetime.now(timezone.utc)
        check = ContentFeedbackCheck(
            id=str(uuid.uuid4()),
            content_id=content_id,
            publish_url=publish_url,
            platform=platform,
            tenant_id=tenant_id,
            keyword=keyword,
            tactics_version=tactics_version,
            status="pending",
            check_at=now + timedelta(days=check_after_days),
            created_at=now,
            updated_at=now,
        )
        self.db.add(check)
        self.db.commit()
        self.db.refresh(check)
        logger.info(
            "scheduled feedback check content=%s url=%s check_at=%s",
            content_id,
            publish_url,
            check.check_at.isoformat(),
        )
        return check

    # ── 2. Run pending checks ─────────────────
    def run_pending_checks(self) -> list[dict[str, Any]]:
        """Query all checks where check_at <= now and status = pending.

        For each: probe inclusion/rank, compare with previous rank,
        update the check record, return results.
        """
        now = datetime.now(timezone.utc)
        pending: list[ContentFeedbackCheck] = (
            self.db.query(ContentFeedbackCheck)
            .filter(
                and_(
                    ContentFeedbackCheck.status == "pending",
                    ContentFeedbackCheck.check_at <= now,
                )
            )
            .all()
        )
        results: list[dict[str, Any]] = []
        for check in pending:
            result = self._process_single_check(check)
            results.append(result)

        if results:
            self.db.commit()

        return results

    def _process_single_check(self, check: ContentFeedbackCheck) -> dict[str, Any]:
        """_process_single_check。

        参数说明：
        :param self: 参数 self
        :param check: 参数 check
        :return: 返回处理结果。
        """
        now = datetime.now(timezone.utc)
        # Probe current inclusion / rank
        probe = _probe_inclusion_rank(
            check.publish_url,
            keyword=check.keyword or "",
        )
        # Look for previous check to compare rank
        previous_rank: Optional[int] = None
        prev_check: Optional[ContentFeedbackCheck] = (
            self.db.query(ContentFeedbackCheck)
            .filter(
                and_(
                    ContentFeedbackCheck.content_id == check.content_id,
                    ContentFeedbackCheck.status == "checked",
                    ContentFeedbackCheck.id != check.id,
                )
            )
            .order_by(ContentFeedbackCheck.checked_at.desc())
            .first()
        )
        if prev_check and prev_check.rank_position is not None:
            previous_rank = prev_check.rank_position

        # Compute rank change
        rank_change: Optional[int] = None
        if probe["rank_position"] is not None and previous_rank is not None:
            # Negative means rank improved (lower position number = better)
            rank_change = previous_rank - probe["rank_position"]

        # Update check record
        check.status = "checked"
        check.checked_at = now
        check.is_indexed = probe["is_indexed"]
        check.rank_position = probe["rank_position"]
        check.rank_change = rank_change
        check.probe_error = probe.get("error")
        check.check_meta = {
            "engine": probe.get("engine"),
            "previous_rank": previous_rank,
        }
        check.updated_at = now
        return {
            "check_id": check.id,
            "content_id": check.content_id,
            "publish_url": check.publish_url,
            "platform": check.platform,
            "tenant_id": check.tenant_id,
            "is_indexed": probe["is_indexed"],
            "rank_position": probe["rank_position"],
            "previous_rank": previous_rank,
            "rank_change": rank_change,
            "tactics_version": check.tactics_version,
            "probe_error": probe.get("error"),
        }

    # ── 3. Analyze and adjust ─────────────────
    def analyze_and_adjust(
        self, results: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyze probe results and adjust tactics accordingly.

        Actions:
          - Newly indexed -> record as success pattern in industry_patterns
          - Not indexed after 7 days -> flag for content refresh
          - Rank improved -> boost the writing tactic version used
          - Rank declined -> suggest content refresh with updated tactics
        """
        now = datetime.now(timezone.utc)
        actions: list[dict[str, Any]] = []
        success_count = 0
        refresh_count = 0
        boost_count = 0
        for r in results:
            content_id = r["content_id"]
            is_indexed = r["is_indexed"]
            rank_change = r["rank_change"]
            tactics_version = r.get("tactics_version", "")
            if is_indexed and (r["previous_rank"] is None):
                # Newly indexed — record success pattern
                self._record_success_pattern(r)
                success_count += 1
                actions.append({
                    "content_id": content_id,
                    "action": "indexed_success",
                    "detail": "Content newly indexed; success pattern recorded.",
                })

            if not is_indexed:
                # Check if it's been 7+ days since publish
                check = self.db.query(ContentFeedbackCheck).filter(
                    ContentFeedbackCheck.id == r["check_id"]
                ).first()
                if check:
                    age_days = (now - check.created_at).days
                    if age_days >= 7:
                        self._flag_content_refresh(check, reason="not_indexed_7d")
                        refresh_count += 1
                        actions.append({
                            "content_id": content_id,
                            "action": "flag_refresh",
                            "detail": f"Not indexed after {age_days} days; flagged for content refresh.",
                        })

            if rank_change is not None:
                if rank_change > 0:
                    # Rank improved — boost this tactic version
                    self._record_success_pattern(r)
                    self._boost_tactic_version(tactics_version, r)
                    boost_count += 1
                    actions.append({
                        "content_id": content_id,
                        "action": "tactic_boost",
                        "detail": f"Rank improved by {rank_change} positions; tactic {tactics_version} boosted.",
                    })
                elif rank_change < 0:
                    # Rank declined — suggest refresh
                    self._flag_content_refresh(
                        self.db.query(ContentFeedbackCheck).filter(
                            ContentFeedbackCheck.id == r["check_id"]
                        ).first(),
                        reason="rank_declined",
                    )
                    refresh_count += 1
                    actions.append({
                        "content_id": content_id,
                        "action": "suggest_refresh",
                        "detail": f"Rank declined by {abs(rank_change)} positions; content refresh suggested.",
                    })

        # Auto-update tactics_changelog.json
        if actions:
            _append_changelog({
                "timestamp": now.isoformat(),
                "action_count": len(actions),
                "success_count": success_count,
                "refresh_count": refresh_count,
                "boost_count": boost_count,
                "actions": actions,
            })

        self.db.commit()
        return {
            "analyzed": len(results),
            "success_patterns_recorded": success_count,
            "refresh_triggered": refresh_count,
            "tactics_boosted": boost_count,
            "actions": actions,
        }

    def _record_success_pattern(self, result: dict[str, Any]) -> None:
        """Store a success pattern in the industry_patterns table."""
        now = datetime.now(timezone.utc)
        pattern = IndustryPattern(
            id=str(uuid.uuid4()),
            tenant_id=result.get("tenant_id", ""),
            content_id=result["content_id"],
            publish_url=result["publish_url"],
            platform=result.get("platform", ""),
            pattern_type="success",
            tactics_version=result.get("tactics_version", ""),
            rank_position=result.get("rank_position"),
            rank_change=result.get("rank_change"),
            details={
                "is_indexed": result.get("is_indexed"),
                "probe_error": result.get("probe_error"),
            },
            created_at=now,
            updated_at=now,
        )
        self.db.add(pattern)

    def _flag_content_refresh(
        self, check: Optional[ContentFeedbackCheck], reason: str
    ) -> None:
        """Record a failure pattern and mark content as needing refresh."""
        if check is None:
            return
        now = datetime.now(timezone.utc)
        check.refresh_suggested = True
        check.refresh_reason = reason
        check.updated_at = now
        pattern = IndustryPattern(
            id=str(uuid.uuid4()),
            tenant_id=check.tenant_id or "",
            content_id=check.content_id,
            publish_url=check.publish_url,
            platform=check.platform or "",
            pattern_type="failure",
            tactics_version=check.tactics_version or "",
            rank_position=check.rank_position,
            rank_change=check.rank_change,
            details={"reason": reason},
            created_at=now,
            updated_at=now,
        )
        self.db.add(pattern)

    def _boost_tactic_version(
        self, tactics_version: str, result: dict[str, Any]
    ) -> None:
        """Boost a tactic version score in industry_patterns."""
        now = datetime.now(timezone.utc)
        pattern = IndustryPattern(
            id=str(uuid.uuid4()),
            tenant_id=result.get("tenant_id", ""),
            content_id=result["content_id"],
            publish_url=result["publish_url"],
            platform=result.get("platform", ""),
            pattern_type="boost",
            tactics_version=tactics_version,
            rank_position=result.get("rank_position"),
            rank_change=result.get("rank_change"),
            details={
                "boost_reason": "rank_improved",
                "rank_improvement": result.get("rank_change"),
            },
            created_at=now,
            updated_at=now,
        )
        self.db.add(pattern)

    # ── 4. Feedback summary ───────────────────
    def _query_avg_rank_change(self, tenant_id: str, since) -> float:
        """查询窗口内的平均排名变化（仅统计非 None）。"""
        avg_rank_change_raw = (
            self.db.query(func.avg(ContentFeedbackCheck.rank_change))
            .filter(
                and_(
                    ContentFeedbackCheck.tenant_id == tenant_id,
                    ContentFeedbackCheck.created_at >= since,
                    ContentFeedbackCheck.rank_change.isnot(None),  # type: ignore[attr-defined]
                )
            )
            .scalar()
        )
        return round(float(avg_rank_change_raw), 2) if avg_rank_change_raw is not None else 0.0

    def _query_top_performing(self, tenant_id: str, since):
        """查询表现最佳的内容（排名提升最大）。"""
        return (
            self.db.query(ContentFeedbackCheck)
            .filter(
                and_(
                    ContentFeedbackCheck.tenant_id == tenant_id,
                    ContentFeedbackCheck.created_at >= since,
                    ContentFeedbackCheck.rank_change.isnot(None),  # type: ignore[attr-defined]
                    ContentFeedbackCheck.is_indexed.is_(True),  # type: ignore[attr-defined]
                )
            )
            .order_by(ContentFeedbackCheck.rank_change.desc())
            .limit(5)
            .all()
        )

    def _query_underperforming(self, tenant_id: str, since):
        """查询表现不佳的内容（排名下降或未收录）。"""
        return (
            self.db.query(ContentFeedbackCheck)
            .filter(
                and_(
                    ContentFeedbackCheck.tenant_id == tenant_id,
                    ContentFeedbackCheck.created_at >= since,
                    ContentFeedbackCheck.refresh_suggested.is_(True),  # type: ignore[attr-defined]
                )
            )
            .order_by(ContentFeedbackCheck.updated_at.desc())
            .limit(5)
            .all()
        )

    def get_feedback_summary(
        self, tenant_id: str, days: int = 30
    ) -> dict[str, Any]:
        """Return a summary of content feedback loop performance.

        Includes: total published, indexed count, index rate,
        average rank change, top performing content, underperforming content.
        """
        now = datetime.now(timezone.utc)
        since = now - timedelta(days=days)
        # Base query scoped to tenant and time window
        base_q = self.db.query(ContentFeedbackCheck).filter(
            and_(
                ContentFeedbackCheck.tenant_id == tenant_id,
                ContentFeedbackCheck.created_at >= since,
            )
        )
        total_published = base_q.count()
        checked_q = base_q.filter(ContentFeedbackCheck.status == "checked")
        total_checked = checked_q.count()
        indexed_count = checked_q.filter(
            ContentFeedbackCheck.is_indexed.is_(True)  # type: ignore[attr-defined]
        ).count()
        index_rate = round(indexed_count / total_checked, 4) if total_checked else 0.0
        avg_rank_change = self._query_avg_rank_change(tenant_id, since)
        top_performing = self._query_top_performing(tenant_id, since)
        underperforming = self._query_underperforming(tenant_id, since)
        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_published": total_published,
            "total_checked": total_checked,
            "indexed_count": indexed_count,
            "index_rate": index_rate,
            "avg_rank_change": avg_rank_change,
            "top_performing": [
                {
                    "check_id": str(c.id),
                    "content_id": str(c.content_id),
                    "publish_url": c.publish_url,
                    "platform": c.platform,
                    "rank_position": c.rank_position,
                    "rank_change": c.rank_change,
                    "tactics_version": c.tactics_version,
                }
                for c in top_performing
            ],
            "underperforming": [
                {
                    "check_id": str(c.id),
                    "content_id": str(c.content_id),
                    "publish_url": c.publish_url,
                    "platform": c.platform,
                    "is_indexed": c.is_indexed,
                    "rank_position": c.rank_position,
                    "refresh_reason": c.refresh_reason,
                    "tactics_version": c.tactics_version,
                }
                for c in underperforming
            ],
        }
