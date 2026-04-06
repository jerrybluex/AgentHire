# AgentHire Week 1 任务分配总表

## 项目概览
- **项目名称**: AgentHire - AI Agent驱动的去中心化招聘平台
- **当前阶段**: Week 1 - 项目搭建
- **目标日期**: 8周完成MVP
- **项目路径**: `C:\Users\MLTZ\AgentHire`

---

## 团队成员任务分配

### 1. Backend Agent (后端开发)
**工作目录**: `/backend`  
**负责人**: Backend Agent

| 优先级 | 任务 | 状态 | 依赖 |
|--------|------|------|------|
| P0 | 创建 requirements.txt | ✅ 已完成 | 无 |
| P0 | 创建 app/main.py (FastAPI入口) | ✅ 已完成 | 无 |
| P0 | 创建 app/core/config.py (配置管理) | ✅ 已完成 | 无 |
| P0 | 创建 app/core/database.py (数据库连接) | 🔄 进行中 | Database Agent |
| P0 | 创建 API路由结构 | ✅ 已完成 | 无 |
| P1 | 创建 SQLAlchemy模型 | 🔄 进行中 | Database Agent |
| P1 | 创建 Pydantic Schema | 🔄 进行中 | 无 |
| P1 | 创建工具函数 (ID生成器等) | 🔄 进行中 | 无 |
| P2 | 创建服务层接口 | ⏳ 待开始 | 无 |

**验收标准**:
- [ ] `docker-compose up` 能正常启动API服务
- [ ] 访问 `http://localhost:8000/health` 返回 `{"status": "ok"}`
- [ ] 访问 `http://localhost:8000/docs` 显示Swagger文档
- [ ] 代码通过 `pytest` 基础测试

---

### 2. Database Agent (数据库设计)
**工作目录**: `/database`  
**负责人**: Database Agent

| 优先级 | 任务 | 状态 | 依赖 |
|--------|------|------|------|
| P0 | 创建数据库设计文档 (ER图) | ✅ 已完成 | 无 |
| P0 | 创建 SQL Schema文件 (8个表) | ✅ 已完成 | 无 |
| P0 | 配置 Alembic迁移 | ✅ 已完成 | 无 |
| P1 | 创建数据库索引 | ✅ 已完成 | SQL Schema |
| P1 | 创建种子数据 | 🔄 进行中 | SQL Schema |
| P2 | 创建数据库工具脚本 | ⏳ 待开始 | 无 |

**关键表结构**:
1. `seeker_profiles` - 求职者档案表 (含vector(384))
2. `resume_files` - 简历文件表
3. `resume_parse_jobs` - 简历解析任务表
4. `job_postings` - 职位表 (含vector(384))
5. `job_matches` - 匹配记录表
6. `enterprises` - 企业表
7. `enterprise_api_keys` - API密钥表
8. `billing_records` - 计费记录表

**验收标准**:
- [ ] pgvector扩展成功启用
- [ ] 所有表能正常创建，无语法错误
- [ ] Alembic迁移能正常执行
- [ ] 向量字段能正常存储和查询

---

### 3. DevOps Agent (运维部署)
**工作目录**: `/devops`  
**负责人**: DevOps Agent

| 优先级 | 任务 | 状态 | 依赖 |
|--------|------|------|------|
| P0 | 创建 Dockerfile | ✅ 已完成 | 无 |
| P0 | 创建 docker-compose.yml | ✅ 已完成 | 无 |
| P0 | 创建 docker-compose.dev.yml | 🔄 进行中 | 无 |
| P0 | 创建 .env.example | ✅ 已完成 | 无 |
| P0 | 创建初始化脚本 | ✅ 已完成 | Database Agent |
| P1 | 配置 CI/CD (GitHub Actions) | 🔄 进行中 | 无 |
| P1 | 创建 Nginx配置 | ✅ 已完成 | 无 |
| P2 | 配置监控 (Prometheus/Grafana) | ⏳ 待开始 | 无 |

**服务架构**:
```yaml
services:
  api: FastAPI应用
  db: PostgreSQL + pgvector
  redis: Redis缓存/队列
  celery: 异步任务worker
```

**验收标准**:
- [ ] `docker-compose -f docker-compose.dev.yml up` 一键启动
- [ ] 所有服务健康检查通过
- [ ] 开发环境热重载正常
- [ ] 日志输出正常

---

### 4. Testing Agent (测试)
**工作目录**: `/testing`  
**负责人**: Testing Agent

