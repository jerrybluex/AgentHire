-- ============================================================
-- AgentHire Test Data Seed
-- 测试数据种子脚本
-- ============================================================

-- Generate random vector (384 dimensions)
CREATE OR REPLACE FUNCTION random_vector(dim INT DEFAULT 384)
RETURNS vector AS $$
DECLARE
    arr FLOAT[];
BEGIN
    SELECT array_agg(random()::float) INTO arr
    FROM generate_series(1, dim);
    RETURN arr::vector;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- 1. Test Enterprises
-- ============================================================
INSERT INTO enterprises (id, name, display_name, unified_social_credit_code, contact, industry, company_size, company_stage, status, description) VALUES
('ent_test_001', '字节跳动', 'ByteDance', '91110108MA00XXXXXX', '{"name": "张HR", "phone": "13800138001", "email": "hr@bytedance.com", "position": "招聘经理"}', '互联网', '1000+', 'listed', 'approved', '字节跳动是全球领先的互联网公司'),
('ent_test_002', '阿里巴巴', 'Alibaba', '91110108MA00YYYYYY', '{"name": "李HR", "phone": "13800138002", "email": "hr@alibaba.com", "position": "高级招聘专员"}', '互联网/电商', '1000+', 'listed', 'approved', '让天下没有难做的生意'),
('ent_test_003', '腾讯', 'Tencent', '91110108MA00ZZZZZZ', '{"name": "王HR", "phone": "13800138003", "email": "hr@tencent.com", "position": "HRBP"}', '互联网/游戏', '1000+', 'listed', 'approved', '用户为本，科技向善'),
('ent_test_004', '美团', 'Meituan', '91110108MA00AAAAAA', '{"name": "赵HR", "phone": "13800138004", "email": "hr@meituan.com", "position": "招聘主管"}', '互联网/本地生活', '1000+', 'listed', 'approved', '帮大家吃得更好，生活更好'),
('ent_test_005', '小米', 'Xiaomi', '91110108MA00BBBBBB', '{"name": "钱HR", "phone": "13800138005", "email": "hr@xiaomi.com", "position": "技术招聘"}', '智能硬件', '1000+', 'listed', 'pending', '让每个人都能享受科技的乐趣');

-- ============================================================
-- 2. Test API Keys
-- ============================================================
INSERT INTO enterprise_api_keys (id, enterprise_id, name, api_key_hash, api_key_prefix, plan, rate_limit, monthly_quota, status) VALUES
('key_test_001', 'ent_test_001', '生产环境密钥', 'hash_placeholder_001', 'ak_001', 'monthly_pro', 1000, 10000, 'active'),
('key_test_002', 'ent_test_001', '测试环境密钥', 'hash_placeholder_002', 'ak_002', 'pay_as_you_go', 100, NULL, 'active'),
('key_test_003', 'ent_test_002', '主密钥', 'hash_placeholder_003', 'ak_003', 'monthly_enterprise', 5000, 50000, 'active'),
('key_test_004', 'ent_test_003', '招聘系统密钥', 'hash_placeholder_004', 'ak_004', 'monthly_pro', 1000, 10000, 'active'),
('key_test_005', 'ent_test_004', '默认密钥', 'hash_placeholder_005', 'ak_005', 'monthly_basic', 500, 2000, 'active');

-- ============================================================
-- 3. Test Job Postings with Vectors
-- ============================================================
INSERT INTO job_postings (id, enterprise_id, api_key_id, title, department, description, responsibilities, requirements, compensation, location, job_vector, status, match_threshold) VALUES
('post_test_001', 'ent_test_001', 'key_test_001', '高级后端工程师', '基础架构',
'负责字节跳动核心后端系统的设计与开发',
ARRAY['设计高并发系统架构', '优化数据库性能', '指导初中级工程师'],
'{"skills": ["Go", "Kubernetes", "MySQL", "Redis"], "experience_min": 5, "experience_max": 8, "education": "本科及以上"}'::jsonb,
'{"salary_min": 40000, "salary_max": 60000, "salary_months": 16, "currency": "CNY", "benefits": ["五险一金", "补充医疗", "免费三餐", "租房补贴"]}'::jsonb,
'{"city": "北京", "district": "海淀区", "remote_policy": "hybrid"}'::jsonb,
random_vector(),
'active', 0.75),

