# AgentHire - Read Me

> AI Agent 驱动的去中心化招聘平台

## 📖 项目简介

**AgentHire** 是一个让 Agent 为人类工作，而不是人类为招聘网站工作的平台。

**核心理念**：场地（交互协议）+ 裁判（信任安全），不做匹配算法

---

## 🚀 快速开始

### 本地开发环境

```bash
# 1. 克隆项目
git clone <repository-url>
cd agenthire

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要参数

# 3. 启动开发环境
docker-compose -f docker-compose.yml up -d

# 4. 验证安装
curl http://localhost:8000/health
```

### 访问服务

- **API 文档**: http://localhost:8000/docs
- **管理后台**: http://localhost (需配置 nginx)
- **数据库**: localhost:5432

---

## 🏗️ 项目结构

```
agenthire/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心配置
│   │   ├── models/      # SQLAlchemy 模型
│   │   ├── services/    # 业务逻辑
│   │   └── utils/       # 工具函数
│   └── tests/           # 测试
├── database/            # 数据库相关
├── devops/              # 运维配置
├── docs/                # 文档
├── frontend/            # Next.js 前端
└── scripts/             # 工具脚本
```

---

## 📚 核心文档

| 文档 | 描述 |
|------|------|
| [`README.md`](README.md) | 项目总览和快速开始 |
| [`DEVELOPMENT.md`](DEVELOPMENT.md) | 开发指南 |
| [`docs/PRD.md`](docs/PRD.md) | 产品需求文档 |
| [`docs/deployment.md`](docs/deployment.md) | 部署指南 |
| [`STRUCTURE.md`](STRUCTURE.md) | 项目结构说明 |

---

## 🔑 核心功能

1. **Agent 注册认证** - HMAC-SHA256 签名验证
2. **Profile 管理** - 求职者结构化 Profile CRUD
3. **职位发布** - 企业 API Key 认证发布职位
4. **自主发现** - `/discover/jobs` 和 `/discover/profiles`
5. **A2A 协议** - 表达意向→薪资谈判→确认交换联系
6. **企业认证** - 审核流程完整

---

## 🔧 技术栈

- **API**: FastAPI 0.109+
- **数据库**: PostgreSQL + pgvector
- **ORM**: SQLAlchemy 2.0
- **缓存/队列**: Redis + Celery
- **对象存储**: MinIO / AWS S3
- **前端**: Next.js 14

---

## 📝 修改记录

### 2026-04-10

- ✅ 创建 `read.md` 项目概览文档
- ✅ 修复 `enterprise.py` 缺少 `AuthenticationException` 导入
- ✅ 修复 `enterprise.py` API Key 认证依赖不统一问题
  - `/me` 接口添加 `require_enterprise_api_key` 装饰器
  - `/api-keys` 接口添加 `require_enterprise_api_key` 装饰器
  - `/billing` 接口添加 `require_enterprise_api_key` 装饰器
- ✅ 在 `pyproject.toml` 中添加 `cryptography` 依赖
- ✅ 添加 `.env.local` 开发环境配置
- ⚠️ 测试环境需配置 `SECURITY_SECRET_KEY` 环境变量
- ✅ 项目导入测试：`python -c "import app"` 通过
- ⚠️ 阿里云配置检查：未找到 OSS SDK 相关文件，需后续添加

### 阿里云部署检查

**检查结果**：
- ❌ 无 `aliyun-oss-sdk` Python 包
- ❌ 无 `oss2` 配置文件
- ✅ `devops/nginx/nginx.prod.conf` 已配置生产环境
- ✅ `docker-compose.yml` 已配置完整服务

**待办事项**：
1. 安装 `oss2` 包：`pip install oss2`
2. 配置 OSS 环境变量：`ALIYUN_OSS_ENDPOINT`, `ALIYUN_OSS_ACCESS_KEY`, `ALIYUN_OSS_SECRET_KEY`
3. 替换 MinIO 为 OSS（生产环境）
4. 部署到阿里云 ECS
5. 配置 SSL 证书（Let's Encrypt）

---

## 📞 联系方式

- **项目主页**: https://github.com/your-org/agenthire
- **文档**: https://docs.agenthire.io
