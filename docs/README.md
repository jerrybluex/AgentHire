# AgentHire

> **让Agent为人类工作，而不是人类为招聘网站工作**

AgentHire是一个AI Agent驱动的去中心化招聘协议，通过开放API让个人Agent和企业Agent成为招聘市场的中介，实现求职者和招聘方的高效匹配。

---

## 核心特性

- **自然语言求职**：求职者只需对Agent描述需求，无需反复填写简历
- **简历智能解析**：支持PDF/Word/图片简历自动解析，提取结构化信息
- **语义匹配引擎**：基于向量相似度的智能匹配，而非简单的关键词搜索
- **零平台锁定**：数据可迁移，匹配引擎可替换，用户真正拥有数据
- **开放协议**：标准化Skill API，任何Agent均可接入

---

## 快速开始

### 5分钟启动开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/agenthire/agenthire.git
cd agenthire

# 2. 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 3. 验证服务状态
curl http://localhost:8000/health

# 4. 查看API文档
open http://localhost:8000/docs
```

### 求职者快速接入

```python
import requests

# 上传简历解析
with open('resume.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/skill/parse-resume',
        files={'resume_file': f}
    )
    parsed = response.json()

# 创建Profile
profile = requests.post(
    'http://localhost:8000/api/v1/skill/profiles',
    json={'source': 'resume_parse', 'parse_id': parsed['data']['parse_id']}
).json()

print(f"Profile创建成功: {profile['data']['profile_id']}")
```

### 企业快速接入

```python
# 发布职位（需要企业API Key）
job = requests.post(
    'http://localhost:8000/api/v1/skill/jobs',
    headers={'Authorization': 'Bearer YOUR_API_KEY'},
    json={
        'job': {
            'title': '高级后端工程师',
            'requirements': {'skills': ['Go', 'Kubernetes'], 'experience_min': 3},
            'compensation': {'salary_min': 35000, 'salary_max': 50000}
        }
    }
).json()
```

---

## 架构图

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
│  │                         File Storage (S3/MinIO)                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| **API框架** | FastAPI (Python) | 高性能、自动文档、Python生态丰富 |
| **数据库** | PostgreSQL + pgvector | 关系型+向量扩展，一套数据库搞定 |
| **缓存** | Redis | 限流、缓存、消息队列 |
| **向量模型** | BGE / M3E (开源) | 中文效果好，可本地部署 |
| **任务队列** | Celery + Redis | 异步处理认证审核、数据同步 |
| **搜索** | Elasticsearch (可选) | 全文检索、复杂筛选 |
| **部署** | Docker + Docker Compose | 快速部署、环境一致 |
| **监控** | Prometheus + Grafana | 性能监控、告警 |

---

## Week 1 开发计划

当前处于 **Week 1 - 项目搭建** 阶段。

### 各Agent任务分配

| Agent | 工作目录 | 任务 | 优先级 |
|-------|----------|------|--------|
| Backend Agent | `/backend` | FastAPI框架搭建 | P0 |
| Database Agent | `/database` | PostgreSQL + pgvector | P0 |
| DevOps Agent | `/devops` | Docker配置 | P0 |
| Testing Agent | `/testing` | 测试框架 | P1 |
| Documentation Agent | `/docs` | 文档维护 | P1 |

详见各目录下的 `README.md` 了解详细任务。

---

## 文档目录

- [快速开始](docs/quickstart.md) - 5分钟上手指南
- [架构设计](docs/architecture.md) - 系统架构详解
- [API文档](docs/api/README.md) - 完整API参考
- [部署指南](docs/deployment.md) - 生产环境部署
- [贡献指南](CONTRIBUTING.md) - 如何参与贡献

---

## 贡献方式

我们欢迎各种形式的贡献！

1. **提交Issue**：报告bug或提出新功能建议
2. **提交PR**：修复bug或实现新功能
3. **完善文档**：帮助我们改进文档
4. **分享使用**：将AgentHire推荐给更多人

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 开源协议

AgentHire采用 [MIT License](LICENSE) 开源协议。

---

## 联系我们

- GitHub Issues: [https://github.com/agenthire/agenthire/issues](https://github.com/agenthire/agenthire/issues)
- 邮件: contact@agenthire.io

---

<p align="center">Made with ❤️ by AgentHire Team</p>
