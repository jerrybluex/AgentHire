"""Initial migration - Create all tables for AgentHire database

Revision ID: 001
Revises:
Create Date: 2024-01-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"pgvector\"")

    # Create update_updated_at_column function
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Create seeker_profiles table
    op.create_table(
        'seeker_profiles',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('agent_id', sa.String(64), nullable=False),
        sa.Column('agent_type', sa.String(32)),
        sa.Column('status', sa.String(16), nullable=False, server_default='active'),
        sa.Column('nickname', sa.String(64)),
        sa.Column('avatar_url', sa.Text),
        sa.Column('job_intent', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('resume_data', postgresql.JSONB, server_default='{}'),
        sa.Column('intent_vector', pgvector.sqlalchemy.Vector(384)),
        sa.Column('privacy', postgresql.JSONB, server_default='{}'),
        sa.Column('match_preferences', postgresql.JSONB, server_default='{}'),
        sa.Column('webhook_url', sa.Text),
        sa.Column('webhook_secret', sa.String(256)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_seeker_status', 'seeker_profiles', ['status'])
    op.create_index('idx_seeker_agent', 'seeker_profiles', ['agent_id'])
    op.create_index('idx_seeker_vector', 'seeker_profiles', ['intent_vector'], postgresql_using='ivfflat', postgresql_with={'lists': 100})
    op.execute("""
        CREATE TRIGGER trigger_seeker_profiles_updated_at
            BEFORE UPDATE ON seeker_profiles
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create resume_files table
    op.create_table(
        'resume_files',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('profile_id', sa.String(32), sa.ForeignKey('seeker_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_filename', sa.String(256), nullable=False),
        sa.Column('file_path', sa.Text, nullable=False),
        sa.Column('file_size', sa.Integer, sa.CheckConstraint('file_size > 0')),
        sa.Column('file_type', sa.String(16), nullable=False),
        sa.Column('mime_type', sa.String(64)),
        sa.Column('file_hash', sa.String(64)),
        sa.Column('parse_status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('parse_result', postgresql.JSONB),
        sa.Column('parse_confidence', sa.Float, sa.CheckConstraint('parse_confidence >= 0 AND parse_confidence <= 1')),
        sa.Column('parsed_at', sa.DateTime(timezone=True)),
        sa.Column('raw_text', sa.Text),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('is_current', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('profile_id', 'is_current', name='unique_current_resume'),
    )
    op.create_index('idx_resume_profile', 'resume_files', ['profile_id'])
    op.create_index('idx_resume_status', 'resume_files', ['parse_status'])
    op.create_index('idx_resume_file_hash', 'resume_files', ['file_hash'])

    # Create resume_parse_jobs table
    op.create_table(
        'resume_parse_jobs',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('resume_file_id', sa.String(32), sa.ForeignKey('resume_files.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(16), nullable=False, server_default='queued'),
        sa.Column('priority', sa.Integer, nullable=False, server_default='5'),
        sa.Column('result', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('error_code', sa.String(32)),
        sa.Column('retry_count', sa.Integer, nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer, nullable=False, server_default='3'),
        sa.Column('processor_node', sa.String(64)),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('priority >= 1 AND priority <= 10', name='check_priority_range'),
    )
    op.create_index('idx_parse_job_status', 'resume_parse_jobs', ['status'])
    op.create_index('idx_parse_job_file', 'resume_parse_jobs', ['resume_file_id'])
    op.create_index('idx_parse_job_queue', 'resume_parse_jobs', ['status', 'priority', 'created_at'])
    op.execute("""
        CREATE TRIGGER trigger_resume_parse_jobs_updated_at
            BEFORE UPDATE ON resume_parse_jobs
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create enterprises table
    op.create_table(
        'enterprises',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('display_name', sa.String(128)),
        sa.Column('unified_social_credit_code', sa.String(32), unique=True),
        sa.Column('certification', postgresql.JSONB, server_default='{}'),
        sa.Column('contact', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('website', sa.String(256)),
        sa.Column('industry', sa.String(64)),
        sa.Column('company_size', sa.String(16)),
        sa.Column('company_stage', sa.String(32)),
        sa.Column('description', sa.Text),
        sa.Column('logo_url', sa.Text),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('billing_info', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('verified_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_enterprise_status', 'enterprises', ['status'])
    op.create_index('idx_enterprise_credit_code', 'enterprises', ['unified_social_credit_code'])
    op.create_index('idx_enterprise_industry', 'enterprises', ['industry'])
    op.execute("""
        CREATE TRIGGER trigger_enterprises_updated_at
            BEFORE UPDATE ON enterprises
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create enterprise_api_keys table
    op.create_table(
        'enterprise_api_keys',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('enterprise_id', sa.String(32), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('api_key_hash', sa.String(256), nullable=False),
        sa.Column('api_key_prefix', sa.String(16), nullable=False),
        sa.Column('plan', sa.String(32), nullable=False, server_default='pay_as_you_go'),
        sa.Column('rate_limit', sa.Integer, nullable=False, server_default='100'),
        sa.Column('monthly_quota', sa.Integer),
        sa.Column('monthly_used', sa.Integer, server_default='0'),
        sa.Column('total_requests', sa.Integer, server_default='0'),
        sa.Column('total_successful', sa.Integer, server_default='0'),
        sa.Column('status', sa.String(16), nullable=False, server_default='active'),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_used_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_api_key_hash', 'enterprise_api_keys', ['api_key_hash'])
    op.create_index('idx_api_key_enterprise', 'enterprise_api_keys', ['enterprise_id'])
    op.create_index('idx_api_key_status', 'enterprise_api_keys', ['status'])
    op.execute("""
        CREATE TRIGGER trigger_enterprise_api_keys_updated_at
            BEFORE UPDATE ON enterprise_api_keys
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create job_postings table
    op.create_table(
        'job_postings',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('enterprise_id', sa.String(32), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('api_key_id', sa.String(32), sa.ForeignKey('enterprise_api_keys.id'), nullable=False),
        sa.Column('title', sa.String(128), nullable=False),
        sa.Column('department', sa.String(64)),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('responsibilities', sa.ARRAY(sa.Text)),
        sa.Column('requirements', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('compensation', postgresql.JSONB),
        sa.Column('location', postgresql.JSONB),
        sa.Column('job_vector', pgvector.sqlalchemy.Vector(384)),
        sa.Column('status', sa.String(16), nullable=False, server_default='active'),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('match_threshold', sa.Float, server_default='0.7'),
        sa.Column('auto_match', sa.Boolean, server_default='true'),
        sa.Column('view_count', sa.Integer, server_default='0'),
        sa.Column('match_count', sa.Integer, server_default='0'),
        sa.Column('application_count', sa.Integer, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint('match_threshold >= 0 AND match_threshold <= 1', name='check_threshold_range'),
    )
    op.create_index('idx_job_enterprise', 'job_postings', ['enterprise_id'])
    op.create_index('idx_job_status', 'job_postings', ['status', 'expires_at'])
    op.create_index('idx_job_vector', 'job_postings', ['job_vector'], postgresql_using='ivfflat', postgresql_with={'lists': 100})
    op.execute("""
        CREATE TRIGGER trigger_job_postings_updated_at
            BEFORE UPDATE ON job_postings
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create job_matches table
    op.create_table(
        'job_matches',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('seeker_id', sa.String(32), sa.ForeignKey('seeker_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('job_id', sa.String(32), sa.ForeignKey('job_postings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('match_score', sa.Float, nullable=False),
        sa.Column('match_factors', postgresql.JSONB),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('seeker_response', sa.String(16)),
        sa.Column('seeker_message', sa.Text),
        sa.Column('seeker_responded_at', sa.DateTime(timezone=True)),
        sa.Column('employer_response', sa.String(16)),
        sa.Column('employer_message', sa.Text),
        sa.Column('employer_responded_at', sa.DateTime(timezone=True)),
        sa.Column('contact_shared_at', sa.DateTime(timezone=True)),
        sa.Column('outcome', sa.String(16)),
        sa.Column('feedback_score', sa.Integer),
        sa.Column('feedback_comment', sa.Text),
        sa.Column('webhook_delivered', sa.Boolean, server_default='false'),
        sa.Column('webhook_attempts', sa.Integer, server_default='0'),
        sa.Column('webhook_last_error', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('seeker_id', 'job_id', name='unique_seeker_job_match'),
        sa.CheckConstraint('match_score >= 0 AND match_score <= 1', name='check_match_score_range'),
        sa.CheckConstraint('feedback_score >= 1 AND feedback_score <= 5', name='check_feedback_score_range'),
    )
    op.create_index('idx_match_seeker', 'job_matches', ['seeker_id', 'status'])
    op.create_index('idx_match_job', 'job_matches', ['job_id', 'status'])
    op.create_index('idx_match_score', 'job_matches', ['match_score'])
    op.execute("""
        CREATE TRIGGER trigger_job_matches_updated_at
            BEFORE UPDATE ON job_matches
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Create billing_records table
    op.create_table(
        'billing_records',
        sa.Column('id', sa.String(32), primary_key=True),
        sa.Column('enterprise_id', sa.String(32), sa.ForeignKey('enterprises.id', ondelete='CASCADE'), nullable=False),
        sa.Column('api_key_id', sa.String(32), sa.ForeignKey('enterprise_api_keys.id'), nullable=False),
        sa.Column('usage_type', sa.String(32), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False, server_default='1'),
        sa.Column('unit_price', sa.Float),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('currency', sa.String(3), server_default='CNY'),
        sa.Column('reference_id', sa.String(32)),
        sa.Column('reference_type', sa.String(32)),
        sa.Column('billing_period', sa.String(16)),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('request_ip', postgresql.INET),
        sa.Column('user_agent', sa.Text),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_billing_enterprise', 'billing_records', ['enterprise_id', 'billing_period'])
    op.create_index('idx_billing_api_key', 'billing_records', ['api_key_id', 'created_at'])
    op.create_index('idx_billing_type', 'billing_records', ['usage_type', 'created_at'])
    op.create_index('idx_billing_reference', 'billing_records', ['reference_type', 'reference_id'])

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('table_name', sa.String(64), nullable=False),
        sa.Column('record_id', sa.String(32), nullable=False),
        sa.Column('action', sa.String(16), nullable=False),
        sa.Column('old_data', postgresql.JSONB),
        sa.Column('new_data', postgresql.JSONB),
        sa.Column('changed_by', sa.String(64)),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('ip_address', postgresql.INET),
        sa.Column('user_agent', sa.Text),
    )
    op.create_index('idx_audit_table', 'audit_logs', ['table_name', 'record_id'])
    op.create_index('idx_audit_time', 'audit_logs', ['changed_at'])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])

    # Create system_config table
    op.create_table(
        'system_config',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('value', postgresql.JSONB, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('updated_by', sa.String(64)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.execute("""
        CREATE TRIGGER trigger_system_config_updated_at
            BEFORE UPDATE ON system_config
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Insert default system config
    op.execute("""
        INSERT INTO system_config (id, value, description) VALUES
        ('matching.default_threshold', '{"value": 0.7}', '默认匹配阈值'),
        ('matching.vector_weight', '{"value": 0.4}', '向量相似度权重'),
        ('matching.rule_weight', '{"value": 0.6}', '规则匹配权重'),
        ('pricing.pay_as_you_go.job_post', '{"value": 5.00, "currency": "CNY"}', '按量付费-发布职位单价'),
        ('pricing.pay_as_you_go.match_query', '{"value": 0.50, "currency": "CNY"}', '按量付费-查询匹配单价'),
        ('pricing.pay_as_you_go.match_success', '{"value": 10.00, "currency": "CNY"}', '按量付费-成功匹配单价'),
        ('pricing.pay_as_you_go.profile_view', '{"value": 2.00, "currency": "CNY"}', '按量付费-查看档案单价'),
        ('pricing.monthly_basic.quota', '{"value": 2000}', '基础包月-月度限额'),
        ('pricing.monthly_basic.price', '{"value": 999.00, "currency": "CNY"}', '基础包月-价格'),
        ('pricing.monthly_pro.quota', '{"value": 10000}', '专业包月-月度限额'),
        ('pricing.monthly_pro.price', '{"value": 2999.00, "currency": "CNY"}', '专业包月-价格');
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('system_config')
    op.drop_table('audit_logs')
    op.drop_table('billing_records')
    op.drop_table('job_matches')
    op.drop_table('job_postings')
    op.drop_table('enterprise_api_keys')
    op.drop_table('enterprises')
    op.drop_table('resume_parse_jobs')
    op.drop_table('resume_files')
    op.drop_table('seeker_profiles')

    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
