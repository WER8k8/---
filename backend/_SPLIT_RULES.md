# 超长函数拆分规范（所有 worker 必须遵守）

## 工作目录
C:\Users\Administrator.WIN-36O2UQRI3U1\Desktop\上线网站开发完成\上线网站.worktrees\agents-install-vscode-cline-deploy-strix\backend
Python: C:/Users/Administrator.WIN-36O2UQRI3U1/.workbuddy/binaries/python/versions/3.13.12/python.exe

## 目标
将分配给你的 >=100 行函数拆分为职责单一的小函数（每个 <=60 行），保持原功能 100% 不变。

## 拆分策略（按优先级）
1. **顺序段落提取**：循环体、错误处理、数据组装等独立段落 → 提为 `_xxx_<语义>` 辅助函数
2. **分支提取**：多分支 if/elif 中超过 15 行的分支 → 提取为单独函数
3. **重复代码提取**：循环内重复模式 → 提取公共函数
4. **长 docstring 压缩**：docstring 超过 15 行且是"参数说明"模板 → 压缩为 3-5 行真实描述

## 硬性规则
1. **严禁改动函数外部行为**：参数签名、返回值、异常类型、数据库操作语义完全不变
2. **每改一个文件立即 `py_compile` 校验**，语法错误必须当场修复
3. **拆分后立即重跑**：`python -c "import ast; ast.parse(open('文件').read())"` 确认解析通过
4. **备份**：修改前复制原文件到 `backend/backups/<文件名>_<时间戳>.bak`
5. **新增辅助函数必须写 3-5 行 docstring**（因为 docstring 覆盖率目标 100%）
6. **严禁删除任何函数**（包括看起来没用的）——只允许拆分和重组
7. 拆分后函数内部 **不得有超过 20 行的连续线性代码块**（除数据字典/配置字面量）
8. **不要动 git**，不要提交，只改工作区文件

## 验收标准
- 所有分配函数拆分后 <=60 行（docstring 不算，但 docstring 自身 <=15 行）
- 原文件 py_compile 通过、ast.parse 通过
- 函数命名语义化（见项目规范），禁止 a1、tmp2 之类无意义名

## 报告格式（完成后发回给 team-lead）
对每个拆分函数输出：
- 文件路径、函数名、原行数 → 新行数
- 拆出了哪些辅助函数（名称+职责）
- 采用的策略（顺序段落/分支/重复提取/docstring 压缩）
- 改动风险说明（有/无）
