#!/usr/bin/env python3
"""全量深度扫描：杜绝假接口 / 假成功 / 假数据（QA 门禁）。"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "app"
FRONTEND = ROOT / "frontend" / "admin" / "src"
REPORT = ROOT / "docs" / "no-fake-delivery-scan-latest.json"

# (pattern, label, severity P0|P1|P2)
BACKEND_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"暂时返回模拟|后续接入真实|TODO:\s*调用", re.I),
        "注释承认模拟实现但未门控",
        "P0",
    ),
    (
        re.compile(r"生成AI回复（模拟）|暂时返回模拟回复"),
        "AI 接待使用硬编码模拟回复",
        "P0",
    ),
    (
        re.compile(r'"included"\s*:\s*True.*stub|included:\s*True.*probe_mode.*stub'),
        "收录 stub 冒充已收录",
        "P0",
    ),
    (
        re.compile(r"STATIC_DEMO_KEYWORDS"),
        "SEO 关键词注入静态演示数据",
        "P0",
    ),
    (
        re.compile(r"_summary_from_demo\s*\("),
        "仪表盘无记录时返回演示摘要",
        "P0",
    ),
    (
        re.compile(r"无记录时返回演示数据"),
        "API 文档承认无 DB 仍返回演示数据",
        "P0",
    ),
    (
        re.compile(r"def _mock_trend\s*\("),
        "代理趋势硬编码 mock 数据",
        "P0",
    ),
    (
        re.compile(r"_DEMO_CAMPAIGN_STATS|_DEMO_CUSTOMERS"),
        "硬编码演示客户/活动统计",
        "P0",
    ),
    (
        re.compile(r"返回演示数据|Demo Corp"),
        "桥接层返回演示客户",
        "P0",
    ),
    (
        re.compile(
            r'return success_response\(data=\{"negotiations": \[\]',
        ),
        "谈单引擎未配置仍 200 空列表",
        "P0",
    ),
    (
        re.compile(r"模拟AI生成"),
        "预设内容冒充 AI 生成（须显式标记 preset）",
        "P1",
    ),
    (
        re.compile(r'"mock"\s*:\s*True'),
        "响应体含 mock:true（须确认生产门控）",
        "P1",
    ),
    (
        re.compile(r'data_source["\']?\s*:\s*["\']mock["\']'),
        "统计 data_source=mock（须确认生产门控）",
        "P1",
    ),
]

FRONTEND_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"fallback to mock", re.I),
        "API 失败静默回退假数据",
        "P0",
    ),
    (
        re.compile(r"// fallback to mock"),
        "前端 catch 块注入假回复/假数据",
        "P0",
    ),
    (
        re.compile(r"模拟翻译"),
        "翻译 API 失败本地假译文",
        "P1",
    ),
    (
        re.compile(
            r"const orchestrations = ref\(\[\s*\{[^}]+name:\s*'",
        ),
        "任务编排页内嵌假任务列表",
        "P0",
    ),
    (
        re.compile(
            r"const records = ref\(\[\s*\{[^}]+name:\s*'",
        ),
        "执行复盘页内嵌假记录",
        "P0",
    ),
    (
        re.compile(
            r"const summary = ref\(\[\s*\{[^}]+value:\s*\d+",
        ),
        "执行复盘页内嵌假统计",
        "P0",
    ),
    (
        re.compile(r"WORKBENCH_MOCK"),
        "营销落地页工作台示意数据（已废弃常量名）",
        "P2",
    ),
    (
        re.compile(r"function getMock\w+\("),
        "前端 getMock* 假数据生成函数",
        "P0",
    ),
    (
        re.compile(r"MOCK_STATS|MOCK_TREE|MOCK_CHAINS"),
        "代理汇总 Mock 种子数据",
        "P0",
    ),
    (
        re.compile(r'"api_calls_today"\s*:\s*12580|"total_calls"\s*:\s*12580'),
        "硬编码 AI/API 调用量",
        "P0",
    ),
    (
        re.compile(r"catch \{ /\* keep mock \*/ \}"),
        "API 失败保留 mock 数据",
        "P0",
    ),
    (
        re.compile(
            r"revenue\s*\?\?\s*x\.clientCount|"
            r"revenue:\s*Number\([^)]*inquiries"
        ),
        "用客户数/询盘冒充收入",
        "P0",
    ),
    (
        re.compile(r"sum\(TenantSubscription\.amount\)"),
        "用订阅合同价冒充 MRR/实收",
        "P0",
    ),
    (
        re.compile(r"demoFallback"),
        "usePageData 演示数据回退",
        "P0",
    ),
    (
        re.compile(r"const criticalCount = ref\([1-9]"),
        "代码审查页内嵌假统计",
        "P0",
    ),
    (
        re.compile(r"SSL证书自动续期成功|Redis内存使用超过75%"),
        "健康看板内嵌假运维事件",
        "P0",
    ),
    (
        re.compile(r"gds_id:\s*'DEMO001'"),
        "GEO 页 catch 注入假数据集",
        "P0",
    ),
]

# 路径片段：命中则降级为 P2 或跳过（已门控 / 明示演示区）
ALLOWLIST_DOWNGRADE: dict[str, str] = {
    "chat.py": "P2",
    "payment.py": "P2",
    "payment_service.py": "P2",
    "inclusion_check_service.py": "P2",
    "provisioner.py": "P2",
    "egress_jit_provision_service.py": "P2",
    "pilot_rehearsal_service.py": "P2",
    "seven_step_framework_service.py": "P2",
    "ops_jobs.py": "P2",
    "accio_gap_handlers.py": "P2",
    "ubrain_commercial_os.py": "P2",
    "noFakeDelivery.ts": "P2",
    "landing/index.vue": "P2",
    "ai-learning/behavior.vue": "P2",
    "media_factory.py": "P2",  # _allow_dev_ai_fallback 门控
    "no_fake_delivery.py": "P2",
    "building_wiki.py": "P2",  # 响应 message 已标明内置模板
    "keyword_ranking.py": "P2",  # SEO_KEYWORD_DEMO_ALLOW + mock_allowed 门控
    "admin/geo/index.vue": "P2",  # 超管 GEO 实验台，样例须走后端
    "templates/": "P2",
    "admin-vben/": "P2",
    "_ref/": "P2",
    "baidu_webmaster_service.py": "P2",  # stamp_mock + BAIDU_WEBMASTER_ALLOW_MOCK 门控
    "no_fake_delivery.py": "P2",
    "no_fake_delivery_guard.py": "P2",
    "no_fake_delivery_middleware.py": "P2",
    "ai_engine.py": "P2",  # MockLLM 由 invoke 层生产门控
}

SKIP_DIRS = {"__pycache__", "tests", "node_modules", "dist"}
# 门禁/契约文件自身 — 不参与假交付正文扫描
SKIP_FILES = {
    "backend/app/core/no_fake_delivery_guard.py",
    "backend/app/core/no_fake_delivery_middleware.py",
    "backend/app/core/no_fake_delivery.py",
    "frontend/admin/src/constants/noFakeDelivery.ts",
}
GATE_MARKERS = (
    "mock_allowed(",
    "stamp_mock(",
    "_mock_pay_allowed(",
    "_allow_dev_ai_fallback(",
    "is_production_environment(",
    "payment_mock_allowed(",
    "NotConfiguredError",
    "error_response(503",
    "error_response(code=503",
    "generation_mode",
    "preset_template",
    "SEO_KEYWORD_DEMO_ALLOW",
    "BAIDU_WEBMASTER_ALLOW_MOCK",
    "AGENT_PORTAL_MOCK_TREND",
    "NEGOTIATION_ENGINE_NOT_CONFIGURED",
    "marketing_preview_mode",
    "mode: 'marketing_preview'",
)


def _iter_files(base: Path, suffix: str) -> list[Path]:
    files: list[Path] = []
    if not base.exists():
        return files
    for path in base.rglob(f"*{suffix}"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        files.append(path)
    return files


def _allowlist_severity(rel: str, severity: str) -> str:
    for fragment, down in ALLOWLIST_DOWNGRADE.items():
        if fragment.replace("\\", "/") in rel.replace("\\", "/"):
            if severity == "P0":
                return down
            return severity
    return severity


def _has_gate_context(text: str, line_no: int, window: int = 25) -> bool:
    lines = text.splitlines()
    start = max(0, line_no - window)
    end = min(len(lines), line_no + window)
    chunk = "\n".join(lines[start:end])
    return any(m in chunk for m in GATE_MARKERS)


def _scan_file(path: Path, rules: list, root: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return findings

    rel = str(path.relative_to(root))
    rel_posix = rel.replace("\\", "/")
    if rel_posix in SKIP_FILES:
        return findings
    for pattern, label, severity in rules:
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            sev = _allowlist_severity(rel, severity)
            if sev != "P2" and _has_gate_context(text, line):
                sev = "P2"
            findings.append(
                {
                    "file": rel,
                    "line": line,
                    "label": label,
                    "severity": sev,
                    "snippet": text.splitlines()[line - 1].strip()[:140],
                }
            )
    return findings


def scan() -> dict:
    findings: list[dict] = []
    for path in _iter_files(BACKEND, ".py"):
        findings.extend(_scan_file(path, BACKEND_RULES, ROOT))
    for path in _iter_files(FRONTEND, ".vue"):
        findings.extend(_scan_file(path, FRONTEND_RULES, ROOT))
    for path in _iter_files(FRONTEND, ".ts"):
        findings.extend(_scan_file(path, FRONTEND_RULES, ROOT))

    # 去重：同文件同行同 label
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for f in findings:
        key = (f["file"], f["line"], f["label"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(f)

    p0 = [f for f in deduped if f["severity"] == "P0"]
    p1 = [f for f in deduped if f["severity"] == "P1"]
    p2 = [f for f in deduped if f["severity"] == "P2"]
    ok = len(p0) == 0 and len(p1) == 0

    return {
        "ok": ok,
        "task": "NO-FAKE-DELIVERY-DEEP",
        "scanned": {
            "backend_py": len(_iter_files(BACKEND, ".py")),
            "frontend_vue": len(_iter_files(FRONTEND, ".vue")),
            "frontend_ts": len(_iter_files(FRONTEND, ".ts")),
        },
        "p0_count": len(p0),
        "p1_count": len(p1),
        "p2_count": len(p2),
        "findings": deduped,
        "p0_findings": p0,
        "p1_findings": p1,
    }


def main() -> int:
    out = scan()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
