"""Add PRD v2 models

Revision ID: 002
Revises: 001
Create Date: 2026-04-05 22:11:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # Create new tables (in dependency order)
    # -------------------------------------------------------------------------

    # 1. tenants - 租户隔离空间
    op.create_table(
        'tenants',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),  # enterprise | individual
        sa.Column('status', sa.String(length=16), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # 2. principals - 主体（人/Agent/Service）
    op.create_table(
        'principals',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=64), nullable=False),
        sa.Column('type', sa.String(length=16), nullable=False),  # human | agent | service
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('email', sa.String(length=256), nullable=True),
        sa.Column('status', sa.String(length=16), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
    )
    op.create_index('idx_principals_tenant_id', 'principals', ['tenant_id'])

    # 3. credentials - 认证凭据
    op.create_table(
        'credentials',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('principal_id', sa.String(length=64), nullable=False),
        sa.Column('type', sa.String(length=32), nullable=False),  # api_key | agent_secret | password
        sa.Column('key_hash', sa.String(length=256), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('status', sa.String(length=16), server_default='active'),  # active | revoked | expired
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['principal_id'], ['principals.id']),
    )
    op.create_index('idx_credentials_principal_id', 'credentials', ['principal_id'])

    # 4. enterprise_verification_cases - 企业审核案例
    op.create_table(
        'enterprise_verification_cases',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('enterprise_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('submitted_by', sa.String(length=64), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by', sa.String(length=64), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_comment', sa.Text, nullable=True),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['enterprise_id'], ['enterprises.id']),
    )
    op.create_index('idx_evc_enterprise_id', 'enterprise_verification_cases', ['enterprise_id'])

    # 5. job_versions - 职位版本化管理
    op.create_table(
        'job_versions',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('job_id', sa.String(length=64), nullable=False),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('title', sa.String(length=256), nullable=False),
        sa.Column('department', sa.String(length=128), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('requirements', postgresql.JSONB, server_default='{}'),
        sa.Column('compensation', postgresql.JSONB, server_default='{}'),
        sa.Column('location', postgresql.JSONB, server_default='{}'),
        sa.Column('status', sa.String(length=16), server_default='active'),
        sa.Column('created_by', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['job_postings.id']),
    )
    op.create_index('idx_job_versions_job_id', 'job_versions', ['job_id'])

    # 6. application_events - 申请事件流
    op.create_table(
        'application_events',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('application_id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=32), nullable=False),  # submitted | viewed | status_changed | etc
        sa.Column('from_status', sa.String(length=32), nullable=True),
        sa.Column('to_status', sa.String(length=32), nullable=False),
        sa.Column('actor_type', sa.String(length=16), nullable=False),  # employer | agent | system
        sa.Column('actor_id', sa.String(length=64), nullable=True),
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
    )
    op.create_index('idx_app_events_application_id', 'application_events', ['application_id'])

    # 7. contact_unlocks - 联系方式解锁
    op.create_table(
        'contact_unlocks',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('application_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),  # locked | candidate_authorized | unlocked | revoked
        sa.Column('authorized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('unlocked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reason', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id']),
    )
    op.create_index('idx_contact_unlocks_application_id', 'contact_unlocks', ['application_id'])

    # -------------------------------------------------------------------------
    # Add columns to existing tables
    # -------------------------------------------------------------------------

    # 8. agents - add tenant_id and principal_id
    op.add_column('agents', sa.Column('tenant_id', sa.String(length=64), nullable=True))
    op.add_column('agents', sa.Column('principal_id', sa.String(length=64), nullable=True))
    op.create_foreign_key('fk_agents_tenant_id', 'agents', 'tenants', ['tenant_id'], ['id'])
    op.create_foreign_key('fk_agents_principal_id', 'agents', 'principals', ['principal_id'], ['id'])

    # 9. enterprises - add tenant_id
    op.add_column('enterprises', sa.Column('tenant_id', sa.String(length=64), nullable=True))
    op.create_foreign_key('fk_enterprises_tenant_id', 'enterprises', 'tenants', ['tenant_id'], ['id'])

    # 10. job_postings - add tenant_id
    op.add_column('job_postings', sa.Column('tenant_id', sa.String(length=64), nullable=True))
    op.create_foreign_key('fk_job_postings_tenant_id', 'job_postings', 'tenants', ['tenant_id'], ['id'])

    # 11. applications - add applicant_principal_id
    op.add_column('applications', sa.Column('applicant_principal_id', sa.String(length=64), nullable=True))


def downgrade() -> None:
    # Remove columns from existing tables
    op.drop_column('applications', 'applicant_principal_id')
    op.drop_constraint('fk_job_postings_tenant_id', 'job_postings', type_='foreignkey')
    op.drop_column('job_postings', 'tenant_id')
    op.drop_constraint('fk_enterprises_tenant_id', 'enterprises', type_='foreignkey')
    op.drop_column('enterprises', 'tenant_id')
    op.drop_constraint('fk_agents_principal_id', 'agents', type_='foreignkey')
    op.drop_constraint('fk_agents_tenant_id', 'agents', type_='foreignkey')
    op.drop_column('agents', 'principal_id')
    op.drop_column('agents', 'tenant_id')

    # Drop new tables (reverse dependency order)
    op.drop_table('contact_unlocks')
    op.drop_table('application_events')
    op.drop_table('job_versions')
    op.drop_table('enterprise_verification_cases')
    op.drop_table('credentials')
    op.drop_table('principals')
    op.drop_table('tenants')
