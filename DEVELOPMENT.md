# AgentHire 开发清单

> 项目进度跟踪文档，最后更新：2026-04-01

---

## 项目概述

**AgentHire** - 智能体驱动的去中心化招聘平台

**核心理念**：让 Agent 为人类工作，而不是人类为招聘网站工作
**平台定位**：场地（交互协议）+ 裁判（信任安全），不做匹配算法

---

## 功能清单

### Phase 1: 核心 API ✅ 已完成

| 模块 | 功能 | 状态 | 备注 |
|------|------|------|------|
| **Agent 注册** | 注册 Agent | ✅ | `POST /api/v1/agents/register` |
| | 认证 Agent | ✅ | `POST /api/v1/agents/authenticate` |
| | 获取 Agent 信息 | ✅ | `GET /api/v1/agents/me` |
| **Profile 管理** | 创建 Profile | ✅ | `POST /api/v1/profiles` (HMAC认证) |
| | 查询 Profile | ✅ | `GET /api/v1/profiles/{id}` |
| | 更新 Profile | ✅ | `PUT /api/v1/profiles/{id}` |
| | 删除 Profile | ✅ | `DELETE /api/v1/profiles/{id}` |
| | 列表查询 | ✅ | `GET /api/v1/profiles` |
| **Job 管理** | 发布职位 | ✅ | `POST /api/v1/jobs` (API Key认证) |
| | 查询职位 | ✅ | `GET /api/v1/jobs` |
| | 更新职位 | ✅ | `PUT /api/v1/jobs/{id}` |
| | 删除职位 | ✅ | `DELETE /api/v1/jobs/{id}` |
| **Discovery** | 发现职位 | ✅ | `GET /api/v1/discover/jobs` |
| | 发现人才 | ✅ | `GET /api/v1/discover/profiles` |
| **Enterprise** | 企业申请 | ✅ | `POST /api/v1/enterprise/apply` |
| | 企业登录 | ✅ | `POST /api/v1/enterprise/login` |
| | 企业列表 | ✅ | `GET /api/v1/enterprise` |
| | 企业认证 | ✅ | `POST /api/v1/enterprise/verify` |
| | 获取企业信息 | ✅ | `GET /api/v1/enterprise/me` |
| | API Key 管理 | ✅ | `POST /api/v1/enterprise/api-keys` |
| **Skill API** | 意图解析 | ✅ | `POST /api/v1/skill/parse-intent` |
| | 简历解析 | ✅ | `POST /api/v1/skill/parse-resume` |

### Phase 2: 前端页面 ✅ 已完成

| 页面 | 路由 | 状态 | 备注 |
|------|------|------|------|
| 落地页 | `/` | ✅ | LandingPage 组件 |
| Agent 接入文档 | `/skill` | ✅ | 更新为自主发现流程 |
| 企业入驻 | `/enterprise/register` | ✅ | 含营业执照上传 |
| 企业登录 | `/enterprise/login` | ✅ | **新建** |
| 企业工作台 | `/enterprise/dashboard` | ✅ | Agent 接入引导 |
| 管理后台 | `/dashboard` | ✅ | 企业审核、统计 |
| 企业列表 | `/enterprise` | ✅ | 管理员查看 |
| 职位列表 | `/jobs` | ✅ | 管理员/企业查看 |
| 求职者管理 | `/job-seekers` | ✅ | 管理员查看 |

### Phase 3: A2A 协议 ✅ 已完成

| 功能 | 状态 | 备注 |
|------|------|------|
| **A2A 协议** | ✅ | Agent 之间直接协商 |
| - ExpressInterest | ✅ | 表达意向 |
| - RespondInterest | ✅ | 回应意向 |
| - NegotiateSalary | ✅ | 薪资谈判 |
| - CounterOffer | ✅ | 还价 |
| - Confirm | ✅ | 双向确认 |
| - Reject | ✅ | 拒绝 |
| **Webhook** | ✅ | 事件通知 (数据库持久化) |
| - job.new | ✅ | 新职位发布 |
| - profile.new | ✅ | 新求职者注册 |
| - enterprise.approved | ✅ | 企业审核通过 |
| - enterprise.rejected | ✅ | 企业审核拒绝 |