('post_test_002', 'ent_test_001', 'key_test_001', '算法工程师', 'AI Lab',
'负责推荐算法和NLP模型的研发',
ARRAY['设计和优化推荐算法', '构建大规模机器学习系统', '发表顶级会议论文'],
'{"skills": ["Python", "PyTorch", "TensorFlow", "机器学习"], "experience_min": 3, "experience_max": 6, "education": "硕士及以上"}'::jsonb,
'{"salary_min": 50000, "salary_max": 80000, "salary_months": 16, "currency": "CNY", "benefits": ["五险一金", "股票期权", "免费三餐"]}'::jsonb,
'{"city": "北京", "district": "海淀区", "remote_policy": "onsite"}'::jsonb,
random_vector(),
'active', 0.80),

('post_test_003', 'ent_test_002', 'key_test_003', 'Java开发专家', '淘宝技术部',
'负责淘宝核心交易系统的架构升级',
ARRAY['交易系统架构设计', '高可用系统保障', '技术方案评审'],
'{"skills": ["Java", "Spring", "Dubbo", "RocketMQ"], "experience_min": 5, "experience_max": 10, "education": "本科及以上"}'::jsonb,
'{"salary_min": 45000, "salary_max": 70000, "salary_months": 16, "currency": "CNY", "benefits": ["五险一金", "股票期权", "购房补贴"]}'::jsonb,
'{"city": "杭州", "district": "余杭区", "remote_policy": "hybrid"}'::jsonb,
random_vector(),
'active', 0.70),

('post_test_004', 'ent_test_003', 'key_test_004', '游戏客户端开发', '天美工作室',
'负责王者荣耀等游戏客户端开发',
ARRAY['游戏客户端功能开发', '性能优化', '新技术预研'],
'{"skills": ["C++", "Unity3D", "图形学", "游戏开发"], "experience_min": 3, "experience_max": 7, "education": "本科及以上"}'::jsonb,
'{"salary_min": 35000, "salary_max": 55000, "salary_months": 18, "currency": "CNY", "benefits": ["五险一金", "项目奖金", "免费晚餐"]}'::jsonb,
'{"city": "深圳", "district": "南山区", "remote_policy": "onsite"}'::jsonb,
random_vector(),
'active', 0.65),

('post_test_005', 'ent_test_004', 'key_test_005', '前端工程师', '到店事业群',
'负责美团到店业务前端开发',
ARRAY['前端架构设计', '性能优化', '组件库建设'],
'{"skills": ["JavaScript", "React", "Vue", "TypeScript"], "experience_min": 3, "experience_max": 5, "education": "本科及以上"}'::jsonb,
'{"salary_min": 30000, "salary_max": 45000, "salary_months": 15, "currency": "CNY", "benefits": ["五险一金", "补充医疗", "带薪年假"]}'::jsonb,
'{"city": "北京", "district": "朝阳区", "remote_policy": "hybrid"}'::jsonb,
random_vector(),
'active', 0.70),

('post_test_006', 'ent_test_002', 'key_test_003', '云原生架构师', '阿里云',
'负责阿里云容器服务架构设计',
ARRAY['云原生架构设计', 'Kubernetes二次开发', '开源社区贡献'],
'{"skills": ["Go", "Kubernetes", "Docker", "etcd"], "experience_min": 5, "experience_max": 10, "education": "本科及以上"}'::jsonb,
'{"salary_min": 50000, "salary_max": 80000, "salary_months": 16, "currency": "CNY", "benefits": ["五险一金", "股票期权", "技术影响力"]}'::jsonb,
'{"city": "杭州", "district": "西湖区", "remote_policy": "hybrid"}'::jsonb,
random_vector(),
'active', 0.75),

('post_test_007', 'ent_test_001', 'key_test_002', '数据工程师', '数据平台',
'负责大数据平台的建设和优化',
ARRAY['数据仓库建设', '实时计算系统', '数据治理'],
'{"skills": ["Python", "Spark", "Flink", "Hive"], "experience_min": 3, "experience_max": 6, "education": "本科及以上"}'::jsonb,
'{"salary_min": 35000, "salary_max": 50000, "salary_months": 16, "currency": "CNY", "benefits": ["五险一金", "免费三餐", "租房补贴"]}'::jsonb,
'{"city": "上海", "district": "徐汇区", "remote_policy": "hybrid"}'::jsonb,
random_vector(),
'active', 0.70),

