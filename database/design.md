# AgentHire Database Design Document

## Overview

This document describes the PostgreSQL database schema for AgentHire, an AI-powered recruitment platform.

- **Database**: PostgreSQL 15+
- **Extensions**: pgvector (for semantic search), uuid-ossp
- **Vector Dimension**: 384 (using BGE embedding model)

## ER Diagram

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   seeker_profiles   │────<│    resume_files     │────<│ resume_parse_jobs   │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ PK id               │     │ PK id               │     │ PK id               │
│    agent_id         │     │ FK profile_id       │     │ FK resume_file_id   │
│    status           │     │    original_filename│     │    status           │
│    nickname         │     │    file_path        │     │    priority         │
│    job_intent (JSON)│     │    file_size        │     │    result (JSON)    │
│    resume_data(JSON)│     │    file_type        │     │    error_message    │
│    intent_vector    │     │    parse_status     │     │    retry_count      │
│    privacy (JSON)   │     │    parse_result     │     │    created_at       │
│    match_prefs(JSON)│     │    is_current       │     └─────────────────────┘
│    webhook_url      │     │    created_at       │
│    created_at       │     └─────────────────────┘
└─────────────────────┘                │
         │                             │
         │    ┌─────────────────────┐  │
         └───<│     job_matches     │>─┘
              ├─────────────────────┤
              │ PK id               │
              │ FK seeker_id        │
              │ FK job_id           │
              │    match_score      │
              │    match_factors    │
              │    status           │
              │    seeker_response  │
              │    employer_response│
              │    outcome          │
              │    created_at       │
              └─────────────────────┘
                        │
                        │
              ┌─────────┘
              │
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   job_postings      │────<│  enterprise_api_keys│>────│    enterprises      │
├─────────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ PK id               │     │ PK id               │     │ PK id               │
│ FK enterprise_id    │     │ FK enterprise_id    │     │    name             │
│ FK api_key_id       │     │    name             │     │    display_name     │
│    title            │     │    api_key_hash     │     │    credit_code      │
│    description      │     │    api_key_prefix   │     │    certification    │
│    requirements(JSON)     │    plan             │     │    contact (JSON)   │
│    compensation(JSON)│    │    rate_limit       │     │    industry         │
│    location (JSON)  │     │    monthly_quota    │     │    company_size     │
│    job_vector       │     │    monthly_used     │     │    status           │
│    status           │     │    status           │     │    billing_info     │
│    match_threshold  │     │    expires_at       │     │    created_at       │
│    created_at       │     │    created_at       │     └─────────────────────┘
└─────────────────────┘     └─────────────────────┘              │
         │                                                       │
         │    ┌─────────────────────┐                            │
         └───<│   billing_records   │>───────────────────────────┘
              ├─────────────────────┤
              │ PK id               │
              │ FK enterprise_id    │
              │ FK api_key_id       │
              │    usage_type       │
              │    amount           │
              │    reference_id     │
              │    billing_period   │
              │    status           │
              │    created_at       │
              └─────────────────────┘