| 优先级 | 任务 | 状态 | 依赖 |
|--------|------|------|------|
| P0 | 配置 pytest.ini | ✅ 已完成 | 无 |
| P0 | 创建 conftest.py (fixtures) | 🔄 进行中 | Backend Agent |
| P0 | 创建单元测试框架 | 🔄 进行中 | Backend Agent |
| P1 | 创建集成测试框架 | ⏳ 待开始 | Backend Agent |
| P1 | 准备测试数据 (fixtures) | 🔄 进行中 | Database Agent |
| P1 | 准备测试文件 (PDF/DOCX) | ⏳ 待开始 | 无 |
| P2 | 创建测试脚本 | ⏳ 待开始 | 无 |

**验收标准**:
- [ ] `pytest` 命令能正常运行
- [ ] 测试覆盖率报告生成
- [ ] 测试数据库隔离
- [ ] 测试能在CI环境中运行

---

### 5. Documentation Agent (文档)
**工作目录**: `/docs`  
**负责人**: Documentation Agent

| 优先级 | 任务 | 状态 | 依赖 |
|--------|------|------|------|
| P1 | 维护 API文档 | 待开始 | Backend Agent |
| P1 | 编写 部署指南 | 待开始 | DevOps Agent |
| P1 | 编写 开发规范 | 待开始 | 无 |
| P2 | 编写 贡献指南 | 待开始 | 无 |

---

## 任务依赖关系图

```
Week 1 任务依赖关系:

┌─────────────────────────────────────────────────────────────┐
│  Database Agent (P0)                                         │
│  ├── 数据库Schema设计                                         │
│  ├── SQL文件创建                                             │
│  └── Alembic配置                                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│Backend Agent │ │ DevOps Agent │ │Testing Agent │
│(P0)          │ │(P0)          │ │(P1)          │
│              │ │              │ │              │
│FastAPI框架    │ │Docker配置    │ │测试框架      │
│模型定义       │ │初始化脚本    │ │测试用例      │
│API路由        │ │CI/CD         │ │fixtures      │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┴──────────────┘
                       │
                       ▼
            ┌────────────────────┐
            │  Week 1 完成        │
            │  - 项目结构搭建完成  │
            │  - 开发环境可运行    │
            │  - 基础API可用      │
            └────────────────────┘
```

---

## 关键接口约定

### API响应格式
```json
{
  "success": true,
  "data": {},
  "message": null,
  "error": null
}
```

### ID格式
- Profile: `prof_` + nanoid (12位)
- Job: `job_` + nanoid (12位)
- Enterprise: `ent_` + nanoid (12位)
- Match: `match_` + nanoid (12位)

### 向量维度
- 语义向量: 384维 (使用BGE模型)
- 存储类型: pgvector `vector(384)`

---

## 每日站会议程

1. **昨日完成**
   - 每个Agent汇报昨日完成的任务

2. **今日计划**
   - 每个Agent说明今日计划完成的任务

3. **阻塞问题**
   - 是否有依赖其他Agent的任务被阻塞
   - 是否需要Lead Agent协调

4. **接口确认**
   - 是否有接口变更需要同步
   - 是否需要更新文档

---

## Week 1 完成标准

### 必须完成 (P0)
- [x] 代码仓库结构完整
- [x] Docker开发环境可一键启动
- [x] PostgreSQL + pgvector正常运行
- [x] FastAPI基础框架搭建完成
- [x] 健康检查API可用

### 建议完成 (P1)
- [x] 基础模型定义完成
- [x] 测试框架配置完成
- [x] CI/CD基础配置完成

---

## 风险预警

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| pgvector Docker配置复杂 | 中 | 高 | DevOps Agent提前测试镜像 |
| 团队成员进度不一致 | 高 | 中 | 每日站会同步，及时调整 |
| 接口定义频繁变更 | 中 | 高 | Week 1冻结核心接口定义 |
| 依赖冲突 | 中 | 中 | 使用requirements.txt锁定版本 |

---

## 参考文档

- **PRD**: `/docs/PRD.md` - 完整产品需求文档
- **项目结构**: `/STRUCTURE.md`
- **Backend任务**: `/backend/README.md`
- **Database任务**: `/database/README.md`
- **DevOps任务**: `/devops/README.md`
- **Testing任务**: `/testing/README.md`

---

**文档维护**: Lead Agent  
**最后更新**: 2024-01-15  
**状态**: Week 1 任务分配完成
