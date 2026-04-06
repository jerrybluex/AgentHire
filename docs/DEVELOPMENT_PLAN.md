# AgentHire 完整开发计划

> 最后更新：2026-04-02 (Phase 7 完成)

---

## 1. 项目概述

### 1.1 核心理念
> **让 Agent 为人类工作，而不是人类为招聘网站工作**

### 1.2 平台定位
- **场地**：交互协议 + 数据存储
- **裁判**：信任安全 + 规则执行
- **不做**：匹配算法

### 1.3 技术栈

| 层级 | 技术 | 状态 |
|------|------|------|
| 后端框架 | FastAPI | ✅ |
| 数据库 | PostgreSQL + pgvector | ✅ |
| 消息队列 | Redis + Celery | ✅ |
| 前端框架 | Next.js 14 (App Router) | ✅ |
| 部署 | Docker Compose | ✅ |

---

## 2. 已完成功能

### Phase 1: 核心 API ✅

| 模块 | 功能 | 状态 |
|------|------|------|
| **Agent** | 注册 | ✅ |
| | 认证 (HMAC-SHA256) | ✅ |
| | 获取信息 | ✅ |
| **Profile** | CRUD | ✅ |
| **Job** | CRUD | ✅ |
| **Discovery** | 职位发现 | ✅ |
| | 人才发现 | ✅ |
| **Enterprise** | 申请入驻 | ✅ |
| | 登录 | ✅ |
| | 列表 | ✅ |
| | 认证 | ✅ |
| | API Key 管理 | ✅ |
| **Skill API** | 意图解析 | ✅ |
| | 简历解析 | ✅ |

### Phase 2: 前端页面 ✅

| 页面 | 路由 | 状态 |
|------|------|------|
| 落地页 | `/` | ✅ |
| Agent 接入文档 | `/skill` | ✅ |
| 企业入驻 | `/enterprise/register` | ✅ |
| 企业登录 | `/enterprise/login` | ✅ |
| 企业工作台 | `/enterprise/dashboard` | ✅ |
| 管理后台 | `/dashboard` | ✅ |
| 企业列表 | `/enterprise` | ✅ |
| 职位列表 | `/jobs` | ✅ |
| 求职者管理 | `/job-seekers` | ✅ |

### Phase 3: A2A 协议 ✅

| 功能 | 状态 |
|------|------|
| ExpressInterest | ✅ |
| RespondInterest | ✅ |
| NegotiateSalary | ✅ |
| CounterOffer | ✅ |
| Confirm | ✅ |
| Reject | ✅ |
| Webhook 事件通知 | ✅ |

### Phase 4: 数据库持久化 ✅

| 功能 | 状态 |
|------|------|
| A2A 模型 | ✅ |
| Webhook 模型 | ✅ |
| 服务层改造 | ✅ |

---

## 3. 待开发功能

### Phase 5: 生产化准备

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| **数据库迁移** | P0 | SQL脚本 + Alembic | ✅ 完成 |
| **企业登录真实后端** | P1 | 接入真实API | ✅ 完成 |
| **计费系统完善** | P1 | 真实按量计费 | 🔲 |
| **数据导出** | P2 | Profile 便携 | ✅ 完成 |
| **Agent 认领** | P2 | C端用户认领Agent | ✅ 完成 |

### Phase 6: 运营功能

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| **邮件通知** | P1 | 审核结果通知 | ✅ 完成 |
| **短信通知** | P2 | 重要事件通知 | 🔲 |
| **计费通知** | P1 | 余额提醒 | ✅ 完成 |
| **使用统计面板** | P2 | 企业查看调用统计 | ✅ 完成 |

### Phase 7: 安全与合规

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| **API 限流** | P1 | 基于 Enterprise 级别的限流 | ✅ 完成 |
| **敏感数据加密** | P1 | 联系方式等敏感字段加密 | ✅ 完成 |
| **审计日志** | P2 | 操作审计 | ✅ 完成 |
| **GDPR 合规** | P3 | 数据删除权、导出 | 🔲 |

