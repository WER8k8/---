## 任务：③ 测试数据治理

工作目录：$BASE/backend
问题：14个 user_a_* mock 用户混在生产库，无清理机制
产出：outputs/anti-gravity/t13-data-cleanup/

### 实现：
1. 清理脚本：tools/cleanup_test_data.py
   - 查找所有 username LIKE 'user_a_%' 或 email LIKE '%@test.local' 的记录
   - 安全删除（检查关联数据：inquiries/orders/posts）
   - 生成清理报告

2. 测试数据隔离：
   - 在 conftest.py 中为每个测试 session 创建独立 schema 或使用事务回滚
   - 添加 pytest fixture: @pytest.fixture(scope='session') 的 test_db 自动清理

3. 定期清理 cron：scripts/cron/cleanup-orphan-data.sh
   - 每周自动清理 30天前的 test 标记数据
