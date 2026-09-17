## 任务：§17 5分钟快速回滚机制

工作目录：$BASE/backend, $BASE/deploy
产出：outputs/command-code/t11-rollback/

### 实现：
1. 数据库迁移回滚脚本：deploy/scripts/rollback-migration.sh
   - 找到当前 migration 版本，回退到上一版本
   - 数据兼容性检查（不破坏新字段的数据）

2. 应用版本快照：deploy/scripts/snapshot-version.sh
   - 每次发布前自动打标签 + 保存当前二进制/config
   - 支持 `rollback to <tag>` 一键恢复

3. 健康检查门：deploy/scripts/pre-deploy-check.sh
   - 冒烟测试通过才允许部署
   - 部署后 2分钟窗口内自动 smoke test，失败自动回滚

4. 文档：deploy/ROLLBACK.md 说明完整回滚流程