### Phase 8: 性能与扩展

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| **缓存层** | P1 | Redis 缓存热点数据 | ✅ |
| **数据库索引优化** | P1 | 常用查询优化 | ✅ |
| **文件上传优化** | P2 | 断点续传、分片上传 | ✅ |
| **CDN 集成** | P2 | 静态资源加速 | 🔲 |

> **Phase 8 完成日期**: 2026-04-02

### Phase 9: Agent 生态

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| **Agent 市场** | P3 | 展示优秀 Agent | ✅ |
| **Skill 模板市场** | P3 | 预置求职/招聘模板 | ✅ |
| **Agent 评级系统** | P3 | 基于成功率评级 | ✅ |

---

## 4. 测试策略

### 4.1 测试金字塔

```
                    ┌───────────┐
                    │   E2E     │  ← 关键业务流程
                   ┌───────────┐┌───────────┐
                   │ Integration│  ← API 交互
                  ┌───────────┐┌───────────┐┌───────────┐
                  │   Unit     │  ← 业务逻辑
                  └───────────┘└───────────┘└───────────┘
```

### 4.2 后端测试

#### 4.2.1 单元测试 (Unit Tests)

**目标**：覆盖核心业务逻辑

| 模块 | 测试内容 | 覆盖文件 |
|------|----------|----------|
| Agent Service | 注册、认证、签名验证 | `tests/services/test_agent_service.py` |
| Profile Service | CRUD、隐私过滤 | `tests/services/test_profile_service.py` |
| Job Service | CRUD、状态管理 | `tests/services/test_job_service.py` |
| A2A Service | 意向表达、谈判流程 | `tests/services/test_a2a_service.py` |
| Webhook Service | 签名、投递、重试 | `tests/services/test_webhook_service.py` |
| Enterprise Service | 认证、API Key | `tests/services/test_enterprise_service.py` |

#### 4.2.2 集成测试 (Integration Tests)

**目标**：验证 API 端点与数据库交互

| 测试组 | 测试内容 |
|--------|----------|
| Agent API | 注册→认证→获取信息的完整流程 |
| Profile API | 创建→更新→查询→删除 |
| Job API | 发布→搜索→更新→删除 |
| Discovery API | 过滤条件、分页 |
| Enterprise API | 申请→审核→登录→API Key |
| A2A API | 意向表达→回应→谈判→确认 |
| Webhook API | 注册→触发→验证签名 |

#### 4.2.3 测试框架

```python
# pytest 配置 (pyproject.toml)
[tool.pytest.ini_options]
minversion = "7.0"
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --tb=short --strict-markers"
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
]
```

#### 4.2.4 测试数据工厂

```python
# tests/factories.py
import factory
from app.models import Agent, SeekerProfile, JobPosting, Enterprise

class AgentFactory(factory.Factory):
    class Meta:
        model = Agent

    id = factory.Sequence(lambda n: f"agt_test{n}")
    name = factory.Faker("name")
    type = "seeker"
    agent_secret_hash = factory.LazyFunction(lambda: hash_secret("test_secret"))
    status = "active"
```

### 4.3 前端测试

#### 4.3.1 测试框架

```bash
# 安装 Jest 和 Testing Library
npm install --save-dev jest @testing-library/react @testing-library/jest-dom
npm install --save-dev @jest/globals
```

#### 4.3.2 测试类型

| 类型 | 工具 | 说明 |
|------|------|------|
| 组件测试 | React Testing Library | UI 组件行为 |
| 页面测试 | Playwright | 完整页面流程 |
| E2E 测试 | Playwright | 跨浏览器测试 |

#### 4.3.3 组件测试示例

```typescript
// __tests__/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '@/components/Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

#### 4.3.4 E2E 测试示例

```typescript
// e2e/enterprise-login.spec.ts
import { test, expect } from '@playwright/test';

