-- AgentHire 数据库迁移脚本
-- Phase 5: A2A协议和Webhook表结构
-- 创建时间: 2026-04-01

-- 启用 pgvector 扩展 (如果尚未启用)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- A2A 协议表
-- ============================================

-- A2A 意向表 - 记录求职者和雇主之间的意向表达
CREATE TABLE IF NOT EXISTS a2a_interests (
    id VARCHAR(32) PRIMARY KEY,
    profile_id VARCHAR(32) NOT NULL,
    job_id VARCHAR(32) NOT NULL,
    seeker_agent_id VARCHAR(64) NOT NULL,
    employer_agent_id VARCHAR(64) NOT NULL,
    status VARCHAR(16) DEFAULT 'pending' NOT NULL,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_interest_profile_job ON a2a_interests(profile_id, job_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_interest_profile_job_unique ON a2a_interests(profile_id, job_id);
CREATE INDEX IF NOT EXISTS idx_interest_seeker ON a2a_interests(seeker_agent_id);
CREATE INDEX IF NOT EXISTS idx_interest_employer ON a2a_interests(employer_agent_id);

-- A2A 会话表 - 记录薪资谈判和确认状态
CREATE TABLE IF NOT EXISTS a2a_sessions (
    id VARCHAR(32) PRIMARY KEY,
    interest_id VARCHAR(32) NOT NULL,
    profile_id VARCHAR(32) NOT NULL,
    job_id VARCHAR(32) NOT NULL,
    seeker_agent_id VARCHAR(64) NOT NULL,
    employer_agent_id VARCHAR(64) NOT NULL,
    status VARCHAR(16) DEFAULT 'negotiating' NOT NULL,
    current_offer JSONB,
    messages JSONB DEFAULT '[]',
    seeker_confirmed BOOLEAN DEFAULT FALSE,
    employer_confirmed BOOLEAN DEFAULT FALSE,
    contact_exchanged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_session_interest ON a2a_sessions(interest_id);
CREATE INDEX IF NOT EXISTS idx_session_profile ON a2a_sessions(profile_id);
CREATE INDEX IF NOT EXISTS idx_session_job ON a2a_sessions(job_id);
CREATE INDEX IF NOT EXISTS idx_session_status ON a2a_sessions(status);

-- ============================================
-- Webhook 表
-- ============================================

-- Webhook 注册表
CREATE TABLE IF NOT EXISTS webhooks (
    id VARCHAR(32) PRIMARY KEY,
    enterprise_id VARCHAR(32) NOT NULL,
    url TEXT NOT NULL,
    events VARCHAR(64)[] NOT NULL,
    secret VARCHAR(256) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_webhook_enterprise ON webhooks(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_webhook_active ON webhooks(active);

-- Webhook 投递记录表
CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id VARCHAR(32) PRIMARY KEY,
    webhook_id VARCHAR(32) NOT NULL,
    event VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(16) DEFAULT 'pending',
    response_status INTEGER,
    response_body TEXT,
    error_message TEXT,
    attempt_count INTEGER DEFAULT 1,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_delivery_webhook ON webhook_deliveries(webhook_id);
CREATE INDEX IF NOT EXISTS idx_delivery_status ON webhook_deliveries(status);
CREATE INDEX IF NOT EXISTS idx_delivery_event ON webhook_deliveries(event);

-- ============================================
-- 迁移完成提示
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'A2A and Webhook tables migration completed successfully!';
    RAISE NOTICE 'Created tables: a2a_interests, a2a_sessions, webhooks, webhook_deliveries';
END $$;