Additional Tables:
┌─────────────────────┐     ┌─────────────────────┐
│    audit_logs       │     │   system_config     │
├─────────────────────┤     ├─────────────────────┤
│ PK id (BIGSERIAL)   │     │ PK id               │
│    table_name       │     │    value (JSON)     │
│    record_id        │     │    description      │
│    action           │     │    updated_by       │
│    old_data (JSON)  │     │    created_at       │
│    new_data (JSON)  │     └─────────────────────┘
│    changed_at       │
└─────────────────────┘
```

## Table Relationships

### Core Relationships

| Parent Table | Child Table | Relationship | On Delete |
|-------------|-------------|--------------|-----------|
| seeker_profiles | resume_files | 1:N | CASCADE |
| seeker_profiles | job_matches | 1:N | CASCADE |
| resume_files | resume_parse_jobs | 1:N | CASCADE |
| enterprises | enterprise_api_keys | 1:N | CASCADE |
| enterprises | job_postings | 1:N | CASCADE |
| enterprises | billing_records | 1:N | CASCADE |
| enterprise_api_keys | job_postings | 1:N | RESTRICT |
| enterprise_api_keys | billing_records | 1:N | RESTRICT |
| job_postings | job_matches | 1:N | CASCADE |

## Table Specifications

### 1. seeker_profiles - 求职者档案表

存储求职者的基本信息、求职意图和语义向量。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: prof_xxx |
| agent_id | VARCHAR(64) | NOT NULL, INDEX | 关联的Agent ID |
| agent_type | VARCHAR(32) | | Agent类型: openclaw, custom |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'active' | 状态: active, paused, deleted |
| nickname | VARCHAR(64) | | 昵称 |
| avatar_url | TEXT | | 头像URL |
| job_intent | JSONB | NOT NULL, DEFAULT '{}' | 求职意图结构化数据 |
| resume_data | JSONB | DEFAULT '{}' | 简历结构化数据 |
| intent_vector | vector(384) | INDEX (ivfflat) | 语义向量用于匹配 |
| privacy | JSONB | DEFAULT '{}' | 隐私设置 |
| match_preferences | JSONB | DEFAULT '{}' | 匹配偏好设置 |
| webhook_url | TEXT | | 结果推送URL |
| webhook_secret | VARCHAR(256) | | Webhook签名密钥 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |
| last_active_at | TIMESTAMPTZ | DEFAULT NOW() | 最后活跃时间 |

**Indexes:**
- `idx_seeker_status` on status
- `idx_seeker_agent` on agent_id
- `idx_seeker_active` on last_active_at WHERE status = 'active'
- `idx_seeker_job_intent` GIN on job_intent
- `idx_seeker_vector` ivfflat on intent_vector

### 2. resume_files - 简历文件表

存储上传的简历文件信息和解析结果。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: res_xxx |
| profile_id | VARCHAR(32) | FK, NOT NULL, INDEX | 关联的求职者档案 |
| original_filename | VARCHAR(256) | NOT NULL | 原始文件名 |
| file_path | TEXT | NOT NULL | 存储路径(S3/MinIO) |
| file_size | INTEGER | CHECK > 0 | 文件大小(字节) |
| file_type | VARCHAR(16) | NOT NULL | 文件类型: pdf, doc, docx |
| mime_type | VARCHAR(64) | | MIME类型 |
| file_hash | VARCHAR(64) | INDEX | SHA256哈希值 |
| parse_status | VARCHAR(16) | NOT NULL, DEFAULT 'pending' | 解析状态 |
| parse_result | JSONB | | 解析结果数据 |
| parse_confidence | FLOAT | CHECK 0-1 | 解析置信度 |
| parsed_at | TIMESTAMPTZ | | 解析完成时间 |
| raw_text | TEXT | | 提取的原始文本 |
| version | INTEGER | NOT NULL, DEFAULT 1 | 版本号 |
| is_current | BOOLEAN | NOT NULL, DEFAULT true | 是否当前版本 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

**Constraints:**
- UNIQUE(profile_id, is_current) - 每个profile只能有一个current简历

**Indexes:**
- `idx_resume_profile` on profile_id
- `idx_resume_status` on parse_status
- `idx_resume_current` on (profile_id, is_current) WHERE is_current = true
- `idx_resume_file_hash` on file_hash

### 3. resume_parse_jobs - 简历解析任务表

异步处理简历解析任务队列。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: job_xxx |
| resume_file_id | VARCHAR(32) | FK, NOT NULL, INDEX | 关联的简历文件 |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'queued' | 任务状态 |
| priority | INTEGER | NOT NULL, DEFAULT 5, CHECK 1-10 | 优先级(1最高) |
| result | JSONB | | 处理结果 |
| error_message | TEXT | | 错误信息 |
| error_code | VARCHAR(32) | | 错误代码 |
| retry_count | INTEGER | NOT NULL, DEFAULT 0 | 重试次数 |
| max_retries | INTEGER | NOT NULL, DEFAULT 3 | 最大重试次数 |
| processor_node | VARCHAR(64) | | 处理节点标识 |
| started_at | TIMESTAMPTZ | | 开始处理时间 |
| completed_at | TIMESTAMPTZ | | 完成时间 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**Indexes:**
- `idx_parse_job_status` on (status, priority DESC, created_at)
- `idx_parse_job_file` on resume_file_id
- `idx_parse_job_queue` on (status, priority DESC, created_at) WHERE status IN ('queued', 'failed')

### 4. enterprises - 企业表

存储企业信息和认证状态。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: ent_xxx |
| name | VARCHAR(128) | NOT NULL, INDEX | 企业名称 |
| display_name | VARCHAR(128) | | 显示名称 |
| unified_social_credit_code | VARCHAR(32) | UNIQUE, INDEX | 统一社会信用代码 |
| certification | JSONB | DEFAULT '{}' | 认证材料信息 |
| contact | JSONB | NOT NULL, DEFAULT '{}' | 联系人信息 |
| website | VARCHAR(256) | | 企业官网 |
| industry | VARCHAR(64) | INDEX | 所属行业 |
| company_size | VARCHAR(16) | | 公司规模 |
| company_stage | VARCHAR(32) | | 发展阶段 |
| description | TEXT | | 企业简介 |
| logo_url | TEXT | | Logo URL |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'pending' | 认证状态 |
| billing_info | JSONB | DEFAULT '{}' | 计费设置 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |
| verified_at | TIMESTAMPTZ | | 认证通过时间 |

**Indexes:**
- `idx_enterprise_status` on status
- `idx_enterprise_credit_code` on unified_social_credit_code
- `idx_enterprise_industry` on industry
- `idx_enterprise_name` on name

### 5. enterprise_api_keys - 企业API密钥表

管理企业API访问密钥和套餐配额。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: key_xxx |
| enterprise_id | VARCHAR(32) | FK, NOT NULL, INDEX | 关联的企业 |
| name | VARCHAR(64) | NOT NULL | 密钥名称(用户自定义) |
| api_key_hash | VARCHAR(256) | NOT NULL, INDEX | API密钥哈希值 |
| api_key_prefix | VARCHAR(16) | NOT NULL | 密钥前缀(用于展示) |
| plan | VARCHAR(32) | NOT NULL, DEFAULT 'pay_as_you_go' | 套餐类型 |
| rate_limit | INTEGER | NOT NULL, DEFAULT 100 | 每分钟请求限制 |
| monthly_quota | INTEGER | | 月度配额 |
| monthly_used | INTEGER | DEFAULT 0 | 本月已使用量 |
| total_requests | INTEGER | DEFAULT 0 | 总请求数 |
| total_successful | INTEGER | DEFAULT 0 | 成功请求数 |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'active', INDEX | 密钥状态 |
| expires_at | TIMESTAMPTZ | | 过期时间 |
| last_used_at | TIMESTAMPTZ | | 最后使用时间 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**Indexes:**
- `idx_api_key_hash` on api_key_hash
- `idx_api_key_enterprise` on enterprise_id
- `idx_api_key_status` on status
- `idx_api_key_active` on (enterprise_id, status) WHERE status = 'active'

### 6. job_postings - 职位表

存储发布的职位信息和语义向量。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: post_xxx |
| enterprise_id | VARCHAR(32) | FK, NOT NULL, INDEX | 发布企业 |
| api_key_id | VARCHAR(32) | FK, NOT NULL | 使用的API密钥 |
| title | VARCHAR(128) | NOT NULL | 职位名称 |
| department | VARCHAR(64) | | 所属部门 |
| description | TEXT | NOT NULL | 职位描述 |
| responsibilities | TEXT[] | | 职责列表 |
| requirements | JSONB | NOT NULL, DEFAULT '{}' | 岗位要求 |
| compensation | JSONB | | 薪酬福利 |
| location | JSONB | | 工作地点 |
| job_vector | vector(384) | INDEX (ivfflat) | 职位语义向量 |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'active', INDEX | 职位状态 |
| published_at | TIMESTAMPTZ | DEFAULT NOW() | 发布时间 |
| expires_at | TIMESTAMPTZ | | 过期时间 |
| match_threshold | FLOAT | DEFAULT 0.7, CHECK 0-1 | 匹配阈值 |
| auto_match | BOOLEAN | DEFAULT true | 是否自动匹配 |
| view_count | INTEGER | DEFAULT 0 | 浏览次数 |
| match_count | INTEGER | DEFAULT 0 | 匹配次数 |
| application_count | INTEGER | DEFAULT 0 | 申请次数 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**Indexes:**
- `idx_job_enterprise` on enterprise_id
- `idx_job_status` on (status, expires_at)
- `idx_job_active` on (status, published_at, expires_at) WHERE status = 'active'
- `idx_job_location` GIN on location
- `idx_job_requirements` GIN on requirements
- `idx_job_vector` ivfflat on job_vector

### 7. job_matches - 匹配记录表

记录求职者和职位之间的匹配结果和交互状态。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: match_xxx |
| seeker_id | VARCHAR(32) | FK, NOT NULL | 求职者 |
| job_id | VARCHAR(32) | FK, NOT NULL | 职位 |
| match_score | FLOAT | NOT NULL, CHECK 0-1 | 匹配分数 |
| match_factors | JSONB | | 各维度得分详情 |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'pending', INDEX | 匹配状态 |
| seeker_response | VARCHAR(16) | | 求职者回应 |
| seeker_message | TEXT | | 求职者留言 |
| seeker_responded_at | TIMESTAMPTZ | | 求职者回应时间 |
| employer_response | VARCHAR(16) | | 企业回应 |
| employer_message | TEXT | | 企业留言 |
| employer_responded_at | TIMESTAMPTZ | | 企业回应时间 |
| contact_shared_at | TIMESTAMPTZ | | 联系方式交换时间 |
| outcome | VARCHAR(16) | | 最终结果 |
| feedback_score | INTEGER | CHECK 1-5 | 反馈评分 |
| feedback_comment | TEXT | | 反馈评论 |
| webhook_delivered | BOOLEAN | DEFAULT false | Webhook是否送达 |
| webhook_attempts | INTEGER | DEFAULT 0 | Webhook尝试次数 |
| webhook_last_error | TEXT | | 最后错误信息 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**Constraints:**
- UNIQUE(seeker_id, job_id) - 避免重复匹配

**Indexes:**
- `idx_match_seeker` on (seeker_id, status)
- `idx_match_job` on (job_id, status)
- `idx_match_score` on match_score DESC
- `idx_match_pending` on (status, created_at) WHERE status = 'pending'
- `idx_match_outcome` on outcome WHERE outcome IS NOT NULL

### 8. billing_records - 计费记录表

记录API使用情况和计费信息。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(32) | PRIMARY KEY | 唯一标识符，格式: bill_xxx |
| enterprise_id | VARCHAR(32) | FK, NOT NULL | 关联企业 |
| api_key_id | VARCHAR(32) | FK, NOT NULL | 关联API密钥 |
| usage_type | VARCHAR(32) | NOT NULL | 使用类型 |
| quantity | INTEGER | NOT NULL, DEFAULT 1 | 数量 |
| unit_price | DECIMAL(10,4) | | 单价 |
| amount | DECIMAL(10,2) | NOT NULL | 总价 |
| currency | VARCHAR(3) | DEFAULT 'CNY' | 货币 |
| reference_id | VARCHAR(32) | | 关联记录ID |
| reference_type | VARCHAR(32) | | 关联记录类型 |
| billing_period | VARCHAR(16) | | 计费周期 |
| status | VARCHAR(16) | NOT NULL, DEFAULT 'pending' | 计费状态 |
| metadata | JSONB | DEFAULT '{}' | 元数据 |
| request_ip | INET | | 请求IP |
| user_agent | TEXT | | User Agent |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |

**Indexes:**
- `idx_billing_enterprise` on (enterprise_id, billing_period)
- `idx_billing_api_key` on (api_key_id, created_at)
- `idx_billing_type` on (usage_type, created_at)
- `idx_billing_period` on billing_period WHERE billing_period IS NOT NULL
- `idx_billing_status` on status
- `idx_billing_reference` on (reference_type, reference_id)

### 9. audit_logs - 审计日志表

记录数据变更历史，用于合规审计。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | BIGSERIAL | PRIMARY KEY | 自增ID |
| table_name | VARCHAR(64) | NOT NULL, INDEX | 表名 |
| record_id | VARCHAR(32) | NOT NULL, INDEX | 记录ID |
| action | VARCHAR(16) | NOT NULL, INDEX | 操作类型 |
| old_data | JSONB | | 变更前数据 |
| new_data | JSONB | | 变更后数据 |
| changed_by | VARCHAR(64) | | 操作用户 |
| changed_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW(), INDEX | 变更时间 |
| ip_address | INET | | IP地址 |
| user_agent | TEXT | | User Agent |

**Indexes:**
- `idx_audit_table` on (table_name, record_id)
- `idx_audit_time` on changed_at
- `idx_audit_action` on action

### 10. system_config - 系统配置表

存储系统运行时配置。

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(64) | PRIMARY KEY | 配置项ID |
| value | JSONB | NOT NULL | 配置值 |
| description | TEXT | | 配置说明 |
| updated_by | VARCHAR(64) | | 最后更新者 |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

## Vector Search

### pgvector Configuration

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- Create vector indexes (IVFFlat)
CREATE INDEX idx_seeker_vector ON seeker_profiles 
USING ivfflat (intent_vector vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_job_vector ON job_postings 
USING ivfflat (job_vector vector_cosine_ops) WITH (lists = 100);
```

