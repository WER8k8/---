"""add evolution engine and deerflow tables

Revision ID: 069_add_evolution_deerflow
Revises: 4188869502e0
Create Date: 2026-08-30 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = '069_add_evolution_deerflow'
down_revision: Union[str, None] = '4188869502e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid_type():
    # 2026-09-05 P0-B：恢复方言感知（09-03 为对齐当时 VARCHAR 的 tenants.id 改硬编码
    # String(36)；现 4188869502e0 的 tenants.id 已 sweep 为 _uuid_col()=PG native uuid，
    # tenant_id/created_by 必须跟随，否则 FK DatatypeMismatch）。
    if op.get_context().dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import UUID

        return UUID(as_uuid=False)
    return sa.String(length=36)


def upgrade() -> None:
    # ============================================================
    # DeerFlow Jobs 表 (如果尚未创建)
    # 2026-09-05 P0-B：加守卫——024_deerflow_jobs 已建同名表，绿色链在此
    # DuplicateTable 崩溃；活库此前由 stamp 绕过从未真跑过本迁移。
    # ============================================================
    _upgrade_evolution_only()



def _upgrade_evolution_only() -> None:
    # ============================================================
    # Evolution Task Records 表
    # ============================================================
    op.create_table(
        'evolution_task_records',
        sa.Column('id', _uuid_type(), primary_key=True),
        sa.Column('tenant_id', _uuid_type(), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        sa.Column('task_type', sa.String(80), nullable=False, index=True),
        sa.Column('executor_type', sa.String(30), nullable=False, default='skill'),
        sa.Column('executor_id', sa.String(100), nullable=False, index=True),
        sa.Column('success', sa.Boolean, nullable=False, index=True),
        sa.Column('duration_ms', sa.Integer, default=0, nullable=False),
        sa.Column('cost', sa.Float, default=0.0, nullable=False),
        sa.Column('tokens_used', sa.Integer, default=0),
        sa.Column('error_code', sa.String(50), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('input_summary', sa.Text, nullable=True),
        sa.Column('output_summary', sa.Text, nullable=True),
        sa.Column('metadata', JSONB, default=dict),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_index('idx_evolution_task_type_success', 'evolution_task_records', ['task_type', 'success'])
    op.create_index('idx_evolution_executor_time', 'evolution_task_records', ['executor_type', 'executor_id', 'created_at'])
    op.create_index('idx_evolution_tenant_time', 'evolution_task_records', ['tenant_id', 'created_at'])

    # ============================================================
    # Evolution Experiences 表
    # ============================================================
    op.create_table(
        'evolution_experiences',
        sa.Column('id', _uuid_type(), primary_key=True),
        sa.Column('task_type', sa.String(80), nullable=False, index=True),
        sa.Column('pattern_type', sa.String(30), nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('pattern_data', JSONB, default=dict),
        sa.Column('source_record_ids', JSONB, default=list),
        sa.Column('confidence', sa.Float, default=0.5, nullable=False),
        sa.Column('occurrence_count', sa.Integer, default=1, nullable=False),
        sa.Column('applied', sa.Boolean, default=False, nullable=False, index=True),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_evolution_pattern_unapplied', 'evolution_experiences', ['pattern_type', 'applied'])
    op.create_index('idx_evolution_confidence', 'evolution_experiences', ['confidence'])

    # ============================================================
    # Skill Versions 表
    # ============================================================
    op.create_table(
        'evolution_skill_versions',
        sa.Column('id', _uuid_type(), primary_key=True),
        sa.Column('skill_id', sa.String(100), nullable=False, index=True),
        sa.Column('skill_name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, index=True),
        sa.Column('major', sa.Integer, default=0, nullable=False),
        sa.Column('minor', sa.Integer, default=0, nullable=False),
        sa.Column('patch', sa.Integer, default=0, nullable=False),
        sa.Column('status', sa.String(20), default='draft', nullable=False, index=True),
        sa.Column('prompt_template', sa.Text, nullable=True),
        sa.Column('parameters', JSONB, default=dict),
        sa.Column('changelog', sa.Text, nullable=True),
        sa.Column('based_on_experience_ids', JSONB, default=list),
        sa.Column('success_rate', sa.Float, nullable=True),
        sa.Column('avg_duration_ms', sa.Integer, nullable=True),
        sa.Column('total_invocations', sa.Integer, default=0),
        sa.Column('parent_version_id', _uuid_type(), sa.ForeignKey('evolution_skill_versions.id'), nullable=True),
        sa.Column('canary_percentage', sa.Float, default=0.0),
        sa.Column('canary_tenant_ids', JSONB, default=list),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_evolution_skill_status', 'evolution_skill_versions', ['skill_id', 'status'])
    op.create_index('idx_evolution_skill_version_unique', 'evolution_skill_versions', ['skill_id', 'version'], unique=True)

    # ============================================================
    # SOP Versions 表
    # ============================================================
    op.create_table(
        'evolution_sop_versions',
        sa.Column('id', _uuid_type(), primary_key=True),
        sa.Column('sop_id', sa.String(100), nullable=False, index=True),
        sa.Column('sop_name', sa.String(200), nullable=False),
        sa.Column('version', sa.String(20), nullable=False, index=True),
        sa.Column('major', sa.Integer, default=0, nullable=False),
        sa.Column('minor', sa.Integer, default=0, nullable=False),
        sa.Column('patch', sa.Integer, default=0, nullable=False),
        sa.Column('status', sa.String(20), default='draft', nullable=False, index=True),
        sa.Column('steps', JSONB, default=list),
        sa.Column('decision_tree', JSONB, default=dict),
        sa.Column('exception_handling', JSONB, default=dict),
        sa.Column('changelog', sa.Text, nullable=True),
        sa.Column('based_on_experience_ids', JSONB, default=list),
        sa.Column('linked_skill_version_ids', JSONB, default=list),
        sa.Column('completion_rate', sa.Float, nullable=True),
        sa.Column('avg_completion_time_ms', sa.Integer, nullable=True),
        sa.Column('total_executions', sa.Integer, default=0),
        sa.Column('parent_version_id', _uuid_type(), sa.ForeignKey('evolution_sop_versions.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_evolution_sop_status', 'evolution_sop_versions', ['sop_id', 'status'])
    op.create_index('idx_evolution_sop_version_unique', 'evolution_sop_versions', ['sop_id', 'version'], unique=True)

    # ============================================================
    # Approval Records 表
    # ============================================================
    op.create_table(
        'evolution_approvals',
        sa.Column('id', _uuid_type(), primary_key=True),
        sa.Column('target_type', sa.String(30), nullable=False, index=True),
        sa.Column('target_id', _uuid_type(), nullable=False, index=True),
        sa.Column('action', sa.String(30), nullable=False),
        sa.Column('status', sa.String(20), default='pending', nullable=False, index=True),
        sa.Column('requester', sa.String(100), nullable=False),
        sa.Column('reviewer', sa.String(100), nullable=True),
        sa.Column('review_comment', sa.Text, nullable=True),
        sa.Column('evidence', JSONB, default=dict),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_evolution_approval_pending', 'evolution_approvals', ['target_type', 'status'])

    # ============================================================
    # Canary Route Records 表
    # ============================================================
    op.create_table(
        'evolution_canary_routes',
        sa.Column('id', _uuid_type(), primary_key=True),
        sa.Column('tenant_id', _uuid_type(), nullable=True, index=True),
        sa.Column('skill_id', sa.String(100), nullable=False, index=True),
        sa.Column('routed_version', sa.String(20), nullable=True),
        sa.Column('routed_version_id', _uuid_type(), nullable=True),
        sa.Column('is_canary', sa.Boolean, default=False, nullable=False),
        sa.Column('request_hash', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )
    op.create_index('idx_evolution_canary_analysis', 'evolution_canary_routes', ['skill_id', 'is_canary', 'created_at'])

    # ============================================================
    # n8n Workflow Registry 表
    # ============================================================
    op.create_table(
        'n8n_workflows',
        sa.Column('id', _uuid_type(), primary_key=True),
        sa.Column('tenant_id', _uuid_type(), sa.ForeignKey('tenants.id'), nullable=True, index=True),
        sa.Column('workflow_id', sa.String(100), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('endpoint_url', sa.String(500), nullable=False),
        sa.Column('auth_type', sa.String(30), default='none'),
        sa.Column('auth_config', JSONB, default=dict),
        sa.Column('scene', sa.String(50), nullable=True, index=True),
        sa.Column('enabled', sa.Boolean, default=True, nullable=False),
        sa.Column('last_triggered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_n8n_workflow_scene', 'n8n_workflows', ['scene', 'enabled'])


def downgrade() -> None:
    op.drop_index('idx_n8n_workflow_scene', table_name='n8n_workflows')
    op.drop_table('n8n_workflows')
    op.drop_index('idx_evolution_canary_analysis', table_name='evolution_canary_routes')
    op.drop_table('evolution_canary_routes')
    op.drop_index('idx_evolution_approval_pending', table_name='evolution_approvals')
    op.drop_table('evolution_approvals')
    op.drop_index('idx_evolution_sop_version_unique', table_name='evolution_sop_versions')
    op.drop_index('idx_evolution_sop_status', table_name='evolution_sop_versions')
    op.drop_table('evolution_sop_versions')
    op.drop_index('idx_evolution_skill_version_unique', table_name='evolution_skill_versions')
    op.drop_index('idx_evolution_skill_status', table_name='evolution_skill_versions')
    op.drop_table('evolution_skill_versions')
    op.drop_index('idx_evolution_confidence', table_name='evolution_experiences')
    op.drop_index('idx_evolution_pattern_unapplied', table_name='evolution_experiences')
    op.drop_table('evolution_experiences')
    op.drop_index('idx_evolution_tenant_time', table_name='evolution_task_records')
    op.drop_index('idx_evolution_executor_time', table_name='evolution_task_records')
    op.drop_index('idx_evolution_task_type_success', table_name='evolution_task_records')
    op.drop_table('evolution_task_records')
    # deerflow_jobs 可能属 024（本迁移守卫跳过建表时），IF EXISTS 防二次删除崩溃
    op.execute("DROP TABLE IF EXISTS deerflow_jobs")
