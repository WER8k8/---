# -*- coding: utf-8 -*-
# Copyright (c) 2026 吕博旺 (131025199403304817). All rights reserved.
"""Accio gap 技能 ID（避免 catalog ↔ handlers 循环导入）。"""



# GET /gap 预览仍返回 MVP 载荷的 partial 技能

GAP_MVP_SKILL_IDS = frozenset(

    {

        "image_sourcing",

        "supplier_rfq",

    }

)



# POST /gap/{id}/execute 可执行技能（含已升级为 true 的矩阵/建站/广告/RBAC）

GAP_EXECUTE_SKILL_IDS = frozenset(

    {

        "image_sourcing",

        "auto_shopify",

        "paid_ads_creative",

        "supplier_rfq",

        "matrix_publish",

        "team_rbac",

    }

)

