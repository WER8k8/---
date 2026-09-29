# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""G12 Evolution 生产晋升与回滚演练单元测试。"""
from __future__ import annotations

import pytest
from app.services.evolution.version_control import VersionControl


def test_evolution_promotion_and_rollback_lifecycle(db_session):
    vc = VersionControl(db_session)
    skill_id = "test_evolution_skill"

    # 1. 创建 v0.1.0 draft
    v1 = vc.create_skill_version(
        skill_id=skill_id,
        skill_name="Test Skill",
        bump="minor",
        prompt_template="Prompt v1",
    )
    assert v1.status == "draft"

    # 2. 推进到 evaluation -> canary
    vc.transition_skill(v1.id, "evaluation")
    vc.transition_skill(v1.id, "canary", canary_percentage=20.0)
    assert v1.status == "canary"
    assert v1.canary_percentage == 20.0

    # 3. 生产晋升 (G12 Promotion)
    prod_v1 = vc.promote_skill_to_production(v1.id, operator_id="admin_01", changelog="Initial production release")
    assert prod_v1.status == "production"
    assert prod_v1.canary_percentage == 100.0
    assert vc.get_production_version(skill_id).id == v1.id

    # 4. 创建下一个迭代 v0.2.0 并推进到 canary
    v2 = vc.create_skill_version(
        skill_id=skill_id,
        skill_name="Test Skill",
        bump="minor",
        prompt_template="Prompt v2",
        parent_version_id=v1.id,
    )
    vc.transition_skill(v2.id, "evaluation")
    vc.transition_skill(v2.id, "canary", canary_percentage=50.0)

    # 5. 晋升 v2 到生产，验证 v1 自动转为 archived
    prod_v2 = vc.promote_skill_to_production(v2.id, operator_id="admin_01", changelog="Upgrade to v2")
    assert prod_v2.status == "production"
    db_session.refresh(v1)
    assert v1.status == "archived", "旧生产版本必须归档为 archived"

    # 6. 演练回滚 (G12 Rollback) 到 v1
    rolled_back = vc.rollback_skill(skill_id, operator_id="admin_01", reason="Rehearsal rollback test")
    assert rolled_back.id == v1.id
    assert rolled_back.status == "production"
    db_session.refresh(v2)
    assert v2.status == "archived", "被回滚的新版本应转为 archived"
