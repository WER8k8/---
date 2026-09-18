# Git Push 交接说明 · 交 TRAE

> 时间：2026-09-18  
> 本机 agent：MiMo · 推送任务交由 TRAE 执行  
> 仓库路径：`C:\Users\Administrator\Documents\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix`

## 1. 远程（已配置）

```
origin = https://github.com/WER8k8/---.git
```

- `git remote -v` 本机已写好 origin  
- `git ls-remote` **可访问**（无需本机再猜地址）  
- 远程分支：`main` @ `61185c6a`（创建 .gitignore）· `master` @ `edae6538`

## 2. 本地状态

- 分支：`main`  
- HEAD：`ee437a93` feat(probe): 代码实测切片+主链演示注水脚本  
- 与 `origin/main` 关系：**分叉**  
  - 本地领先约 **32** 个提交（优丁全量开发）  
  - 远程独有 **2** 个提交（Initial commit + 创建 .gitignore）  
  - **非祖先关系**（远程是空壳脚手架，本地是完整工作树历史）

## 3. 本机已尝试、失败原因

```text
git push -u origin main:refs/heads/youding-dev-20260918
→ error: RPC failed; curl 55 OpenSSL SSL_read: unexpected eof
→ send-pack: unexpected disconnect
```

网络/大包传输中断，**不是**权限或 remote 配错。TRAE 侧建议：

1. 配置 `git config http.postBuffer 524288000`（或更大）  
2. 浅推或分批：先 `git push origin ee437a93:refs/heads/youding-dev-20260918` 单分支  
3. 或 `git push --depth=1` 探测连通后再全量  
4. 失败重试；必要时换网络/代理

## 4. 推荐推送策略（勿直接覆盖远程 main）

远程 main 仅有 2 个空壳提交，与本地历史无关。

**推荐（安全）**

```powershell
cd 上线网站.worktrees\agents-install-vscode-cline-deploy-strix
git remote -v   # 应显示 origin https://github.com/WER8k8/---.git
git fetch origin
git config http.postBuffer 524288000
git push -u origin main:refs/heads/youding-dev-20260918
```

推成功后可选（**需主理人明确同意再做**）：

```powershell
# 将本地 main 设为远程 main（覆盖空壳；非 fast-forward）
git push -u origin main:main --force-with-lease
```

**禁止**：未确认前 `git push --force` 到 main；禁止改 origin URL 为编造地址。

## 5. 不要提交的内容

- `docs/softcopy_youding_src.zip`（软著包，刻意不入库）  
- `static/`（若为本地生成物）  
- `backend/.env` / `config/dev/.env`（密钥与本地路径，已在 gitignore）

## 6. 交接后自检

```powershell
git status -sb
git log origin/youding-dev-20260918 -1 --oneline
# 期望：远程备份分支 HEAD = ee437a93 或更新
```

## 7. 联系口径

- 推送成功：回复「备份分支 URL + HEAD」  
- 仍失败：附完整 git 错误原文，勿改 remote 重试编造地址  
- 主理人口令：`push` / `继续` / `提交`