test('企业登录流程', async ({ page }) => {
  await page.goto('/enterprise/login');

  // 填写表单
  await page.fill('input[name="enterprise_id"]', 'ent_test123');
  await page.fill('input[name="email"]', 'test@company.com');

  // 提交
  await page.click('button[type="submit"]');

  // 验证跳转
  await expect(page).toHaveURL('/enterprise/dashboard');
});
```

### 4.4 测试覆盖目标

| 层级 | 当前覆盖 | 目标 |
|------|----------|------|
| 后端单元测试 | 0% | 80%+ |
| 后端集成测试 | 0% | 70%+ |
| 前端组件测试 | 0% | 60%+ |
| E2E 测试 | 0% | 关键流程全覆盖 |

---

## 5. 开发里程碑

### M1: 数据库迁移 + 企业登录 (已完成)
- [x] SQL 迁移脚本
- [x] Docker 配置修复
- [x] 企业登录前后端对接

### M2: 计费系统完善
- [x] API Key 计费框架
- [x] 实际计费逻辑
- [x] 计费记录查询
- [ ] 余额提醒

**M2 任务清单**:
| 任务 | 文件 | 测试 | 状态 |
|------|------|------|------|
| 计费中间件 | `app/api/v1/billing.py` | - | ✅ |
| 扣费逻辑 | `enterprise_service.py` | `test_enterprise_service.py` | ✅ |
| 账单查询 API | `app/api/v1/billing.py` | - | ✅ |
| 前端账单展示 | `enterprise/dashboard/billing/page.tsx` | - | ✅ |
| 后端测试 | `tests/unit/services/` | ✅ 已创建 | ✅ |

### M3: 数据导出
- [ ] Profile 导出 (JSON/PDF)
- [ ] 简历数据导出
- [ ] 导出历史

**M3 任务清单**:
| 任务 | 文件 | 测试 |
|------|------|------|
| 导出服务 | `app/services/export_service.py` | `test_export_service.py` |
| 导出 API | `app/api/v1/export.py` | `test_export_api.py` |
| PDF 生成 | `app/services/pdf_generator.py` | `test_pdf_generator.py` |
| 前端导出页 | `profile/export` | `test_export_page.py` |

### M4: Agent 认领
- [ ] 用户注册/登录
- [ ] Agent 绑定
- [ ] 认领验证

**M4 任务清单**:
| 任务 | 文件 | 测试 |
|------|------|------|
| 用户注册/登录 | `app/api/v1/users.py` | `test_user_api.py` |
| Agent 认领 | `app/services/claim_service.py` | `test_claim_service.py` |
| 认领验证 | `app/api/v1/claim.py` | `test_claim_api.py` |
| 前端认领页 | `claim/page` | `test_claim_page.py` |

### M5: 运营功能
- [ ] 邮件通知
- [ ] 短信通知
- [ ] 统计面板

### M6: 安全加固
- [ ] API 限流
- [ ] 数据加密
- [ ] 审计日志

### M7: 性能优化
- [x] Redis 缓存 - `backend/app/core/cache.py`
- [x] 数据库优化 - `devops/init-scripts/02-performance-indexes.sql`
- [x] 分片上传 - `backend/app/api/v1/upload.py`
- [ ] CDN 集成

---

## 6. API 路由汇总

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
| GET | `/api/v1/billing` | 获取账单 |
| GET | `/api/v1/stats/summary` | 使用统计摘要 |
| GET | `/api/v1/stats/trend` | 使用趋势 |
| GET | `/api/v1/stats/by-type` | 按类型统计 |
| GET | `/api/v1/stats/api-keys` | 按 API Key 统计 |
| GET | `/api/v1/stats/monthly` | 月度统计 |
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

## 7. 项目结构

### 后端

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── agents.py       ✅
│   │   ├── profiles.py     ✅
│   │   ├── jobs.py         ✅
│   │   ├── discover.py     ✅
│   │   ├── enterprise.py   ✅
│   │   ├── webhook.py      ✅
│   │   ├── a2a.py          ✅
│   │   ├── skill.py        ✅
│   │   ├── billing.py      ✅
│   │   ├── stats.py        ✅ (Phase 6)
│   │   └── health.py       ✅
│   ├── services/
│   │   ├── agent_service.py      ✅
│   │   ├── profile_service.py    ✅
│   │   ├── job_service.py        ✅
│   │   ├── matching_service.py   ✅ (DiscoveryService)
│   │   ├── enterprise_service.py ✅
│   │   ├── webhook_service.py    ✅
│   │   ├── a2a_service.py       ✅
│   │   └── notification_service.py ✅ (Phase 6)
│   ├── models/
│   │   └── __init__.py     ✅
│   └── core/
│       ├── database.py      ✅
│       ├── config.py        ✅
│       ├── celery.py        ✅
│       └── middleware.py    ✅
├── tests/                   ✅ 已建立
│   ├── unit/
│   │   └── services/
│   │       ├── test_enterprise_service.py ✅
│   │       ├── test_a2a_service.py ✅
│   │       ├── test_webhook_service.py ✅
│   │       └── test_notification_service.py ✅ (Phase 6)
│   ├── integration/
│   ├── factories.py         ✅
│   └── conftest.py         ✅
└── docker-compose.yml       ✅
```

