# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""模块5 · M1 五个发布面方法 —— 配对反证测试（契约 §7）。

配对反证（缺任一侧 = 空真）：
- **负向**：未配租户凭据 → `task_count==0`、`skipped.reason==credential_missing`、
  `publish_tasks` **不增**；且**在 env 已设的前提下仍拒绝**（证明无 env 兜底，裁-5 fail-closed）；
- **正向**：配租户凭据 → `task_count==N`、库行数 +N、`content_asset_id`/`tenant_id` 正确；
- **幂等**：同键重复提交 → 不产生第二行、`task_count` 不增、复用既有 task_id；
- **校验**：内容解析失败 / 平台未登记 → `ValueError`（端点 → 400），不静默建行。

契约落点：`docs/模块5-publish_jobs收口契约-2026-09-27.md` §3.1-3.5 / §7 / R5-R8。
"""
from __future__ import annotations

import uuid

import pytest

from app.models.content import Platform, PlatformAccount, PublishTask
from app.models.content_master import ContentMaster
from app.services.publish_service import PublishService

TENANT = "3a333333-3333-4333-8333-333333333331"


def _task_count(db) -> int:
    return db.query(PublishTask).count()


@pytest.fixture
def fix(db_session):
    """造平台 / 账号 / 内容的最小集合；测试结束按创建顺序清理（留空库）。"""
    state: dict[str, list[str]] = {"platforms": [], "accounts": [], "masters": []}

    def mk_platform(*, is_active: bool = True) -> Platform:
        p = Platform(
            id=str(uuid.uuid4()),
            name="P" + uuid.uuid4().hex[:10],   # name unique
            platform_type="b2b",
            is_active=is_active,
        )
        db_session.add(p)
        db_session.commit()
        db_session.refresh(p)
        state["platforms"].append(str(p.id))
        return p

    def mk_account(*, platform_id, tenant_id: str = TENANT, is_active: bool = True,
                   token_data: dict | None = None, cookie_data: str | None = None) -> PlatformAccount:
        a = PlatformAccount(
            id=str(uuid.uuid4()),
            platform_id=platform_id,
            tenant_id=tenant_id,
            account_name="acct-" + uuid.uuid4().hex[:6],
            is_active=is_active,
            token_data=token_data or {},
            cookie_data=cookie_data,
        )
        db_session.add(a)
        db_session.commit()
        db_session.refresh(a)
        state["accounts"].append(str(a.id))
        return a

    def mk_master(*, tenant_id: str = TENANT) -> ContentMaster:
        m = ContentMaster(id=str(uuid.uuid4()), tenant_id=tenant_id, title="M1 反证内容")
        db_session.add(m)
        db_session.commit()
        db_session.refresh(m)
        state["masters"].append(str(m.id))
        return m

    yield {"platform": mk_platform, "account": mk_account, "master": mk_master}

    for mid in state["masters"]:
        db_session.query(PublishTask).filter(
            PublishTask.content_master_id == mid
        ).delete(synchronize_session=False)
        db_session.query(ContentMaster).filter(
            ContentMaster.id == mid
        ).delete(synchronize_session=False)
    for aid in state["accounts"]:
        db_session.query(PlatformAccount).filter(
            PlatformAccount.id == aid
        ).delete(synchronize_session=False)
    for pid in state["platforms"]:
        db_session.query(Platform).filter(
            Platform.id == pid
        ).delete(synchronize_session=False)
    db_session.commit()


class TestM1FailClosed:
    """负向：未配凭据必须拒绝，且不得偷偷建行 / 不得用 env 顶上。"""

    def test_negative_no_credential_is_skipped(self, db_session, fix):
        svc = PublishService(db_session)
        plat = fix["platform"]()
        acct = fix["account"](platform_id=plat.id)     # token_data 空 → 无凭据
        master = fix["master"]()
        before = _task_count(db_session)

        res = svc.publish_content(
            content_id=str(master.id),
            platform_ids=[str(plat.id)],
            account_ids=[str(acct.id)],
        )

        assert res["task_count"] == 0
        assert res["skipped"] == [{"platform_id": str(plat.id), "reason": "credential_missing"}]
        assert _task_count(db_session) == before, "fail-closed：未配凭据不得建行"

    def test_negative_env_present_still_rejects(self, db_session, fix, monkeypatch):
        """§7.1 硬要求：负向必须在 **env 已设** 的前提下仍拒绝（证明没走 env 顶上）。"""
        monkeypatch.setenv("WECHAT_MP_APPID", "wx-fake-appid")
        monkeypatch.setenv("PLATFORM_X", "fake-secret")
        svc = PublishService(db_session)
        plat = fix["platform"]()
        acct = fix["account"](platform_id=plat.id)
        master = fix["master"]()
        before = _task_count(db_session)

        res = svc.publish_content(
            content_id=str(master.id),
            platform_ids=[str(plat.id)],
            account_ids=[str(acct.id)],
        )

        assert res["task_count"] == 0
        assert res["skipped"][0]["reason"] == "credential_missing"
        assert _task_count(db_session) == before

    def test_unknown_content_raises_value_error(self, db_session, fix):
        svc = PublishService(db_session)
        with pytest.raises(ValueError, match="内容不存在或不可发布"):
            svc.publish_content(content_id=str(uuid.uuid4()), platform_ids=[], account_ids=[])

    def test_unregistered_platform_raises_value_error(self, db_session, fix):
        svc = PublishService(db_session)
        master = fix["master"]()
        with pytest.raises(ValueError, match="平台不可用或未登记"):
            svc.publish_content(
                content_id=str(master.id),
                platform_ids=[str(uuid.uuid4())],
                account_ids=[str(uuid.uuid4())],
            )


class TestM1Positive:
    """正向：配了租户凭据必须能建任务；幂等：同键重提不产生第二行。"""

    def test_positive_creates_one_task(self, db_session, fix):
        svc = PublishService(db_session)
        plat = fix["platform"]()
        acct = fix["account"](platform_id=plat.id, token_data={"access_token": "t-1"})
        master = fix["master"]()
        before = _task_count(db_session)

        res = svc.publish_content(
            content_id=str(master.id),
            platform_ids=[str(plat.id)],
            account_ids=[str(acct.id)],
        )

        assert res["task_count"] == 1
        assert _task_count(db_session) == before + 1
        task = db_session.query(PublishTask).filter(
            PublishTask.idempotency_key == f"pub:{TENANT}:{master.id}:{plat.id}:{acct.id}:v1"
        ).one()
        assert str(task.content_asset_id) == str(master.id), "R7：content_asset_id 落 content_masters.id"
        assert str(task.tenant_id) == TENANT, "R6：发布域 tenant_id 存 uuid 字符串形式"
        assert task.status == "pending", "只建任务不真发"
        assert task.publish_type == "immediate"

    def test_idempotent_repeat_submit(self, db_session, fix):
        svc = PublishService(db_session)
        plat = fix["platform"]()
        acct = fix["account"](platform_id=plat.id, token_data={"access_token": "t-1"})
        master = fix["master"]()
        kw = dict(
            content_id=str(master.id),
            platform_ids=[str(plat.id)],
            account_ids=[str(acct.id)],
        )

        first = svc.publish_content(**kw)
        after_first = _task_count(db_session)
        second = svc.publish_content(**kw)

        assert first["task_count"] == 1
        assert second["task_count"] == 0, "幂等：重提不得新增计数"
        assert _task_count(db_session) == after_first, "幂等：不得产生第二行"
        assert second["task_ids"] == first["task_ids"], "幂等：复用既有行"

    def test_batch_publish(self, db_session, fix):
        svc = PublishService(db_session)
        plat = fix["platform"]()
        acct = fix["account"](platform_id=plat.id, token_data={"access_token": "t-1"})
        m1, m2 = fix["master"](), fix["master"]()

        res = svc.batch_publish([
            {"content_id": str(m1.id), "platform_ids": [str(plat.id)], "account_ids": [str(acct.id)]},
            {"content_id": str(m2.id), "platform_ids": [str(plat.id)], "account_ids": [str(acct.id)]},
        ])

        assert len(res) == 2
        assert [r["task_count"] for r in res] == [1, 1]

    def test_get_publish_tasks_serialization(self, db_session, fix):
        svc = PublishService(db_session)
        plat = fix["platform"]()
        acct = fix["account"](platform_id=plat.id, token_data={"access_token": "t-1"})
        master = fix["master"]()
        svc.publish_content(
            content_id=str(master.id),
            platform_ids=[str(plat.id)],
            account_ids=[str(acct.id)],
        )

        items, total = svc.get_publish_tasks(status="pending", page=1, page_size=10)
        assert total >= 1
        assert items, "应有可序列化 items"
        # 字段对齐 unified_publish._serialize_task，并补 publish_jobs 新列
        for key in ("id", "status", "publish_type", "content_asset_id", "idempotency_key"):
            assert key in items[0]

    def test_schedule_publish_sets_scheduled_type(self, db_session, fix):
        import asyncio
        from datetime import datetime, timedelta, timezone

        svc = PublishService(db_session)
        plat = fix["platform"]()
        acct = fix["account"](platform_id=plat.id, token_data={"access_token": "t-1"})
        master = fix["master"]()
        when = datetime.now(timezone.utc) + timedelta(hours=1)

        # 2026-09-28 加固：原 asyncio.get_event_loop().run_until_complete(...) 依赖
        # 「当前线程已有事件循环」——同进程先前任何测试清理过 loop（如 E2E/外发链的
        # asyncio.run 收尾 set_event_loop(None)）即 RuntimeError。asyncio.run 自建
        # 新 loop，与执行顺序无关，语义不变。
        res = asyncio.run(
            svc.schedule_publish(
                content_id=str(master.id),
                platform_ids=[str(plat.id)],
                account_ids=[str(acct.id)],
                scheduled_time=when,
            )
        )

        assert res["task_count"] == 1
        task = db_session.query(PublishTask).filter(
            PublishTask.idempotency_key == f"pub:{TENANT}:{master.id}:{plat.id}:{acct.id}:v1"
        ).one()
        assert task.publish_type == "scheduled"
        assert task.scheduled_time is not None
