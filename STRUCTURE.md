# AgentHire 项目结构说明

## 目录结构

```
AgentHire/
├── backend/              # FastAPI后端 (Backend Agent)
│   ├── app/
│   │   ├── api/         # API路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # SQLAlchemy模型
│   │   ├── schemas/     # Pydantic模型
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   ├── alembic/         # 数据库迁移
│   └── tests/           # 后端测试
│
├── database/            # 数据库相关 (Database Agent)
│   ├── migrations/      # 迁移文件
│   ├── schemas/         # SQL schema文件
│   └── seeds/           # 种子数据
│
├── devops/              # 运维配置 (DevOps Agent)
│   ├── docker/          # Docker配置
│   ├── k8s/            # Kubernetes配置
│   └── scripts/        # 部署脚本
│
├── testing/             # 测试 (Testing Agent)
│   ├── unit/           # 单元测试
│   ├── integration/    # 集成测试
│   ├── e2e/            # 端到端测试
│   └── fixtures/       # 测试数据
│
├── docs/               # 文档 (Documentation Agent)
│   ├── PRD.md          # 产品需求文档
│   └── README.md       # 文档索引
│
└── scripts/            # 工具脚本
    └── start-dev.sh    # 开发环境启动脚本
```

## 团队成员工作目录

| 角色 | 工作目录 | README文件 |
|------|----------|------------|
| Backend Agent | `/backend` | `backend/README.md` |
| Database Agent | `/database` | `database/README.md` |
| DevOps Agent | `/devops` | `devops/README.md` |
| Testing Agent | `/testing` | `testing/README.md` |
| Documentation Agent | `/docs` | `docs/README.md` |

## 快速开始

### 1. 克隆仓库
```bash
git clone <repository-url>
cd AgentHire
```

### 2. 启动开发环境
```bash
./scripts/start-dev.sh
```

### 3. 访问服务
- API: http://localhost:8000
- API文档: http://localhost:8000/docs
- 数据库: localhost:5432

## 开发规范

### 分支策略
- `main`: 生产分支
- `develop`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 热修复分支

### 提交规范
```
<type>: <subject>

<body>

type:
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具
```

## 技术栈

| 层级 | 技术 |
|------|------|
| API框架 | FastAPI |
| 数据库 | PostgreSQL + pgvector |
| ORM | SQLAlchemy 2.0 |
| 缓存 | Redis |
| 任务队列 | Celery |
| 部署 | Docker |
| 测试 | pytest |

---

**项目**: AgentHire - AI Agent驱动的去中心化招聘平台
**协议**: MIT License