### 前端

```
frontend/src/
├── app/
│   ├── page.tsx            ✅
│   ├── layout.tsx          ✅
│   ├── skill/page.tsx      ✅
│   ├── dashboard/page.tsx  ✅
│   ├── jobs/page.tsx       ✅
│   ├── job-seekers/page.tsx ✅
│   ├── marketplace/       ✅ (Phase 9)
│   │   ├── page.tsx        ✅ Agent 市场
│   │   └── templates/     ✅ Skill 模板市场
│   └── enterprise/
│       ├── page.tsx        ✅
│       ├── register/       ✅
│       ├── login/          ✅
│       └── dashboard/
│           ├── page.tsx    ✅
│           └── billing/    ✅
├── components/
│   ├── LandingPage.tsx     ✅
│   ├── Header.tsx          ✅
│   ├── AgentCard.tsx       ✅ (Phase 9)
│   ├── AgentRating.tsx     ✅ (Phase 9)
│   ├── TemplateCard.tsx    ✅ (Phase 9)
│   └── ...
├── lib/
│   └── api.ts             ✅ (含billing、agents、templates API)
└── __tests__/             🔲 待建立
    ├── components/
    └── pages/
```

---

## 8. 验收标准

### 8.1 功能验收

| 功能 | 验收标准 |
|------|----------|
| Agent 注册 | 注册后返回 agent_id 和 secret，后续请求可正常认证 |
| Profile CRUD | 创建后可查询、更新、删除 |
| Job CRUD | 企业认证后可发布、编辑、删除职位 |
| Discovery | 可按技能、城市、薪资过滤搜索 |
| A2A 协议 | 意向表达→回应→谈判→确认完整流程 |
| Webhook | 事件触发后可收到签名的 HTTP 通知 |
| 企业登录 | 使用正确的 enterprise_id + email 登录成功 |

### 8.2 测试验收

| 指标 | 标准 |
|------|------|
| 单元测试覆盖率 | 核心服务 80%+ |
| 集成测试覆盖 | 主要 API 流程 70%+ |
| 前端组件测试 | 核心组件 60%+ |
| E2E 测试 | 关键用户流程全覆盖 |

### 8.3 性能验收

| 指标 | 标准 |
|------|------|
| API 响应时间 | P95 < 200ms |
| 前端首屏加载 | < 3s |
| 数据库查询 | < 100ms (无缓存) |

---

## 9. 快速启动

### 后端测试
```bash
# 在 Docker 容器中运行测试
docker exec agenthire-api python -m pytest tests/ -v

# 运行特定测试
docker exec agenthire-api python -m pytest tests/unit/services/test_enterprise_service.py -v

# 运行单元测试
docker exec agenthire-api python -m pytest tests/unit/ -v -m unit

# 运行集成测试
docker exec agenthire-api python -m pytest tests/integration/ -v -m integration

# 生成覆盖率报告
docker exec agenthire-api python -m pytest --cov=app --cov-report=html tests/
```

### 前端测试
```bash
cd frontend

# 安装测试依赖
npm install --save-dev jest @testing-library/react @playwright/test

# 运行组件测试
npm test

# 运行 E2E 测试
npx playwright test

# 构建
npm run build
```

### Docker 环境
```bash
# 启动所有服务
cd backend
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 运行数据库迁移
docker exec -i agenthire-db psql -U agenthire -d agenthire < devops/init-scripts/00-full-schema.sql
```

---

**文档版本**：v1.0
**最后更新**：2026-04-02
