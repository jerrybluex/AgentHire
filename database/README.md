# Database Agent - Week 1 任务分配

## 角色职责
负责PostgreSQL数据库设计、pgvector扩展配置和Alembic迁移管理

## Week 1 目标
完成数据库Schema设计，搭建PostgreSQL + pgvector环境，创建初始迁移

## 具体任务清单

### 1. 数据库设计文档 (优先级: P0)
- [ ] 创建 `database/schemas/ER_diagram.md`
  - 根据PRD第5章整理完整ER图
  - 标注主键、外键、索引

- [ ] 创建 `database/schemas/tables.md`
  - 每个表的详细字段说明
  - 字段类型、约束、默认值
  - 注释说明

### 2. SQL Schema文件 (优先级: P0)
- [ ] 创建 `database/schemas/01_init.sql`
  - 启用pgvector扩展: `CREATE EXTENSION IF NOT EXISTS vector;`
  - 创建schema: `CREATE SCHEMA IF NOT EXISTS agenthire;`

- [ ] 创建 `database/schemas/02_seeker_profiles.sql`
  - 求职者档案表
  - 包含vector(384)字段用于语义向量
  - JSONB字段用于灵活存储

- [ ] 创建 `database/schemas/03_resume_files.sql`
  - 简历文件表
  - 解析状态跟踪

- [ ] 创建 `database/schemas/04_job_postings.sql`
  - 职位表
  - 包含vector(384)字段

- [ ] 创建 `database/schemas/05_job_matches.sql`
  - 匹配记录表
  - 复合唯一约束避免重复匹配

- [ ] 创建 `database/schemas/06_enterprises.sql`
  - 企业表
  - 认证状态管理

- [ ] 创建 `database/schemas/07_enterprise_api_keys.sql`
  - API密钥表
  - 仅存储hash，不存明文

- [ ] 创建 `database/schemas/08_billing_records.sql`
  - 计费记录表

### 3. Alembic配置 (优先级: P0)
- [ ] 初始化Alembic
  - 在backend目录运行: `alembic init alembic`
  - 配置 `alembic.ini`
  - 配置 `alembic/env.py` 支持异步

- [ ] 创建初始迁移脚本
  - 生成第一个revision
  - 包含所有表的创建
  - 包含pgvector扩展启用

### 4. 索引优化 (优先级: P1)
- [ ] 为所有外键创建索引
- [ ] 为vector字段创建ivfflat索引
- [ ] 为常用查询字段创建索引
- [ ] 为JSONB字段创建GIN索引（如需要）

### 5. 种子数据 (优先级: P1)
- [ ] 创建 `database/seeds/01_test_data.sql`
  - 插入测试企业数据
  - 插入测试职位数据（带向量）
  - 插入测试求职者数据（带向量）

- [ ] 创建 `database/seeds/02_sample_vectors.sql`
  - 提供384维示例向量数据
  - 用于测试匹配功能

### 6. 数据库工具脚本 (优先级: P2)
- [ ] 创建 `database/scripts/init_db.py`
  - 初始化数据库脚本
  - 创建数据库和用户
  - 执行schema文件

- [ ] 创建 `database/scripts/reset_db.py`
  - 重置数据库脚本（开发用）

## 依赖关系
- 被 Backend Agent 依赖: 提供SQLAlchemy模型定义参考
- 被 DevOps Agent 依赖: 提供初始化SQL脚本
- 输入: PRD第5章数据库设计

## 验收标准
1. pgvector扩展成功启用
2. 所有表能正常创建，无语法错误
3. Alembic迁移能正常执行
4. 向量字段能正常存储和查询
5. 种子数据能正常插入
6. 索引创建成功，explain query显示使用索引

## 关键SQL示例
```sql
-- pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 向量字段示例
intent_vector vector(384)

-- 向量索引
CREATE INDEX idx_seeker_vector ON seeker_profiles 
USING ivfflat (intent_vector vector_cosine_ops);

-- 向量查询示例
SELECT * FROM seeker_profiles 
ORDER BY intent_vector <-> '[0.1, 0.2, ...]'::vector 
LIMIT 10;
```

## 参考文档
- PRD: `/docs/PRD.md` 第5章
- pgvector文档: https://github.com/pgvector/pgvector
- Alembic文档: https://alembic.sqlalchemy.org/
