#!/usr/bin/env python3
"""COMP-03 · 生成送检说明书章节骨架（人类填写 · 非 AI 正文）"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "compliance" / "comp-03-manual"
SHOT = ROOT / "docs" / "cert-screenshots"

CHAPTERS = [
    ("01-login", "登录与账号", "/login", "cert-01-login.png", [
        "系统支持的账号类型（超管/租户/代理）",
        "登录页左栏租户搜索说明",
        "密码登录与安全提示",
    ]),
    ("02-tenants", "租户管理", "/admin/tenants", "cert-02-tenants.png", [
        "租户列表字段含义",
        "新建/编辑租户步骤",
        "状态与套餐说明",
    ]),
    ("03-hierarchy", "层级管理", "/admin/hierarchy", "cert-03-hierarchy.png", [
        "组织树操作",
        "权限继承规则",
    ]),
    ("04-aggregation", "数据中心", "/admin/aggregation", "cert-04-aggregation.png", [
        "聚合指标定义",
        "筛选与导出",
    ]),
    ("05-health", "系统健康", "/system-health/dashboard", "cert-05-health.png", [
        "健康指标说明",
        "告警处理流程",
    ]),
    ("06-finance", "商业与发票", "/admin/finance", "cert-06-finance.png", [
        "套餐与账单入口",
        "发票申请步骤",
    ]),
    ("07-products", "产品管理", "/products", "cert-07-products.png", [
        "产品 CRUD 操作",
        "必填字段说明",
    ]),
    ("08-categories", "分类管理", "/products/categories", "cert-08-categories.png", [
        "分类树维护",
        "与产品关联",
    ]),
    ("09-inquiries", "海外询盘", "/international/inquiries", "cert-09-inquiries.png", [
        "询盘 inbox 流程",
        "状态变更与导出",
    ]),
    ("10-seo", "SEO 发布", "/seo-matrix/publish", "cert-10-seo.png", [
        "发布任务创建",
        "进度查看",
    ]),
    ("11-ai-content", "AI 内容助手", "/admin/ai-center/content", "cert-11-ai-content.png", [
        "内容生成与审核",
        "Token 消耗说明",
    ]),
    ("12-trade-intel", "贸易情报", "/admin/ai-engine/trade-intel", "cert-12-trade-intel.png", [
        "查询入口与结果解读",
    ]),
]


def chapter_md(slug: str, title: str, route: str, png: str, bullets: list[str]) -> str:
    shot_rel = f"../../cert-screenshots/{png}"
    lines = [
        f"# 第{slug.split('-')[0]}章 · {title}",
        "",
        f"> **路由**：`{route}` · **配图**：`{png}`",
        "> **填写说明**：以下【人类填写区】由经办人手写扩写，每章 500–1300 字。",
        "",
        "## 功能概述",
        "",
        "【人类填写区：本模块解决什么业务问题】",
        "",
        "## 操作步骤",
        "",
    ]
    for i, b in enumerate(bullets, 1):
        lines.append(f"{i}. {b}")
        lines.append("   - 【人类填写区：逐步操作说明】")
        lines.append("")
    lines.extend([
        "## 界面截图",
        "",
        f"![{title}]({shot_rel})",
        "",
        "## 常见问题",
        "",
        "【人类填写区】",
        "",
        "---",
        "*COMP-03 骨架 · 非 AI 正文*",
    ])
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index_lines = [
        "# COMP-03 · 送检用户操作说明书（骨架）",
        "",
        "> 经办人逐章手写扩写后 → `scripts/build-cert-manual-html.py` → PM-05 PDF",
        "",
        "| 章 | 文件 | 路由 |",
        "|----|------|------|",
    ]
    for slug, title, route, png, _ in CHAPTERS:
        fname = f"{slug}.md"
        (OUT / fname).write_text(chapter_md(slug, title, route, png, _), encoding="utf-8")
        index_lines.append(f"| {title} | [{fname}](./{fname}) | `{route}` |")
        missing = not (SHOT / png).exists()
        if missing:
            print(f"[warn] screenshot missing: {png}")

    (OUT / "README.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(CHAPTERS)} chapters -> {OUT}")


if __name__ == "__main__":
    main()
