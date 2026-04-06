-- AgentHire 完整数据库初始化脚本
-- 在容器首次启动时自动执行

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 设置时区
SET timezone = 'Asia/Shanghai';
ALTER DATABASE agenthire SET timezone = 'Asia/Shanghai';

-- ============================================
-- Agent 表
-- ============================================
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    type VARCHAR(16) NOT NULL,
    platform VARCHAR(64),
    user_id VARCHAR(64),
    agent_secret_hash VARCHAR(256) NOT NULL,
    contact JSONB DEFAULT '{}',
    status VARCHAR(16) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agent_user_id ON agents(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_status ON agents(status);

-- ============================================
-- 企业表
-- ============================================
CREATE TABLE IF NOT EXISTS enterprises (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    unified_social_credit_code VARCHAR(32) UNIQUE,
    certification JSONB,
    contact JSONB NOT NULL,
    website VARCHAR(256),
    industry VARCHAR(64),
    company_size VARCHAR(16),
    description TEXT,
    logo_url TEXT,
    status VARCHAR(16) DEFAULT 'pending',
    billing_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_enterprise_status ON enterprises(status);
CREATE INDEX IF NOT EXISTS idx_enterprise_credit_code ON enterprises(unified_social_credit_code);

-- ============================================
-- 企业 API Key 表
-- ============================================
CREATE TABLE IF NOT EXISTS enterprise_api_keys (
    id VARCHAR(32) PRIMARY KEY,
    enterprise_id VARCHAR(32) NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    name VARCHAR(64) NOT NULL,
    api_key_hash VARCHAR(256) NOT NULL,
    api_key_prefix VARCHAR(16) NOT NULL,
    plan VARCHAR(32) DEFAULT 'pay_as_you_go',
    rate_limit INTEGER DEFAULT 100,
    monthly_quota INTEGER,
    status VARCHAR(16) DEFAULT 'active',
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_api_key_hash ON enterprise_api_keys(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_api_key_enterprise ON enterprise_api_keys(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_api_key_status ON enterprise_api_keys(status);

-- ============================================
-- 求职者 Profile 表
-- ============================================
CREATE TABLE IF NOT EXISTS seeker_profiles (
    id VARCHAR(32) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    agent_type VARCHAR(32),
    status VARCHAR(16) DEFAULT 'active',
    nickname VARCHAR(64),
    avatar_url TEXT,
    job_intent JSONB NOT NULL,
    intent_vector_id VARCHAR(64),
    privacy JSONB DEFAULT '{}',
    match_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_seeker_status ON seeker_profiles(status);
CREATE INDEX IF NOT EXISTS idx_seeker_agent_id ON seeker_profiles(agent_id);

-- ============================================
-- 简历文件表
-- ============================================
CREATE TABLE IF NOT EXISTS resume_files (
    id VARCHAR(32) PRIMARY KEY,
    profile_id VARCHAR(32) NOT NULL REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    original_filename VARCHAR(256) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(16),
    mime_type VARCHAR(64),
    parse_status VARCHAR(16) DEFAULT 'pending',
    parse_result JSONB,
    parse_confidence FLOAT,
    parsed_at TIMESTAMP WITH TIME ZONE,
    raw_text TEXT,
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resume_profile ON resume_files(profile_id);
CREATE INDEX IF NOT EXISTS idx_resume_status ON resume_files(parse_status);

-- ============================================
-- 简历解析任务表
-- ============================================
CREATE TABLE IF NOT EXISTS resume_parse_jobs (
    id VARCHAR(32) PRIMARY KEY,
    resume_file_id VARCHAR(32) NOT NULL REFERENCES resume_files(id) ON DELETE CASCADE,
    status VARCHAR(16) DEFAULT 'queued',
    result JSONB,
    error_message TEXT,
    processor_node VARCHAR(64),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_parse_job_status ON resume_parse_jobs(status);

-- ============================================
-- 职位表
-- ============================================
CREATE TABLE IF NOT EXISTS job_postings (
    id VARCHAR(32) PRIMARY KEY,
    enterprise_id VARCHAR(32) NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    api_key_id VARCHAR(32) NOT NULL,
    title VARCHAR(128) NOT NULL,
    department VARCHAR(64),
    description TEXT,
    responsibilities TEXT[],
    requirements JSONB NOT NULL,
    compensation JSONB,
    location JSONB,
    job_vector_id VARCHAR(64),
    status VARCHAR(16) DEFAULT 'active',
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    match_threshold FLOAT DEFAULT 0.7,
    auto_match BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_job_enterprise ON job_postings(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_job_status_expires ON job_postings(status, expires_at);

-- ============================================
-- 匹配记录表
-- ============================================
CREATE TABLE IF NOT EXISTS job_matches (
    id VARCHAR(32) PRIMARY KEY,
    seeker_id VARCHAR(32) NOT NULL REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    job_id VARCHAR(32) NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    match_score FLOAT NOT NULL,
    match_factors JSONB,
    status VARCHAR(16) DEFAULT 'pending',
    seeker_response VARCHAR(16),
    seeker_message TEXT,
    seeker_responded_at TIMESTAMP WITH TIME ZONE,
    employer_response VARCHAR(16),
    employer_message TEXT,
    employer_responded_at TIMESTAMP WITH TIME ZONE,
    contact_shared_at TIMESTAMP WITH TIME ZONE,
    outcome VARCHAR(16),
    feedback_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_match_seeker_status ON job_matches(seeker_id, status);
CREATE INDEX IF NOT EXISTS idx_match_job_status ON job_matches(job_id, status);
CREATE INDEX IF NOT EXISTS idx_match_score ON job_matches(match_score);

-- ============================================
-- 计费记录表
-- ============================================
CREATE TABLE IF NOT EXISTS billing_records (
    id VARCHAR(32) PRIMARY KEY,
    enterprise_id VARCHAR(32) NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    api_key_id VARCHAR(32) NOT NULL,
    usage_type VARCHAR(32) NOT NULL,
    quantity INTEGER DEFAULT 1,
    unit_price FLOAT,
    amount FLOAT,
    reference_id VARCHAR(32),
    billing_period VARCHAR(16),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_enterprise_period ON billing_records(enterprise_id, billing_period);

-- ============================================
-- A2A 协议表
-- ============================================
CREATE TABLE IF NOT EXISTS a2a_interests (
    id VARCHAR(32) PRIMARY KEY,
    profile_id VARCHAR(32) NOT NULL REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    job_id VARCHAR(32) NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,
    seeker_agent_id VARCHAR(64) NOT NULL,
    employer_agent_id VARCHAR(64) NOT NULL,
    status VARCHAR(16) DEFAULT 'pending',
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_interest_profile_job ON a2a_interests(profile_id, job_id);
CREATE INDEX IF NOT EXISTS idx_interest_seeker ON a2a_interests(seeker_agent_id);
CREATE INDEX IF NOT EXISTS idx_interest_employer ON a2a_interests(employer_agent_id);

CREATE TABLE IF NOT EXISTS a2a_sessions (
    id VARCHAR(32) PRIMARY KEY,
    interest_id VARCHAR(32) NOT NULL,
    profile_id VARCHAR(32) NOT NULL,
    job_id VARCHAR(32) NOT NULL,
    seeker_agent_id VARCHAR(64) NOT NULL,
    employer_agent_id VARCHAR(64) NOT NULL,
    status VARCHAR(16) DEFAULT 'negotiating',
    current_offer JSONB,
    messages JSONB DEFAULT '[]',
    seeker_confirmed BOOLEAN DEFAULT FALSE,
    employer_confirmed BOOLEAN DEFAULT FALSE,
    contact_exchanged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_session_interest ON a2a_sessions(interest_id);
CREATE INDEX IF NOT EXISTS idx_session_profile ON a2a_sessions(profile_id);
CREATE INDEX IF NOT EXISTS idx_session_job ON a2a_sessions(job_id);
CREATE INDEX IF NOT EXISTS idx_session_status ON a2a_sessions(status);

-- ============================================
-- Webhook 表
-- ============================================
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

CREATE INDEX IF NOT EXISTS idx_webhook_enterprise ON webhooks(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_webhook_active ON webhooks(active);

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

CREATE INDEX IF NOT EXISTS idx_delivery_webhook ON webhook_deliveries(webhook_id);
CREATE INDEX IF NOT EXISTS idx_delivery_status ON webhook_deliveries(status);
CREATE INDEX IF NOT EXISTS idx_delivery_event ON webhook_deliveries(event);

-- ============================================
-- 初始化完成提示
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'AgentHire database schema initialized successfully!';
    RAISE NOTICE 'All tables created: agents, enterprises, enterprise_api_keys, seeker_profiles, resume_files, resume_parse_jobs, job_postings, job_matches, billing_records, a2a_interests, a2a_sessions, webhooks, webhook_deliveries';
END $$;