('post_test_008', 'ent_test_003', 'key_test_004', '安全工程师', '安全中心',
'负责公司安全体系建设',
ARRAY['安全架构设计', '渗透测试', '安全运营'],
'{"skills": ["网络安全", "渗透测试", "安全开发", "Python"], "experience_min": 4, "experience_max": 8, "education": "本科及以上"}'::jsonb,
'{"salary_min": 40000, "salary_max": 65000, "salary_months": 16, "currency": "CNY", "benefits": ["五险一金", "股票期权", "安全奖金"]}'::jsonb,
'{"city": "深圳", "district": "南山区", "remote_policy": "onsite"}'::jsonb,
random_vector(),
'active', 0.65);

-- ============================================================
-- 4. Test Seeker Profiles with Vectors
-- ============================================================
INSERT INTO seeker_profiles (id, agent_id, agent_type, status, nickname, job_intent, resume_data, intent_vector, privacy, match_preferences) VALUES
('prof_test_001', 'agent_001', 'openclaw', 'active', '张后端',
'{"target_roles": ["后端工程师", "架构师"], "salary_expectation": {"min_monthly": 40000, "max_monthly": 60000, "currency": "CNY"}, "location_preference": {"cities": ["北京", "杭州"], "remote": true}, "skills": [{"name": "Go", "level": "expert", "years": 5}, {"name": "Kubernetes", "level": "advanced", "years": 3}], "experience_years": 5, "job_type": "full_time"}'::jsonb,
'{"basic_info": {"name": "张三", "phone": "138****0001", "email": "zhangsan@example.com"}, "work_experience": [{"company": "某大厂", "title": "高级后端工程师", "duration": "3年"}], "education": [{"school": "某985大学", "degree": "本科", "major": "计算机科学"}], "total_work_years": 5}'::jsonb,
random_vector(),
'{"reveal_on_match": true, "public_fields": ["skills", "experience_years"]}'::jsonb,
'{"auto_match": true, "match_threshold": 0.7, "notification_enabled": true}'::jsonb),

('prof_test_002', 'agent_002', 'openclaw', 'active', '李算法',
'{"target_roles": ["算法工程师", "机器学习工程师"], "salary_expectation": {"min_monthly": 50000, "max_monthly": 80000, "currency": "CNY"}, "location_preference": {"cities": ["北京", "上海"], "remote": false}, "skills": [{"name": "Python", "level": "expert", "years": 4}, {"name": "PyTorch", "level": "expert", "years": 3}], "experience_years": 4, "job_type": "full_time"}'::jsonb,
'{"basic_info": {"name": "李四", "phone": "138****0002", "email": "lisi@example.com"}, "work_experience": [{"company": "某AI公司", "title": "算法工程师", "duration": "2年"}], "education": [{"school": "清华", "degree": "硕士", "major": "人工智能"}], "total_work_years": 4}'::jsonb,
random_vector(),
'{"reveal_on_match": true, "public_fields": ["skills", "experience_years"]}'::jsonb,
'{"auto_match": true, "match_threshold": 0.75, "notification_enabled": true}'::jsonb),

('prof_test_003', 'agent_003', 'custom', 'active', '王Java',
'{"target_roles": ["Java开发", "后端工程师"], "salary_expectation": {"min_monthly": 35000, "max_monthly": 50000, "currency": "CNY"}, "location_preference": {"cities": ["杭州"], "remote": true}, "skills": [{"name": "Java", "level": "expert", "years": 6}, {"name": "Spring", "level": "expert", "years": 5}], "experience_years": 6, "job_type": "full_time"}'::jsonb,
'{"basic_info": {"name": "王五", "phone": "138****0003", "email": "wangwu@example.com"}, "work_experience": [{"company": "某电商公司", "title": "Java专家", "duration": "4年"}], "education": [{"school": "浙大", "degree": "本科", "major": "软件工程"}], "total_work_years": 6}'::jsonb,
random_vector(),
'{"reveal_on_match": true, "public_fields": ["skills", "experience_years"]}'::jsonb,
'{"auto_match": true, "match_threshold": 0.65, "notification_enabled": true}'::jsonb),

