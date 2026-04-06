# AgentHire

> **让Agent为人类工作，而不是人类为招聘网站工作**

AgentHire 是一个AI Agent驱动的去中心化招聘协议，通过开放API让个人Agent和企业Agent成为求职者和招聘方的智能中介，实现简历自动解析、语义匹配和双向推荐。

---

## 核心特性

- **自然语言交互** - 求职者只需对Agent描述需求，无需反复填写简历
- **智能简历解析** - 支持PDF/Word/图片简历自动提取结构化信息
- **语义向量匹配** - 基于384维语义向量实现精准人岗匹配
- **开放协议** - 标准Skill API，任何Agent均可接入
- **数据主权** - 用户完全控制自己的数据，支持导出和迁移

---

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (本地开发)

### 1. 克隆项目

```bash
git clone https://github.com/your-org/agenthire.git
cd agenthire
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的API密钥
```

### 3. 启动服务

```bash
# 一键启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### 4. 验证安装

```bash
# 健康检查
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

### 5. 停止服务

```bash
docker-compose down

# 清除数据（谨慎使用）
docker-compose down -v
```

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              接入层 (Access Layer)                           │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  OpenClaw Agent  │  Custom Agent  │  Web Dashboard  │  Mobile App     │  │
│  └──────────────────┴────────────────┴─────────────────┴─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              协议层 (Protocol Layer)                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    AgentHire Skill API Standard                        │  │
│  │  - Intent Parsing API    - Profile Management API                      │  │
│  │  - Job Posting API       - Matching API                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              服务层 (Service Layer)                          │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │  Skill Service│  │ Matching      │  │ Enterprise    │  │ Billing      │ │
│  │  - 意图解析    │  │ Engine        │  │ Service       │  │ Service      │ │
│  │  - Profile管理 │  │ - 向量检索    │  │ - 认证审核    │  │ - 计费统计   │ │
│  │  - 数据转换    │  │ - 排序打分    │  │ - API管理    │  │ - 支付对接   │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据层 (Data Layer)                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌──────────────┐ │
│  │  Profile DB   │  │ Job Posting   │  │ Vector        │  │ Enterprise   │ │
│  │  (PostgreSQL) │  │ DB            │  │ Store         │  │ DB           │ │
│  │               │  │ (PostgreSQL)  │  │ (pgvector)    │  │ (PostgreSQL) │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └──────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         File Storage (MinIO/S3)                        │  │
│  │                    企业认证材料、简历附件等                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 层级 | 技术选型 | 版本 |
|------|---------|------|
| API框架 | FastAPI | 0.104+ |
| 数据库 | PostgreSQL + pgvector | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| 迁移 | Alembic | 1.12+ |
| 缓存 | Redis | 7+ |
| 任务队列 | Celery | 5.3+ |
| 对象存储 | MinIO / AWS S3 | - |
| 向量模型 | BGE / M3E | - |
| 部署 | Docker + Docker Compose | 20.10+ |
| 测试 | pytest | 7.4+ |

---

## 项目结构

```
AgentHire/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # SQLAlchemy模型
│   │   ├── schemas/     # Pydantic模型
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   ├── alembic/         # 数据库迁移
│   └── tests/           # 后端测试
├── database/            # 数据库相关
│   ├── migrations/      # 迁移文件
│   ├── schemas/         # SQL schema
│   └── seeds/           # 种子数据
├── devops/              # 运维配置
│   ├── docker/          # Docker配置
│   ├── nginx/           # Nginx配置
│   └── scripts/         # 部署脚本
├── testing/             # 测试
│   ├── unit/            # 单元测试
│   ├── integration/     # 集成测试
│   └── fixtures/        # 测试数据
├── docs/                # 文档
│   ├── PRD.md           # 产品需求文档
│   ├── api/             # API文档
│   ├── deployment.md    # 部署指南
│   └── contributing.md  # 贡献指南
└── scripts/             # 工具脚本
```

---

## 文档索引

- **[PRD](docs/PRD.md)** - 产品需求文档（完整功能规格）
- **[API文档](docs/api/README.md)** - API接口文档
- **[部署指南](docs/deployment.md)** - 环境搭建与部署
- **[贡献指南](docs/contributing.md)** - 代码规范与PR流程

---

## 核心API示例

### 1. 解析求职意图

```bash
curl -X POST http://localhost:8000/api/v1/skill/parse-intent \
  -H "Content-Type: application/json" \
  -d '{
    "text": "我想找上海的后端工作，30k以上，3年经验",
    "type": "seeker"
  }'
```

### 2. 上传简历解析

```bash
curl -X POST http://localhost:8000/api/v1/skill/parse-resume \
  -F "resume_file=@/path/to/resume.pdf" \
  -F "file_type=pdf"
```

### 3. 创建求职者Profile

```bash
curl -X POST http://localhost:8000/api/v1/skill/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "basic_info": {"nickname": "张三", "location": "上海"},
      "job_intent": {
        "target_roles": ["后端工程师"],
        "salary_expectation": {"min_monthly": 30000}
      }
    }
  }'
```

---

## 开发计划

| 周次 | 模块 | 关键交付物 |
|------|------|-----------|
| **Week 1** | 项目搭建 | 代码仓库、CI/CD、开发环境 |
| **Week 2** | 简历解析 | PDF/Word解析、OCR、LLM提取 |
| **Week 3** | 意图解析 | Intent Parser、LLM集成 |
| **Week 4** | Profile系统 | Profile CRUD、向量生成 |
| **Week 5** | 职位系统 | Job Posting API、企业认证 |
| **Week 6** | 匹配引擎 | 向量检索、打分算法 |
| **Week 7** | B端系统 | API Key、计费系统、Webhook |
| **Week 8** | 集成测试 | 端到端测试、部署 |

---

## 如何贡献

我们欢迎所有形式的贡献！请阅读[贡献指南](docs/contributing.md)了解详情。

### 快速开始贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 报告问题

如果你发现了bug或有新功能建议，请通过 [GitHub Issues](https://github.com/your-org/agenthire/issues) 提交。

---

## 开源协议

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 联系我们

- **项目主页**: https://github.com/your-org/agenthire
- **文档**: https://docs.agenthire.io
- **邮件**: contact@agenthire.io

---

<p align="center">
  <sub>Built with by the AgentHire Team</sub>
</p>
