# S2/W2 合规与送检 · 一键脚本

```powershell
# COMP-03 说明书骨架 + HTML 草案
python scripts/generate-comp-03-manual-draft.py
python scripts/build-cert-manual-html.py

# COMP-02 / IP-04 校验
python scripts/validate-rz-60-pages.py
python scripts/ip-04-weekly-comp-k3-scan.py

# PM-03 彩排预检
backend\.venv\Scripts\python.exe scripts\pm-rehearsal-v2-check.py

# DOC-02 周报
python scripts/generate-doc-02-weekly-report.py
```
