-- AgentHire 数据库初始化脚本
-- 在容器首次启动时自动执行

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 创建数据库（如果不存在）
-- 注意：这个脚本在 docker-entrypoint-initdb.d 中执行时，
-- 数据库已经由环境变量创建好了

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建基本的数据库配置
ALTER DATABASE agenthire SET timezone = 'Asia/Shanghai';

-- 创建基本角色（可选）
-- CREATE ROLE readonly WITH LOGIN PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE agenthire TO readonly;
-- GRANT USAGE ON SCHEMA public TO readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

-- 打印初始化完成信息
DO $$
BEGIN
    RAISE NOTICE 'AgentHire database initialized successfully!';
    RAISE NOTICE 'pgvector extension enabled.';
END $$;