### Vector Query Examples

```sql
-- Find similar seekers to a job
SELECT sp.*, 
       sp.intent_vector <-> jp.job_vector AS distance
FROM seeker_profiles sp
CROSS JOIN job_postings jp
WHERE jp.id = 'post_xxx'
  AND sp.status = 'active'
ORDER BY sp.intent_vector <-> jp.job_vector
LIMIT 10;

-- Find similar jobs to a seeker
SELECT jp.*,
       jp.job_vector <-> sp.intent_vector AS distance
FROM job_postings jp
CROSS JOIN seeker_profiles sp
WHERE sp.id = 'prof_xxx'
  AND jp.status = 'active'
ORDER BY jp.job_vector <-> sp.intent_vector
LIMIT 10;

-- Hybrid search with score threshold
SELECT * FROM seeker_profiles
WHERE intent_vector <-> '[0.1, 0.2, ...]'::vector < 0.3
  AND status = 'active'
ORDER BY intent_vector <-> '[0.1, 0.2, ...]'::vector
LIMIT 20;
```

## Indexes Summary

### B-Tree Indexes
- Primary keys on all tables
- Foreign key columns
- Status fields for filtering
- Timestamps for sorting

### GIN Indexes (JSONB)
- `idx_seeker_job_intent` on seeker_profiles.job_intent
- `idx_job_location` on job_postings.location
- `idx_job_requirements` on job_postings.requirements

