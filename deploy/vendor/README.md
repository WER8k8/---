# 第三方上游源码（git submodule）

| 目录 | 上游 | 安装 |
|------|------|------|
| `UserActionAnalyzePlatform/` | [oeljeklaus-you/UserActionAnalyzePlatform](https://github.com/oeljeklaus-you/UserActionAnalyzePlatform) | `powershell -File scripts/install-user-action-analytics-vendor.ps1` |

Spark/Java **禁止**复制进 `backend/`；仅在此目录 + Sidecar 网关调用。
