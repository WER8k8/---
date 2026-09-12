# 桌面清理日志 — 2026-05-31

> 原则：**只移动、不永久删除**；开发权威仓不动；大目录中断可恢复。

## 已执行

| 动作 | 源 | 目标 | 说明 |
|------|-----|------|------|
| ✅ 移走过期重复仓 | Desktop 乱码名「假上线网站」(UTF-8 `e6b693...`) | `_archive_20260531/duplicate-stale-fake-shangxianwangzhan/` | **1946 文件**，无 admin_bff / youding-admin-kit；与真仓无关 |
| ✅ 删除空目录 | `Desktop/TREA solo 整理的源码` | — | 空文件夹 |
| ✅ 封存旧快照 | `UJ/wang  zhan` | `_archive_20260531/UJ-snapshots/wang-zhan/` | robocopy /MOV 完成（1759 文件；UJ 源目录已删除；Robocopy exit 1 = 成功） |

## 保留不动（刻意不碰）

| 路径 | 原因 |
|------|------|
| **`Desktop/上线网站`**（UTF-8 `e4b88a...`） | **唯一开发权威仓**（~5100 文件，含 BFF、kit、SOURCE-REPO） |
| **`Desktop/出海计`** | Obsidian 知识库 + docs 镜像 |
| **`UJ/website CodeBuddy`** | 历史总仓归档，仅 cherry-pick |
| **`Desktop/汇总`** | PM 历史报告，非代码但仍有参考价值 |
| **`Desktop/公司网站`** | 安装包/素材，非产品源码（未移动 exe，避免误删工具链） |

## 待用户确认 / 后续（大目录）

| 路径 | 建议 | 状态 |
|------|------|------|
| `UJ/整合好的` (~9 万文件) | 整目录移至 `_archive_20260531/UJ-snapshots/zhenghe-hao-de/` 或夜间 zip | ⏸ **未移动**（shutil 移动 30+ 分钟后进程被中止；**勿用 shutil**，改 robocopy /MOV 夜间执行） |
| `UJ/website CodeBuddy CN主板` | 若确认为空/无效可删 | 需人工确认路径类型 |
| `Desktop/公司网站/*.exe` | 可迁至 `_archive_20260531/installers/` | 未执行 |

## 关键发现（防再犯）

桌面上曾存在 **两个不同 Unicode 名称的「上线网站」**：

- **真仓**：`上线网站` = U+4E0A U+7EBF U+7F51 U+7AD9（5103 文件，当前开发）
- **假仓**：显示为 `上线网站` 实为乱码码点（1946 文件，已归档）

**IDE / 脚本请始终用**：`C:\Users\97907\Desktop\上线网站`（与 Cursor 工作区一致）。

## 归档根目录

```text
C:\Users\97907\Desktop\_archive_20260531\
├── duplicate-stale-fake-shangxianwangzhan\   # 已移走
└── UJ-snapshots\
    └── wang-zhan\                              # 已移走
```

## 验证命令

```powershell
python "C:\Users\97907\Desktop\上线网站\scripts\scan-desktop-projects.py"
```
