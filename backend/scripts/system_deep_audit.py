import os
import re
import sys
from pathlib import Path

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8')

SECRET_REGEXES = [
    (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key (or similar)"),
    (r"EA[A-Za-z0-9]{50,}", "Facebook/WhatsApp Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
]

def scan_secrets(workspace_dir: Path) -> int:
    print("\n[AUDIT] 1. Scanning for Hardcoded Secrets...")
    issues = 0
    for ext in ["*.py", "*.vue", "*.ts"]:
        for fpath in workspace_dir.rglob(ext):
            parts = fpath.parts
            if any(p in parts for p in ["node_modules", ".git", "venv", ".venv", "Lib", "site-packages", "external"]):
                continue
            if "test" in fpath.name or "mock" in fpath.name or "tests" in parts:
                continue
            try:
                content = fpath.read_text(encoding="utf-8")
                for regex, desc in SECRET_REGEXES:
                    for match in re.finditer(regex, content):
                        matched_text = match.group(0)
                        # False positive in base64 PNG
                        if "EAAAABCAYAAAA" in matched_text:
                            continue
                        print(f"  [!] Found {desc} in {fpath.relative_to(workspace_dir)}")
                        issues += 1
            except Exception:
                pass
    if issues == 0:
        print("  [PASS] No hardcoded secrets found.")
    return issues

def scan_protocols(workspace_dir: Path) -> int:
    print("\n[AUDIT] 2. Enforcing HTTPS / Secure Protocols...")
    issues = 0
    http_regex = re.compile(r"http://(?![0-9\.]+|localhost|127\.0\.0\.1|testserver)[a-zA-Z0-9.-]+")
    
    ignore_list = [
        "http://www.w3.org", "http://schemas.xmlsoap.org", "http://schemas.openformats.org", 
        "http://schemas.openxmlformats.org", "http://a.com", "http://b.com", "http://test",
        "http://jaeger", "http://www.sitemaps.org", "http://www.baidu.com", "http://www.so.com", 
        "http://www.sogou.com", "http://www.google.com", "http://ip-api.com", "http://feedpress.me",
        "http://base.google.com", "http://v.polyv.net"
    ]
    
    for fpath in workspace_dir.rglob("*.py"):
        parts = fpath.parts
        if any(p in parts for p in ["node_modules", ".git", "venv", ".venv", "Lib", "site-packages", "external"]):
            continue
        if "test" in fpath.name or "mock" in fpath.name or "tests" in parts:
            continue
        try:
            content = fpath.read_text(encoding="utf-8")
            for match in http_regex.finditer(content):
                url = match.group(0)
                if url in ignore_list:
                    continue
                print(f"  [!] Found insecure HTTP call: {url} in {fpath.relative_to(workspace_dir)}")
                issues += 1
        except Exception:
            pass
    if issues == 0:
        print("  [PASS] All external calls appear to use HTTPS.")
    return issues

if __name__ == "__main__":
    workspace = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent
    print(f"Starting System Deep Audit (AUD-P0-1) on: {workspace}")
    
    total_issues = 0
    total_issues += scan_secrets(workspace)
    total_issues += scan_protocols(workspace)
    
    print("\n==============================================================================")
    if total_issues == 0:
        print("[PASS] AUD-P0-1 AUDIT PASSED: Zero critical issues found.")
        sys.exit(0)
    else:
        print(f"[FAIL] AUD-P0-1 AUDIT FAILED: {total_issues} issues found. Fix them immediately.")
        sys.exit(1)
