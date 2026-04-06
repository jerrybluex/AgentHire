-- ============================================================
-- AgentHire Database Schema
-- PostgreSQL 15+ with pgvector extension
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Custom functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 1. SEEKER_PROFILES - 求职者档案表
-- ============================================================
CREATE TABLE seeker_profiles (
    id VARCHAR(32) PRIMARY KEY,
    agent_id VARCHAR(64) NOT NULL,
    agent_type VARCHAR(32),  -- openclaw, custom, etc.
    status VARCHAR(16) DEFAULT 'active' NOT NULL,  -- active, paused, deleted

    -- 基本信息（用户自选公开）
    nickname VARCHAR(64),
    avatar_url TEXT,

    -- 求职意图（JSON结构化）
    job_intent JSONB NOT NULL DEFAULT '{}',
    /*
    {
      "target_roles": ["后端工程师"],
      "salary_expectation": {"min_monthly": 30000, "max_monthly": 45000, "currency": "CNY"},
      "location_preference": {"cities": ["上海"], "remote": true},
      "skills": [{"name": "Go", "level": "expert", "years": 3}],
      "experience_years": 3,
      "industries": ["互联网", "电商"],
      "job_type": "full_time"
    }
    */

    -- 简历结构化数据（完整经历）
    resume_data JSONB DEFAULT '{}',
    /*
    {
      "basic_info": {"name": "...", "phone": "...", "email": "..."},
      "work_experience": [...],
      "education": [...],
      "skills": [...],
      "projects": [...],
      "total_work_years": 5.5
    }
    */

    -- 语义向量（用于匹配）- 384维，使用BGE模型
    intent_vector vector(384),

    -- 隐私设置
    privacy JSONB DEFAULT '{}',
    /*
    {
      "contact_encrypted": "...",
      "public_fields": ["skills", "experience_years"],
      "reveal_on_match": true
    }
    */

    -- 匹配设置
    match_preferences JSONB DEFAULT '{}',
    /*
    {
      "auto_match": true,
      "match_threshold": 0.7,
      "notification_enabled": true
    }
    */

    -- Webhook配置（用于推送匹配结果）
    webhook_url TEXT,
    webhook_secret VARCHAR(256),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    last_active_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for seeker_profiles
CREATE INDEX idx_seeker_status ON seeker_profiles(status);
CREATE INDEX idx_seeker_agent ON seeker_profiles(agent_id);
CREATE INDEX idx_seeker_active ON seeker_profiles(last_active_at) WHERE status = 'active';
CREATE INDEX idx_seeker_job_intent ON seeker_profiles USING GIN (job_intent);
CREATE INDEX idx_seeker_vector ON seeker_profiles USING ivfflat (intent_vector vector_cosine_ops)
    WITH (lists = 100);  -- 根据数据量调整，一般 sqrt(n/1000)

-- Trigger for updated_at
CREATE TRIGGER trigger_seeker_profiles_updated_at
    BEFORE UPDATE ON seeker_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 2. RESUME_FILES - 简历文件表
-- ============================================================
CREATE TABLE resume_files (
    id VARCHAR(32) PRIMARY KEY,
    profile_id VARCHAR(32) REFERENCES seeker_profiles(id) ON DELETE CASCADE,

    -- 文件信息
    original_filename VARCHAR(256) NOT NULL,
    file_path TEXT NOT NULL,  -- S3/MinIO路径
    file_size INTEGER CHECK (file_size > 0),  -- 字节
    file_type VARCHAR(16) NOT NULL,  -- pdf, doc, docx, jpg, png
    mime_type VARCHAR(64),
    file_hash VARCHAR(64),  -- SHA256 hash for deduplication

    -- 解析结果
    parse_status VARCHAR(16) DEFAULT 'pending' NOT NULL,  -- pending, processing, success, failed
    parse_result JSONB,  -- 解析后的结构化数据
    parse_confidence FLOAT CHECK (parse_confidence >= 0 AND parse_confidence <= 1),
    parsed_at TIMESTAMP WITH TIME ZONE,

    -- 原始文本（可选存储，用于调试和优化）
    raw_text TEXT,

    -- 版本控制
    version INTEGER DEFAULT 1 NOT NULL,
    is_current BOOLEAN DEFAULT true NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    -- 每个profile只能有一个current简历
    CONSTRAINT unique_current_resume UNIQUE (profile_id, is_current)
);

-- Indexes for resume_files
CREATE INDEX idx_resume_profile ON resume_files(profile_id);
CREATE INDEX idx_resume_status ON resume_files(parse_status);
CREATE INDEX idx_resume_current ON resume_files(profile_id, is_current) WHERE is_current = true;
CREATE INDEX idx_resume_file_hash ON resume_files(file_hash);

-- ============================================================
-- 3. RESUME_PARSE_JOBS - 简历解析任务表（异步处理）
-- ============================================================
CREATE TABLE resume_parse_jobs (
    id VARCHAR(32) PRIMARY KEY,
    resume_file_id VARCHAR(32) NOT NULL REFERENCES resume_files(id) ON DELETE CASCADE,

    -- 任务状态
    status VARCHAR(16) DEFAULT 'queued' NOT NULL,  -- queued, processing, completed, failed, cancelled
    priority INTEGER DEFAULT 5 NOT NULL CHECK (priority >= 1 AND priority <= 10),  -- 1=最高

    -- 处理结果
    result JSONB,
    error_message TEXT,
    error_code VARCHAR(32),
    retry_count INTEGER DEFAULT 0 NOT NULL,
    max_retries INTEGER DEFAULT 3 NOT NULL,

    -- 处理元信息
    processor_node VARCHAR(64),  -- 哪个节点处理的
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for resume_parse_jobs
CREATE INDEX idx_parse_job_status ON resume_parse_jobs(status, priority DESC, created_at);
CREATE INDEX idx_parse_job_file ON resume_parse_jobs(resume_file_id);
CREATE INDEX idx_parse_job_queue ON resume_parse_jobs(status, priority DESC, created_at)
    WHERE status IN ('queued', 'failed') AND retry_count < max_retries;

-- Trigger for updated_at
CREATE TRIGGER trigger_resume_parse_jobs_updated_at
    BEFORE UPDATE ON resume_parse_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 4. ENTERPRISES - 企业表
-- ============================================================
CREATE TABLE enterprises (
    id VARCHAR(32) PRIMARY KEY,

    -- 基本信息
    name VARCHAR(128) NOT NULL,
    display_name VARCHAR(128),
    unified_social_credit_code VARCHAR(32) UNIQUE,

    -- 认证材料（存储文件路径）
    certification JSONB DEFAULT '{}',
    /*
    {
      "business_license_url": "s3://...",
      "legal_person_id_url": "s3://...",
      "authorization_letter_url": "s3://...",
      "submitted_at": "2024-01-15T10:30:00Z",
      "verified_at": "2024-01-15T14:00:00Z",
      "verified_by": "admin_001",
      "rejection_reason": "..."
    }
    */

    -- 联系信息
    contact JSONB NOT NULL DEFAULT '{}',
    /*
    {
      "name": "张三",
      "phone": "13800138000",
      "email": "hr@example.com",
      "position": "HR经理"
    }
    */

    -- 企业信息
    website VARCHAR(256),
    industry VARCHAR(64),
    company_size VARCHAR(16),  -- 1-50, 50-100, 100-500, 500-1000, 1000+
    company_stage VARCHAR(32),  -- startup, growth, mature, listed
    description TEXT,
    logo_url TEXT,

    -- 认证状态
    status VARCHAR(16) DEFAULT 'pending' NOT NULL,  -- pending, approved, rejected, suspended

    -- 计费设置
    billing_info JSONB DEFAULT '{}',
    /*
    {
      "default_plan": "pay_as_you_go",
      "auto_renew": true,
      "payment_method": "alipay",
      "balance": 0.00
    }
    */

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for enterprises
CREATE INDEX idx_enterprise_status ON enterprises(status);
CREATE INDEX idx_enterprise_credit_code ON enterprises(unified_social_credit_code);
CREATE INDEX idx_enterprise_industry ON enterprises(industry);
CREATE INDEX idx_enterprise_name ON enterprises(name);

-- Trigger for updated_at
CREATE TRIGGER trigger_enterprises_updated_at
    BEFORE UPDATE ON enterprises
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 5. ENTERPRISE_API_KEYS - 企业API密钥表
-- ============================================================
CREATE TABLE enterprise_api_keys (
    id VARCHAR(32) PRIMARY KEY,
    enterprise_id VARCHAR(32) NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,

    name VARCHAR(64) NOT NULL,  -- 用户自定义名称
    api_key_hash VARCHAR(256) NOT NULL,  -- 存储hash，不存明文
    api_key_prefix VARCHAR(16) NOT NULL,  -- 前几位用于展示

    -- 套餐
    plan VARCHAR(32) DEFAULT 'pay_as_you_go' NOT NULL,
    -- pay_as_you_go: 按量计费
    -- monthly_basic: 基础包月
    -- monthly_pro: 专业包月
    -- monthly_enterprise: 企业包月

    -- 限额
    rate_limit INTEGER DEFAULT 100 NOT NULL,  -- 每分钟请求数
    monthly_quota INTEGER,  -- 包月时的月度限额
    monthly_used INTEGER DEFAULT 0,  -- 本月已使用

    -- 使用统计
    total_requests INTEGER DEFAULT 0,
    total_successful INTEGER DEFAULT 0,

    -- 状态
    status VARCHAR(16) DEFAULT 'active' NOT NULL,  -- active, revoked, expired, suspended
    expires_at TIMESTAMP WITH TIME ZONE,

    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for enterprise_api_keys
CREATE INDEX idx_api_key_hash ON enterprise_api_keys(api_key_hash);
CREATE INDEX idx_api_key_enterprise ON enterprise_api_keys(enterprise_id);
CREATE INDEX idx_api_key_status ON enterprise_api_keys(status);
CREATE INDEX idx_api_key_active ON enterprise_api_keys(enterprise_id, status) WHERE status = 'active';

-- Trigger for updated_at
CREATE TRIGGER trigger_enterprise_api_keys_updated_at
    BEFORE UPDATE ON enterprise_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 6. JOB_POSTINGS - 职位表
-- ============================================================
CREATE TABLE job_postings (
    id VARCHAR(32) PRIMARY KEY,
    enterprise_id VARCHAR(32) NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    api_key_id VARCHAR(32) NOT NULL REFERENCES enterprise_api_keys(id),

    -- 职位信息
    title VARCHAR(128) NOT NULL,
    department VARCHAR(64),
    description TEXT NOT NULL,
    responsibilities TEXT[],

    -- 要求（结构化）
    requirements JSONB NOT NULL DEFAULT '{}',
    /*
    {
      "skills": ["Go", "Kubernetes"],
      "skill_weights": {"Go": 1.0, "Kubernetes": 0.8},
      "skill_levels": {"Go": "expert", "Kubernetes": "intermediate"},
      "experience_min": 3,
      "experience_max": 5,
      "education": "bachelor",
      "languages": [{"language": "english", "level": "fluent"}]
    }
    */

    -- 薪酬
    compensation JSONB,
    /*
    {
      "salary_min": 35000,
      "salary_max": 50000,
      "currency": "CNY",
      "salary_months": 14,
      "stock_options": true,
      "benefits": ["五险一金", "补充医疗", "带薪年假"]
    }
    */

    -- 地点
    location JSONB,
    /*
    {
      "city": "上海",
      "district": "浦东新区",
      "address": "...",
      "remote_policy": "hybrid",  -- onsite, remote, hybrid
      "remote_details": "每周2天远程"
    }
    */

    -- 语义向量
    job_vector vector(384),

    -- 状态
    status VARCHAR(16) DEFAULT 'active' NOT NULL,  -- active, paused, filled, expired, draft
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,

    -- 匹配设置
    match_threshold FLOAT DEFAULT 0.7 CHECK (match_threshold >= 0 AND match_threshold <= 1),
    auto_match BOOLEAN DEFAULT true,

    -- 统计
    view_count INTEGER DEFAULT 0,
    match_count INTEGER DEFAULT 0,
    application_count INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for job_postings
CREATE INDEX idx_job_enterprise ON job_postings(enterprise_id);
CREATE INDEX idx_job_status ON job_postings(status, expires_at);
CREATE INDEX idx_job_active ON job_postings(status, published_at, expires_at)
    WHERE status = 'active';
CREATE INDEX idx_job_location ON job_postings USING GIN (location);
CREATE INDEX idx_job_requirements ON job_postings USING GIN (requirements);
CREATE INDEX idx_job_vector ON job_postings USING ivfflat (job_vector vector_cosine_ops)
    WITH (lists = 100);

-- Trigger for updated_at
CREATE TRIGGER trigger_job_postings_updated_at
    BEFORE UPDATE ON job_postings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 7. JOB_MATCHES - 匹配记录表
-- ============================================================
CREATE TABLE job_matches (
    id VARCHAR(32) PRIMARY KEY,
    seeker_id VARCHAR(32) NOT NULL REFERENCES seeker_profiles(id) ON DELETE CASCADE,
    job_id VARCHAR(32) NOT NULL REFERENCES job_postings(id) ON DELETE CASCADE,

    -- 匹配详情
    match_score FLOAT NOT NULL CHECK (match_score >= 0 AND match_score <= 1),  -- 0-1
    match_factors JSONB,  -- 各维度得分详情
    /*
    {
      "skill_match": 0.95,
      "experience_match": 0.85,
      "location_match": 1.0,
      "salary_match": 0.90,
      "vector_similarity": 0.88,
      "overall": 0.89
    }
    */

    -- 状态流转
    status VARCHAR(16) DEFAULT 'pending' NOT NULL,
    -- pending -> seeker_responded -> employer_responded -> contact_shared -> closed

    seeker_response VARCHAR(16),  -- interested, not_interested
    seeker_message TEXT,
    seeker_responded_at TIMESTAMP WITH TIME ZONE,

    employer_response VARCHAR(16),  -- interested, not_interested
    employer_message TEXT,
    employer_responded_at TIMESTAMP WITH TIME ZONE,

    contact_shared_at TIMESTAMP WITH TIME ZONE,

    -- 反馈（用于优化算法）
    outcome VARCHAR(16),  -- interview, hired, rejected, no_response, cancelled
    feedback_score INTEGER CHECK (feedback_score >= 1 AND feedback_score <= 5),  -- 1-5星评价
    feedback_comment TEXT,

    -- Webhook状态
    webhook_delivered BOOLEAN DEFAULT false,
    webhook_attempts INTEGER DEFAULT 0,
    webhook_last_error TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,

    UNIQUE(seeker_id, job_id)  -- 避免重复匹配
);

-- Indexes for job_matches
CREATE INDEX idx_match_seeker ON job_matches(seeker_id, status);
CREATE INDEX idx_match_job ON job_matches(job_id, status);
CREATE INDEX idx_match_score ON job_matches(match_score DESC);
CREATE INDEX idx_match_pending ON job_matches(status, created_at) WHERE status = 'pending';
CREATE INDEX idx_match_outcome ON job_matches(outcome) WHERE outcome IS NOT NULL;

-- Trigger for updated_at
CREATE TRIGGER trigger_job_matches_updated_at
    BEFORE UPDATE ON job_matches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 8. BILLING_RECORDS - 计费记录表
-- ============================================================
CREATE TABLE billing_records (
    id VARCHAR(32) PRIMARY KEY,
    enterprise_id VARCHAR(32) NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    api_key_id VARCHAR(32) NOT NULL REFERENCES enterprise_api_keys(id),

    -- 使用详情
    usage_type VARCHAR(32) NOT NULL,
    -- job_post: 发布职位
    -- match_query: 查询匹配
    -- match_success: 成功匹配
    -- profile_view: 查看详细档案
    -- api_call: 通用API调用

    quantity INTEGER DEFAULT 1 NOT NULL,
    unit_price DECIMAL(10, 4),  -- 单价
    amount DECIMAL(10, 2) NOT NULL,  -- 总价
    currency VARCHAR(3) DEFAULT 'CNY',

    -- 关联
    reference_id VARCHAR(32),  -- 关联的job_id或match_id
    reference_type VARCHAR(32),  -- job, match, profile

    -- 计费周期（包月时使用）
    billing_period VARCHAR(16),  -- 2024-01

    -- 状态
    status VARCHAR(16) DEFAULT 'pending' NOT NULL,  -- pending, paid, cancelled, refunded

    -- 元数据
    metadata JSONB DEFAULT '{}',
    request_ip INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Indexes for billing_records
CREATE INDEX idx_billing_enterprise ON billing_records(enterprise_id, billing_period);
CREATE INDEX idx_billing_api_key ON billing_records(api_key_id, created_at);
CREATE INDEX idx_billing_type ON billing_records(usage_type, created_at);
CREATE INDEX idx_billing_period ON billing_records(billing_period) WHERE billing_period IS NOT NULL;
CREATE INDEX idx_billing_status ON billing_records(status);
CREATE INDEX idx_billing_reference ON billing_records(reference_type, reference_id);

-- ============================================================
-- 9. AUDIT_LOGS - 审计日志表（可选，用于合规）
-- ============================================================
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    table_name VARCHAR(64) NOT NULL,
    record_id VARCHAR(32) NOT NULL,
    action VARCHAR(16) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(64),  -- user_id or api_key_id or 'system'
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    ip_address INET,
    user_agent TEXT
);

-- Indexes for audit_logs
CREATE INDEX idx_audit_table ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_time ON audit_logs(changed_at);
CREATE INDEX idx_audit_action ON audit_logs(action);

-- Partition audit_logs by month for performance (optional, for high volume)
-- CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- ============================================================
-- 10. SYSTEM_CONFIG - 系统配置表
-- ============================================================
CREATE TABLE system_config (
    id VARCHAR(64) PRIMARY KEY,
    value JSONB NOT NULL,
    description TEXT,
    updated_by VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Trigger for updated_at
CREATE TRIGGER trigger_system_config_updated_at
    BEFORE UPDATE ON system_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Comments for documentation
-- ============================================================
COMMENT ON TABLE seeker_profiles IS '求职者档案表，存储用户求职意图和向量表示';
COMMENT ON TABLE resume_files IS '简历文件表，存储原始简历文件和解析结果';
COMMENT ON TABLE resume_parse_jobs IS '简历解析任务队列，用于异步处理大文件';
COMMENT ON TABLE enterprises IS '企业信息表，包含认证状态';
COMMENT ON TABLE enterprise_api_keys IS '企业API密钥表，用于鉴权和计费';
COMMENT ON TABLE job_postings IS '职位发布表，包含语义向量用于匹配';
COMMENT ON TABLE job_matches IS '匹配记录表，记录求职者和职位的匹配结果';
COMMENT ON TABLE billing_records IS '计费记录表，记录API使用情况';
COMMENT ON TABLE audit_logs IS '审计日志表，记录数据变更历史';
COMMENT ON TABLE system_config IS '系统配置表，存储运行时配置';

-- ============================================================
-- Initial data
-- ============================================================

-- System configuration defaults
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