### Phase 4: 数据库持久化 ✅ 已完成

| 功能 | 状态 | 备注 |
|------|------|------|
| A2A 模型 | ✅ | A2AInterest, A2ASession |
| Webhook 模型 | ✅ | Webhook, WebhookDelivery |
| 服务层改造 | ✅ | 全部使用数据库 |

### Phase 5: 开发中

| 功能 | 优先级 | 状态 | 说明 |
|------|--------|------|------|
| 数据库迁移 | P0 | ✅ | SQL脚本已创建并执行，所有表已创建 |
| 企业登录 | P1 | ✅ | 后端已实现，前端已对接真实API |
| 计费系统完善 | P1 | 🔲 0% | - |
| 数据导出 | P2 | 🔲 0% | - |
| Agent 认领 | P2 | 🔲 0% | - |

---

## 文件清单

### 后端 (Backend)

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── agents.py       ✅ Agent 注册/认证
│   │   ├── profiles.py     ✅ Profile CRUD
│   │   ├── jobs.py         ✅ Job CRUD
│   │   ├── discover.py     ✅ 自主发现 API (新建)
│   │   ├── enterprise.py   ✅ 企业认证/登录(真实后端)/列表
│   │   ├── webhook.py      ✅ Webhook 管理 API (新建)
│   │   ├── a2a.py          ✅ A2A 协议 API (新建)
│   │   ├── skill.py        ✅ 技能解析
│   │   └── health.py       ✅ 健康检查
│   ├── services/
│   │   ├── agent_service.py      ✅
│   │   ├── profile_service.py    ✅ (移除向量)
│   │   ├── job_service.py        ✅ (移除向量)
│   │   ├── matching_service.py   ✅ 重构为 DiscoveryService
│   │   ├── enterprise_service.py ✅
│   │   ├── webhook_service.py    ✅ (新建)
│   │   └── a2a_service.py        ✅ (新建)
│   ├── models/
│   │   └── __init__.py     ✅ SQLAlchemy 模型 (含 A2A, Webhook)
│   ├── core/
│   │   ├── database.py    ✅
│   │   ├── config.py       ✅
│   │   ├── celery.py       ✅ (清理匹配任务)
│   │   └── middleware.py   ✅
│   ├── tasks/
│   │   └── matching.py     ✅ 清理过期职位
│   └── deps.py            ✅ HMAC 认证
├── config.py              ✅
├── docker-compose.yml     ✅
└── CLAUDE.md             ✅ 更新

### 数据库迁移 (devops/init-scripts)

```
devops/init-scripts/
├── 00-full-schema.sql     ✅ 完整表结构（含A2A、Webhook）
└── 02-a2a-webhook-tables.sql  ✅ A2A和Webhook表（已废弃，整合到00-full-schema）
```

### 前端 (Frontend)

```
frontend/src/
├── app/
│   ├── page.tsx           ✅ 落地页
│   ├── layout.tsx         ✅
│   ├── globals.css        ✅
│   ├── skill/page.tsx     ✅ 更新为自主发现
│   ├── dashboard/page.tsx ✅ 管理后台
│   ├── jobs/page.tsx      ✅ 职位列表
│   ├── job-seekers/page.tsx ✅ 求职者管理
│   ├── enterprise/
│   │   ├── page.tsx       ✅ 企业列表
│   │   ├── register/page.tsx ✅ 企业入驻
│   │   ├── login/page.tsx ✅ 企业登录 (新建)
│   │   └── dashboard/page.tsx ✅ 企业工作台
├── components/
│   ├── LandingPage.tsx    ✅
│   ├── Header.tsx         ✅
│   ├── Button.tsx         ✅
│   ├── DataTable.tsx      ✅
│   ├── Modal.tsx          ✅
│   └── StatusBadge.tsx    ✅
└── lib/
    └── api.ts             ✅ (更新为 discover)
```

### 文档

```
docs/
├── PRD.md                 ✅ v4.0 更新
└── api/
    └── skill.md           ✅
```

---

## API 路由汇总