('prof_test_004', 'agent_004', 'openclaw', 'active', '赵前端',
'{"target_roles": ["前端工程师", "全栈工程师"], "salary_expectation": {"min_monthly": 30000, "max_monthly": 45000, "currency": "CNY"}, "location_preference": {"cities": ["北京", "上海"], "remote": true}, "skills": [{"name": "JavaScript", "level": "expert", "years": 4}, {"name": "React", "level": "advanced", "years": 3}], "experience_years": 4, "job_type": "full_time"}'::jsonb,
'{"basic_info": {"name": "赵六", "phone": "138****0004", "email": "zhaoliu@example.com"}, "work_experience": [{"company": "某互联网公司", "title": "前端工程师", "duration": "3年"}], "education": [{"school": "某211大学", "degree": "本科", "major": "计算机"}], "total_work_years": 4}'::jsonb,
random_vector(),
'{"reveal_on_match": true, "public_fields": ["skills", "experience_years"]}'::jsonb,
'{"auto_match": true, "match_threshold": 0.70, "notification_enabled": true}'::jsonb),

('prof_test_005', 'agent_005', 'openclaw', 'paused', '钱数据',
'{"target_roles": ["数据工程师", "大数据开发"], "salary_expectation": {"min_monthly": 35000, "max_monthly": 55000, "currency": "CNY"}, "location_preference": {"cities": ["北京", "上海", "深圳"], "remote": true}, "skills": [{"name": "Python", "level": "expert", "years": 5}, {"name": "Spark", "level": "advanced", "years": 3}], "experience_years": 5, "job_type": "full_time"}'::jsonb,
'{"basic_info": {"name": "钱七", "phone": "138****0005", "email": "qianqi@example.com"}, "work_experience": [{"company": "某数据公司", "title": "数据工程师", "duration": "3年"}], "education": [{"school": "北航", "degree": "硕士", "major": "数据科学"}], "total_work_years": 5}'::jsonb,
random_vector(),
'{"reveal_on_match": false, "public_fields": ["skills"]}'::jsonb,
'{"auto_match": false, "match_threshold": 0.75, "notification_enabled": false}'::jsonb);

-- ============================================================
-- 5. Test Resume Files
-- ============================================================
INSERT INTO resume_files (id, profile_id, original_filename, file_path, file_size, file_type, mime_type, file_hash, parse_status, parse_confidence, is_current, version) VALUES
('res_test_001', 'prof_test_001', '张三_后端工程师_5年.pdf', 's3://resumes/prof_test_001/resume_v1.pdf', 1024000, 'pdf', 'application/pdf', 'sha256_hash_001', 'success', 0.95, true, 1),
('res_test_002', 'prof_test_002', '李四_算法工程师.pdf', 's3://resumes/prof_test_002/resume_v1.pdf', 890000, 'pdf', 'application/pdf', 'sha256_hash_002', 'success', 0.92, true, 1),
('res_test_003', 'prof_test_003', '王五_Java专家.pdf', 's3://resumes/prof_test_003/resume_v1.pdf', 1150000, 'pdf', 'application/pdf', 'sha256_hash_003', 'success', 0.88, true, 1),
('res_test_004', 'prof_test_004', '赵六_前端工程师.pdf', 's3://resumes/prof_test_004/resume_v1.pdf', 750000, 'pdf', 'application/pdf', 'sha256_hash_004', 'processing', NULL, true, 1),
('res_test_005', 'prof_test_005', '钱七_数据工程师.pdf', 's3://resumes/prof_test_005/resume_v1.pdf', 980000, 'pdf', 'application/pdf', 'sha256_hash_005', 'pending', NULL, true, 1);