### IVFFlat Indexes (Vector)
- `idx_seeker_vector` on seeker_profiles.intent_vector
- `idx_job_vector` on job_postings.job_vector

### Partial Indexes
- `idx_seeker_active` WHERE status = 'active'
- `idx_resume_current` WHERE is_current = true
- `idx_job_active` WHERE status = 'active'
- `idx_match_pending` WHERE status = 'pending'
- `idx_api_key_active` WHERE status = 'active'

## Data Types Reference

### Status Enums

**seeker_profiles.status**: active, paused, deleted

**resume_files.parse_status**: pending, processing, success, failed

**resume_parse_jobs.status**: queued, processing, completed, failed, cancelled

**enterprises.status**: pending, approved, rejected, suspended

**enterprise_api_keys.status**: active, revoked, expired, suspended

**job_postings.status**: active, paused, filled, expired, draft

**job_matches.status**: pending, seeker_responded, employer_responded, contact_shared, closed

**job_matches.seeker_response/employer_response**: interested, not_interested

**job_matches.outcome**: interview, hired, rejected, no_response, cancelled

**billing_records.status**: pending, paid, cancelled, refunded

**billing_records.usage_type**: job_post, match_query, match_success, profile_view, api_call

## Files Location

- **SQL Schema**: `sql/01_schema.sql`
- **Alembic Migrations**: `alembic/versions/`
- **Models**: `models.py`