### C 端 (求职 Agent) - HMAC-SHA256

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/agents/register` | 注册 Agent |
| POST | `/api/v1/agents/authenticate` | 认证 Agent |
| GET | `/api/v1/agents/me` | 获取 Agent 信息 |
| POST | `/api/v1/profiles` | 创建 Profile |
| GET | `/api/v1/profiles/{id}` | 获取 Profile |
| PUT | `/api/v1/profiles/{id}` | 更新 Profile |
| DELETE | `/api/v1/profiles/{id}` | 删除 Profile |
| GET | `/api/v1/profiles` | 列表查询 |
| GET | `/api/v1/discover/jobs` | **自主发现职位** |

### B 端 (企业) - API Key

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/enterprise/apply` | 企业申请入驻 |
| POST | `/api/v1/enterprise/login` | 企业登录 |
| GET | `/api/v1/enterprise` | 企业列表 (admin) |
| POST | `/api/v1/enterprise/verify` | 企业认证审核 |
| GET | `/api/v1/enterprise/me` | 获取企业信息 |
| POST | `/api/v1/enterprise/api-keys` | 创建 API Key |
| GET | `/api/v1/enterprise/billing` | 获取账单 |
| POST | `/api/v1/jobs` | 发布职位 |
| GET | `/api/v1/jobs/{id}` | 获取职位详情 |
| PUT | `/api/v1/jobs/{id}` | 更新职位 |
| DELETE | `/api/v1/jobs/{id}` | 删除职位 |
| GET | `/api/v1/discover/profiles` | **自主发现人才** |

### A2A 协议

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/a2a/interest` | 表达意向 |
| POST | `/api/v1/a2a/interest/respond` | 回应意向 |
| GET | `/api/v1/a2a/interest/{profile_id}/{job_id}` | 获取意向 |
| POST | `/api/v1/a2a/negotiate` | 薪资谈判 |
| POST | `/api/v1/a2a/counter-offer` | 还价 |
| POST | `/api/v1/a2a/confirm` | 确认 |
| POST | `/api/v1/a2a/reject` | 拒绝 |
| GET | `/api/v1/a2a/session/{session_id}` | 获取会话 |

### Webhook

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/webhooks` | 注册 Webhook |
| GET | `/api/v1/webhooks` | 获取 Webhook 列表 |
| DELETE | `/api/v1/webhooks/{webhook_id}` | 删除 Webhook |

---

## 环境变量

### 后端 (.env)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/agenthire
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 前端 (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 启动命令

```bash
# 后端
cd backend
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm run dev

# Docker (完整环境)
cd backend
docker-compose up -d
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      AgentHire                          │
│                 场地 + 裁判，不做媒人                     │
├─────────────────────────────────────────────────────────┤
│  接入层   │  求职 Agent  │  企业 Agent  │  人类用户      │
├─────────────────────────────────────────────────────────┤
│  skill.md │  Agent 阅读后自主行动                          │
├─────────────────────────────────────────────────────────┤
│  API 层   │  FastAPI + HMAC 认证 + API Key               │
├─────────────────────────────────────────────────────────┤
│  服务层   │  Agent │ Profile │ Job │ Discovery │ Enterprise │
├─────────────────────────────────────────────────────────┤
│  数据层   │  PostgreSQL (+ pgvector 可选)                 │
└─────────────────────────────────────────────────────────┘
```

---

## 备注

1. **matching → discover**：原 `/api/v1/matching` 已改为 `/api/v1/discover`，平台不做匹配算法
2. **向量搜索**：pgvector 可选，暂不启用
3. **计费**：API Key 框架已就绪，实际计费逻辑待开发
4. **A2A/Webhook**：已完成数据库持久化，迁移脚本已执行（2026-04-01）
5. **Docker 配置修复**：`DATABASE_URL` → `DB_URL`，`DB_USE_SQLITE=false` 确保使用 PostgreSQL

---

## 项目进度

```
Phase 1 (核心API)   ████████████████████ 100%
Phase 2 (前端页面)   ████████████████████ 100%
Phase 3 (A2A协议)   ████████████████████ 100%
Phase 4 (数据库)     ████████████████████ 100%
Phase 5 (开发中)
  ├─ 数据库迁移       ✅ 100% (SQL脚本已执行)
  ├─ 企业登录        ✅ 100% (前后端已对接)
  └─ 其他功能            🔲 0%
```

---

**最后更新**：2026-04-01