-- ============================================================
-- 6. Test Job Matches
-- ============================================================
INSERT INTO job_matches (id, seeker_id, job_id, match_score, match_factors, status, seeker_response, employer_response, outcome) VALUES
('match_test_001', 'prof_test_001', 'post_test_001', 0.92, '{"skill_match": 0.95, "experience_match": 1.0, "location_match": 0.9, "salary_match": 0.85, "vector_similarity": 0.90}'::jsonb, 'seeker_responded', 'interested', 'interested', NULL),
('match_test_002', 'prof_test_001', 'post_test_006', 0.88, '{"skill_match": 0.90, "experience_match": 1.0, "location_match": 0.8, "salary_match": 0.85, "vector_similarity": 0.88}'::jsonb, 'pending', NULL, NULL, NULL),
('match_test_003', 'prof_test_002', 'post_test_002', 0.95, '{"skill_match": 0.98, "experience_match": 0.9, "location_match": 1.0, "salary_match": 0.9, "vector_similarity": 0.95}'::jsonb, 'contact_shared', 'interested', 'interested', 'interview'),
('match_test_004', 'prof_test_003', 'post_test_003', 0.90, '{"skill_match": 0.95, "experience_match": 0.95, "location_match": 1.0, "salary_match": 0.8, "vector_similarity": 0.88}'::jsonb, 'employer_responded', 'interested', 'interested', NULL),
('match_test_005', 'prof_test_004', 'post_test_005', 0.85, '{"skill_match": 0.90, "experience_match": 0.85, "location_match": 0.9, "salary_match": 1.0, "vector_similarity": 0.82}'::jsonb, 'pending', NULL, NULL, NULL),
('match_test_006', 'prof_test_005', 'post_test_007', 0.78, '{"skill_match": 0.85, "experience_match": 0.8, "location_match": 0.7, "salary_match": 0.85, "vector_similarity": 0.75}'::jsonb, 'closed', 'not_interested', NULL, 'cancelled');

-- ============================================================
-- 7. Test Billing Records
-- ============================================================
INSERT INTO billing_records (id, enterprise_id, api_key_id, usage_type, quantity, unit_price, amount, currency, reference_id, reference_type, billing_period, status) VALUES
('bill_test_001', 'ent_test_001', 'key_test_001', 'job_post', 1, 5.00, 5.00, 'CNY', 'post_test_001', 'job', '2024-01', 'paid'),
('bill_test_002', 'ent_test_001', 'key_test_001', 'job_post', 1, 5.00, 5.00, 'CNY', 'post_test_002', 'job', '2024-01', 'paid'),
('bill_test_003', 'ent_test_002', 'key_test_003', 'job_post', 1, 5.00, 5.00, 'CNY', 'post_test_003', 'job', '2024-01', 'paid'),
('bill_test_004', 'ent_test_001', 'key_test_001', 'match_query', 10, 0.50, 5.00, 'CNY', NULL, NULL, '2024-01', 'paid'),
('bill_test_005', 'ent_test_001', 'key_test_001', 'match_success', 1, 10.00, 10.00, 'CNY', 'match_test_001', 'match', '2024-01', 'paid'),
('bill_test_006', 'ent_test_003', 'key_test_004', 'job_post', 1, 5.00, 5.00, 'CNY', 'post_test_004', 'job', '2024-01', 'pending'),
('bill_test_007', 'ent_test_004', 'key_test_005', 'job_post', 1, 5.00, 5.00, 'CNY', 'post_test_005', 'job', '2024-01', 'paid'),
('bill_test_008', 'ent_test_002', 'key_test_003', 'job_post', 1, 5.00, 5.00, 'CNY', 'post_test_006', 'job', '2024-01', 'paid');

-- ============================================================
-- Clean up helper function
-- ============================================================
DROP FUNCTION IF EXISTS random_vector;

-- ============================================================
-- Verification Query
-- ============================================================
-- Uncomment to verify seed data:
/*
SELECT 'Enterprises' as table_name, COUNT(*) as count FROM enterprises
UNION ALL SELECT 'API Keys', COUNT(*) FROM enterprise_api_keys
UNION ALL SELECT 'Job Postings', COUNT(*) FROM job_postings
UNION ALL SELECT 'Seeker Profiles', COUNT(*) FROM seeker_profiles
UNION ALL SELECT 'Resume Files', COUNT(*) FROM resume_files
UNION ALL SELECT 'Job Matches', COUNT(*) FROM job_matches
UNION ALL SELECT 'Billing Records', COUNT(*) FROM billing_records;
*/
