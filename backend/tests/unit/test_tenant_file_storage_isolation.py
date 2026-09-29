# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""验证多租户文件与资料图片存储隔离性单元测试。"""
from __future__ import annotations

import uuid
import pytest

from app.models.tenant import Tenant, TenantPlan, UserTenant
from app.models.user import User
from app.services.product_image_storage_service import (
    store_uploaded_bytes,
    filter_meta_for_user,
    object_key_for_upload,
)


def _create_tenant_and_user(db_session, name: str) -> tuple[Tenant, User]:
    plan = db_session.query(TenantPlan).first()
    if not plan:
        plan = TenantPlan(name="Plan", code=f"p_{uuid.uuid4().hex[:6]}", price_monthly=0, price_yearly=0)
        db_session.add(plan)
        db_session.flush()

    t = Tenant(
        id=str(uuid.uuid4()),
        name=name,
        domain=f"iso-{uuid.uuid4().hex[:6]}.com",
        plan_id=plan.id,
        status="active",
    )
    db_session.add(t)

    u = User(
        id=str(uuid.uuid4()),
        username=f"u_{uuid.uuid4().hex[:8]}",
        email=f"u_{uuid.uuid4().hex[:8]}@test.com",
        hashed_password="pw",
        role="tenant",
        is_active=True,
    )
    db_session.add(u)
    db_session.flush()

    ut = UserTenant(
        id=str(uuid.uuid4()),
        user_id=u.id,
        tenant_id=t.id,
        role="admin",
        is_active=True,
    )
    db_session.add(ut)
    db_session.commit()
    return t, u


def test_tenant_storage_image_isolation(db_session):
    """验证租户一绝对无法看到租户二上传的资料图片。"""
    t1, u1 = _create_tenant_and_user(db_session, "租户一-建材厂")
    t2, u2 = _create_tenant_and_user(db_session, "租户二-石材厂")

    # 1. 租户一上传专属资料图片
    meta1 = store_uploaded_bytes(
        db_session,
        u1,
        content=b"tenant1_secret_blueprint_or_tile_image",
        original_filename="ceramic_tile_blueprint.jpg",
        content_type="image/jpeg",
        prefer_local_storage=True,
    )
    assert meta1["tenant_id"] == str(t1.id)
    assert meta1["original_name"] == "ceramic_tile_blueprint.jpg"

    # 2. 租户二上传专属资料图片
    meta2 = store_uploaded_bytes(
        db_session,
        u2,
        content=b"tenant2_private_marble_catalog",
        original_filename="granite_marble_quote.png",
        content_type="image/png",
        prefer_local_storage=True,
    )
    assert meta2["tenant_id"] == str(t2.id)
    assert meta2["original_name"] == "granite_marble_quote.png"

    all_meta = [meta1, meta2]

    # 3. 租户一查询列表：只能看到自己的图片，绝对看不到租户二的图片
    u1_visible = filter_meta_for_user(all_meta, db_session, u1)
    u1_file_ids = [m["id"] for m in u1_visible]
    u1_file_names = [m["original_name"] for m in u1_visible]

    assert meta1["id"] in u1_file_ids
    assert "ceramic_tile_blueprint.jpg" in u1_file_names
    assert meta2["id"] not in u1_file_ids, "严重违规：租户一看到了租户二的文件ID！"
    assert "granite_marble_quote.png" not in u1_file_names, "严重违规：租户一看到了租户二的图片名！"

    # 4. 租户二查询列表：只能看到自己的图片，绝对看不到租户一的图片
    u2_visible = filter_meta_for_user(all_meta, db_session, u2)
    u2_file_ids = [m["id"] for m in u2_visible]
    u2_file_names = [m["original_name"] for m in u2_visible]

    assert meta2["id"] in u2_file_ids
    assert "granite_marble_quote.png" in u2_file_names
    assert meta1["id"] not in u2_file_ids, "严重违规：租户二看到了租户一的文件ID！"
    assert "ceramic_tile_blueprint.jpg" not in u2_file_names, "严重违规：租户二看到了租户一的图片名！"

    # 5. 云端 Object Key 物理命名空间强制携带租户 ID
    key1 = object_key_for_upload(str(t1.id), meta1["id"], meta1["original_name"], meta1["category"])
    key2 = object_key_for_upload(str(t2.id), meta2["id"], meta2["original_name"], meta2["category"])
    assert key1.startswith(f"tenants/{t1.id}/images/")
    assert key2.startswith(f"tenants/{t2.id}/images/")
    assert str(t1.id) not in key2
    assert str(t2.id) not in key1
