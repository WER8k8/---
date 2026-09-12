"""
Talking-Stick 报告生成器
负责生成多格式的安全审计报告
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReportGenerator:
    """报告生成器"""
    def __init__(self, output_dir: str = "docs", formats: list = None):
        """__init__。

        参数说明：
        :param self: 参数 self
        :param output_dir: 参数 output_dir
        :param formats: 参数 formats
        :return: 返回处理结果。
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.formats = formats or ["markdown", "json"]
    
    def generate(self, task_id: str, scan_result: Dict, audit_result: Dict, 
                 verification_result: Dict, summary: Dict) -> Dict[str, str]:
        """生成所有格式的报告"""
        report_paths = {}
        for fmt in self.formats:
            if fmt == "markdown":
                path = self._generate_markdown(task_id, scan_result, audit_result, verification_result, summary)
                report_paths["markdown"] = path
            elif fmt == "json":
                path = self._generate_json(task_id, scan_result, audit_result, verification_result, summary)
                report_paths["json"] = path
            elif fmt == "html":
                path = self._generate_html(task_id, scan_result, audit_result, verification_result, summary)
                report_paths["html"] = path
        
        return report_paths
    
    def _generate_markdown(self, task_id: str, scan_result: Dict, audit_result: Dict, 
                          verification_result: Dict, summary: Dict) -> str:
        """生成Markdown格式报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"talking-stick-audit-{timestamp}.md"
        filepath = self.output_dir / filename
        severity = summary.get("critical_count", 0), summary.get("high_count", 0), summary.get("medium_count", 0), summary.get("low_count", 0)
        content = f"""# Talking-Stick 安全审计报告

**任务ID**: {task_id}
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**扫描目标**: {scan_result.get('target_path', 'N/A')}

## 执行摘要

| 指标 | 数值 |
|------|------|
| 总文件数 | {summary.get('total_files', 0)} |
| 风险文件 | {summary.get('risk_files', 0)} |
| 发现漏洞 | {summary.get('total_vulnerabilities', 0)} |
| 严重漏洞 | {summary.get('critical_count', 0)} |
| 高危漏洞 | {summary.get('high_count', 0)} |
| 中危漏洞 | {summary.get('medium_count', 0)} |
| 低危漏洞 | {summary.get('low_count', 0)} |
| 确认漏洞 | {summary.get('confirmed_vulnerabilities', 0)} |
| 误报 | {summary.get('false_positives', 0)} |

## 侦察阶段结果

- **总文件数**: {scan_result.get('summary', {}).get('total_files', 0)}
- **风险文件**: {scan_result.get('summary', {}).get('risk_files', 0)}
- **依赖数量**: {scan_result.get('summary', {}).get('total_dependencies', 0)}

### 风险文件列表

"""
        risk_files = scan_result.get("risk_files", [])
        if risk_files:
            content += "| 文件路径 | 风险分数 | 风险原因 |\n"
            content += "|----------|----------|----------|\n"
            for rf in risk_files[:20]:  # 最多显示20个
                reasons = ", ".join(rf.get("risk_reasons", []))
                content += f"| {rf.get('relative_path', rf.get('path', ''))} | {rf.get('risk_score', 0)} | {reasons} |\n"
        else:
            content += "无\n"
        
        content += "\n## 审计阶段结果\n\n"
        vulnerabilities = audit_result.get("vulnerabilities", [])
        if vulnerabilities:
            content += "### 漏洞详情\n\n"
            for vuln in vulnerabilities[:50]:  # 最多显示50个
                content += f"""#### {vuln.get('rule_id', 'Unknown')} - {vuln.get('severity', 'info').upper()}

- **文件**: {vuln.get('file_path', 'N/A')}
- **行号**: {vuln.get('line_number', 'N/A')}
- **类别**: {vuln.get('owasp_category', 'N/A')}
- **描述**: {vuln.get('message', 'N/A')}
- **匹配内容**: `{vuln.get('matched_content', 'N/A')}`

"""
        else:
            content += "未发现漏洞\n"
        
        content += "\n## 验证阶段结果\n\n"
        verify_results = verification_result.get("results", [])
        if verify_results:
            confirmed = [r for r in verify_results if r.get("is_confirmed")]
            false_pos = [r for r in verify_results if r.get("is_false_positive")]
            content += f"- **确认漏洞**: {len(confirmed)}\n"
            content += f"- **误报**: {len(false_pos)}\n\n"
            if confirmed:
                content += "### 修复建议\n\n"
                for r in confirmed:
                    fix = r.get("fix", {})
                    poc = r.get("poc", {})
                    content += f"""#### {r.get('vulnerability_id', 'Unknown')} ({poc.get('risk_level', 'medium')})

- **修复方案**: {fix.get('approach', 'N/A')}
- **代码示例**:
```python
{fix.get('code_example', 'N/A')}
```
- **预计工作量**: {fix.get('estimated_effort', 'N/A')}
- **优先级**: {fix.get('priority', 'N/A')}

