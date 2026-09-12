"""Add pgvector extension and vector columns for AI recommendation system

Revision ID: 020_add_pgvector
Revises: 017_add_tenant_custom_domains
Create Date: 2026-05-23 06:30:00.000000

2026-09-05 P0-B 绿色链修复：本迁移改写为守卫式空操作。理由（实测判定）：
1. 目标表错误——`content` 表不存在（模型实际为 `content_pages`），空库 PG 在
   `ALTER TABLE content ADD title_body_vector` 处必崩（relation does not exist）。
2. 即使表名修正也无法工作——`float[]` 列配 `USING ivfflat (... vector_cosine_ops)`
   与 `<=>` 算子是 pgvector `vector` 类型专属；且函数签名 `RETURNS TABLE(id int)`
   与 products.id (uuid) 不匹配；末行 `logging` 从未 import（NameError）。
3. 功能面死代码——app/ 全仓对 6 个向量列与 3 个搜索/推荐函数 0 引用；
   模型亦无这些列，create_all 不产出 → 真执行只会造成绿色链与活库 schema 漂移。
4. SQLite 侧本迁移在 pgvector 不可用时早已静默跳过，行为不变。

pgvector 扩展本身保留 `CREATE EXTENSION IF NOT EXISTS`（幂等无害）：
ai_knowledge/geo_sourcechain 等真实模型依赖 vector 类型，扩展可用时创建之，
不可用时（无权限/镜像不含）静默跳过，与历史行为一致。
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '020_add_pgvector'
down_revision = '017_add_tenant_custom_domains'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        try:
            op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception:
            # pgvector 不可用（镜像不含扩展或权限不足）：与历史 SQLite 行为一致，静默跳过
            pass


def downgrade() -> None:
    # 空操作的逆操作仍是空操作；绝不 DROP EXTENSION vector——
    # 旧 downgrade 的 DROP 会摧毁 ai_knowledge/geo_sourcechain 真实依赖的扩展。
    pass