"""
        else:
            content += "无验证结果\n"
        
        content += f"\n---\n*报告由 Talking-Stick v1.0.0 自动生成*\n"
        filepath.write_text(content, encoding="utf-8")
        return str(filepath)
    
    def _generate_json(self, task_id: str, scan_result: Dict, audit_result: Dict, 
                      verification_result: Dict, summary: Dict) -> str:
        """生成JSON格式报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"talking-stick-audit-{timestamp}.json"
        filepath = self.output_dir / filename
        output = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "scan_result": {
                "target_path": scan_result.get("target_path"),
                "summary": scan_result.get("summary"),
                "risk_files_count": len(scan_result.get("risk_files", [])),
                "recommendations": scan_result.get("recommendations", [])
            },
            "audit_result": {
                "summary": audit_result.get("summary"),
                "vulnerabilities": audit_result.get("vulnerabilities", []),
                "recommendations": audit_result.get("recommendations", [])
            },
            "verification_result": {
                "summary": verification_result.get("summary"),
                "fixes": verification_result.get("fixes", {}),
                "recommendations": verification_result.get("recommendations", [])
            }
        }
        filepath.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(filepath)
    
    def _generate_html(self, task_id: str, scan_result: Dict, audit_result: Dict, 
                      verification_result: Dict, summary: Dict) -> str:
        """生成HTML格式报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"talking-stick-audit-{timestamp}.html"
        filepath = self.output_dir / filename
        vuln_rows = ""
        for vuln in audit_result.get("vulnerabilities", [])[:30]:
            severity_class = vuln.get("severity", "info")
            vuln_rows += f"""
            <tr class="{severity_class}">
                <td>{vuln.get('rule_id', 'N/A')}</td>
                <td><span class="badge {severity_class}">{vuln.get('severity', 'info').upper()}</span></td>
                <td>{vuln.get('file_path', 'N/A')}</td>
                <td>{vuln.get('line_number', 'N/A')}</td>
                <td>{vuln.get('owasp_category', 'N/A')}</td>
                <td>{vuln.get('message', 'N/A')}</td>
            </tr>"""
        
        content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Talking-Stick 安全审计报告 - {task_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #4a9b8c 0%, #2d7a6e 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .summary-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }}
        .summary-card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; }}
        .summary-card .value {{ font-size: 32px; font-weight: bold; }}
        .critical .value {{ color: #dc3545; }}
        .high .value {{ color: #fd7e14; }}
        .medium .value {{ color: #ffc107; }}
        .low .value {{ color: #28a745; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge.critical {{ background: #dc3545; color: white; }}
        .badge.high {{ background: #fd7e14; color: white; }}
        .badge.medium {{ background: #ffc107; color: #333; }}
        .badge.low {{ background: #28a745; color: white; }}
        .badge.info {{ background: #17a2b8; color: white; }}
        tr.critical {{ border-left: 4px solid #dc3545; }}
        tr.high {{ border-left: 4px solid #fd7e14; }}
        tr.medium {{ border-left: 4px solid #ffc107; }}
        tr.low {{ border-left: 4px solid #28a745; }}
        .section {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ margin-top: 0; color: #333; }}
        .recommendation {{ padding: 10px 15px; background: #e8f5e9; border-left: 4px solid #4caf50; margin: 10px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Talking-Stick 安全审计报告</h1>
            <p>任务ID: {task_id} | 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>扫描目标: {scan_result.get('target_path', 'N/A')}</p>
        </div>
        <div class="summary-grid">
            <div class="summary-card"><h3>总文件数</h3><div class="value">{summary.get('total_files', 0)}</div></div>
            <div class="summary-card"><h3>风险文件</h3><div class="value">{summary.get('risk_files', 0)}</div></div>
            <div class="summary-card critical"><h3>严重漏洞</h3><div class="value">{summary.get('critical_count', 0)}</div></div>
            <div class="summary-card high"><h3>高危漏洞</h3><div class="value">{summary.get('high_count', 0)}</div></div>
            <div class="summary-card medium"><h3>中危漏洞</h3><div class="value">{summary.get('medium_count', 0)}</div></div>
            <div class="summary-card low"><h3>低危漏洞</h3><div class="value">{summary.get('low_count', 0)}</div></div>
            <div class="summary-card"><h3>确认漏洞</h3><div class="value">{summary.get('confirmed_vulnerabilities', 0)}</div></div>
            <div class="summary-card"><h3>误报</h3><div class="value">{summary.get('false_positives', 0)}</div></div>
        </div>
        <div class="section">
            <h2>漏洞详情</h2>
            <table>
                <thead>
                    <tr><th>规则</th><th>严重程度</th><th>文件</th><th>行号</th><th>OWASP类别</th><th>描述</th></tr>
                </thead>
                <tbody>{vuln_rows if vuln_rows else '<tr><td colspan="6" style="text-align:center">未发现漏洞</td></tr>'}</tbody>
            </table>
        </div>
        <div class="section">
            <h2>修复建议</h2>
            {''.join(f'<div class="recommendation">{r}</div>' for r in verification_result.get('recommendations', []))}
        </div>
    </div>
</body>
</html>"""
        
        filepath.write_text(content, encoding="utf-8")
        return str(filepath)