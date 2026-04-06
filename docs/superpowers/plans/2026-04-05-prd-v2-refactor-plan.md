# AgentHire PRD v2 重构实施计划

> **执行方式：** 子 Agent 驱动或内联执行，按优先级分阶段

**目标：** 将 AgentHire 重构为符合 PRD v2 架构的最小可行产品

**架构：** 按 PRD v2 的服务划分重构数据模型和服务层，补全状态机，强化 API 设计原则

**技术栈：** Python/FastAPI, SQLAlchemy (async), PostgreSQL, Redis, Celery

---

## 阶段划分

### Phase 1: 数据模型重构（核心）
### Phase 2: 服务架构拆分
### Phase 3: 状态机补全
### Phase 4: API 设计强化

---

## Phase 1: 数据模型重构

### 任务 1: 创建 Tenant/Principal 基础模型

**文件：**
- 创建：`backend/app/models/tenant.py`
- 修改：`backend/app/models/__init__.py`
- 测试：`tests/unit/test_tenant_model.py`

- [ ] **步骤 1: 写失败测试**

```python
# tests/unit/test_tenant_model.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.fixture
async def db_session():
    # Setup test DB
    ...

async def test_create_tenant(db_session):
    from app.models.tenant import Tenant
    tenant = Tenant(name="测试企业", type="enterprise")
    db_session.add(tenant)
    await db_session.commit()
    
    assert tenant.id is not None
    assert tenant.status == "active"
```

- [ ] **步骤 2: 创建 Tenant 模型**

```python
# backend/app/models/tenant.py
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Tenant(Base):
    """租户 - 企业或个人的数据隔离空间"""
    __tablename__ = "tenants"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # enterprise | individual
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **步骤 3: 运行测试**
- [ ] **步骤 4: 提交**

---

### 任务 2: 添加 Principal 模型

**文件：**
- 创建：`backend/app/models/principal.py`
- 修改：`backend/app/models/__init__.py`
- 测试：`tests/unit/test_principal_model.py`

- [ ] **步骤 1: 写失败测试**

```python
async def test_create_principal(db_session):
    from app.models.principal import Principal
    principal = Principal(
        tenant_id="tenant_test123",
        type="human",
        email="test@example.com"
    )
    ...
```

- [ ] **步骤 2: 创建 Principal 模型**

```python
# backend/app/models/principal.py
class Principal(Base):
    """主体 - 租户下的用户/人/操作员"""
    __tablename__ = "principals"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(32), ForeignKey("tenants.id"))
    type: Mapped[str] = mapped_column(String(16))  # human | agent | service
    name: Mapped[Optional[str]] = mapped_column(String(128))
    email: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(16), default="active")
```

- [ ] **步骤 3: 运行测试**
- [ ] **步骤 4: 提交**

---

### 任务 3: 添加 Credential 模型

**文件：**
- 创建：`backend/app/models/credential.py`
- 修改：`backend/app/models/__init__.py`

- [ ] **步骤 1: 创建 Credential 模型**

```python
# backend/app/models/credential.py
class Credential(Base):
    """凭证 - 认证凭据（API Key / Agent Secret / Password）"""
    __tablename__ = "credentials"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    principal_id: Mapped[str] = mapped_column(String(32), ForeignKey("principals.id"))
    type: Mapped[str] = mapped_column(String(32))  # api_key | agent_secret | password
    key_hash: Mapped[str] = mapped_column(String(256))  # 存储哈希而非明文
    name: Mapped[Optional[str]] = mapped_column(String(128))  # 凭证名称
    status: Mapped[str] = mapped_column(String(16), default="active")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

- [ ] **步骤 2: 运行测试**
- [ ] **步骤 3: 提交**

---

### 任务 4: 重构 Agent 模型（关联 Tenant/Principal）

**文件：**
- 修改：`backend/app/models/__init__.py` (Agent 类)
- 修改：`backend/app/services/agent_service.py`

- [ ] **步骤 1: 更新 Agent 模型关联**

```python
# Agent 模型新增字段
tenant_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("tenants.id"))
principal_id: Mapped[Optional[str]] = mapped_column(String(32), ForeignKey("principals.id"))
```

- [ ] **步骤 2: 更新 AgentService.register()**

```python
# 创建 Agent 时同时创建 Tenant 和 Principal
async def register(self, db, name, agent_type, platform, contact):
    # 1. 创建 Tenant
    tenant = Tenant(id=generate_id("tenant_"), name=name, type="agent")
    db.add(tenant)
    
    # 2. 创建 Principal  
    principal = Principal(
        id=generate_id("prin_"),
        tenant_id=tenant.id,
        type="agent",
        name=name
    )
    db.add(principal)
    
    # 3. 创建 Agent 关联到 Tenant/Principal
    agent = Agent(
        id=generate_id("agt_"),
        tenant_id=tenant.id,
        principal_id=principal.id,
        ...
    )
```

- [ ] **步骤 3: 提交**

---

### 任务 5: 添加 JobVersion 模型

**文件：**
- 创建：`backend/app/models/job_version.py`
- 修改：`backend/app/models/__init__.py`

- [ ] **步骤 1: 创建 JobVersion 模型**

```python
# backend/app/models/job_version.py
class JobVersion(Base):
    """职位版本 - Job 的版本化管理"""
    __tablename__ = "job_versions"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(32), ForeignKey("jobs.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(256))
    department: Mapped[Optional[str]] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text)
    requirements: Mapped[dict] = mapped_column(JSON)  # 结构化技能/年限要求
    compensation: Mapped[dict] = mapped_column(JSON)  # 薪资范围
    location: Mapped[dict] = mapped_column(JSON)  # 地点/远程策略
    status: Mapped[str] = mapped_column(String(16))
    created_by: Mapped[Optional[str]] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **步骤 2: 提交**

---

### 任务 6: 添加 ApplicationEvent 模型（申请事件流）

**文件：**
- 创建：`backend/app/models/application_event.py`
- 修改：`backend/app/models/__init__.py`

- [ ] **步骤 1: 创建 ApplicationEvent 模型**

```python
# backend/app/models/application_event.py
class ApplicationEvent(Base):
    """申请事件 - Application 状态变更的完整事件流"""
    __tablename__ = "application_events"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    application_id: Mapped[str] = mapped_column(String(32), ForeignKey("applications.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32))  # submitted | viewed | status_changed | etc
    from_status: Mapped[Optional[str]] = mapped_column(String(32))
    to_status: Mapped[str] = mapped_column(String(32))
    actor_type: Mapped[str] = mapped_column(String(16))  # employer | agent | system
    actor_id: Mapped[Optional[str]] = mapped_column(String(32))
    comment: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **步骤 2: 提交**

---

### 任务 7: 添加 ContactUnlock 模型

**文件：**
- 创建：`backend/app/models/contact_unlock.py`
- 修改：`backend/app/models/__init__.py`

- [ ] **步骤 1: 创建 ContactUnlock 模型**

```python
# backend/app/models/contact_unlock.py
class ContactUnlock(Base):
    """联系方式解锁 - 候选人联系方式的解锁控制"""
    __tablename__ = "contact_unlocks"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    application_id: Mapped[str] = mapped_column(String(32), ForeignKey("applications.id"), index=True)
    status: Mapped[str] = mapped_column(String(32))  # locked | candidate_authorized | unlocked | revoked
    authorized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    unlocked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **步骤 2: 提交**

---

## Phase 2: 服务架构拆分

### 任务 8: 创建 Identity Service

**文件：**
- 创建：`backend/app/services/identity_service.py`
- 依赖：Tenant, Principal, Credential 模型

- [ ] **步骤 1: 实现 IdentityService**

```python
# backend/app/services/identity_service.py
class IdentityService:
    """身份与访问服务 - 管理 Tenant/Principal/Credential"""
    
    async def create_tenant(self, db, name, tenant_type):
        ...
    
    async def create_principal(self, db, tenant_id, principal_type, name=None, email=None):
        ...
    
    async def create_credential(self, db, principal_id, credential_type, name=None):
        """创建凭证，返回明文密钥（仅显示一次）"""
        ...
    
    async def verify_credential(self, db, credential_type, credential_key) -> Optional[str]:
        """验证凭证，返回 principal_id"""
        ...
```

- [ ] **步骤 2: 提交**

---

### 任务 9: 创建 Application Service（带状态机）

**文件：**
- 创建：`backend/app/services/application_service.py`
- 修改：`backend/app/api/v1/applications.py`

- [ ] **步骤 1: 实现 ApplicationService 状态机**

```python
# backend/app/services/application_service.py
VALID_TRANSITIONS = {
    "draft": ["submitted"],
    "submitted": ["viewed", "rejected"],
    "viewed": ["shortlisted", "rejected", "interview_requested"],
    "shortlisted": ["rejected", "interview_requested", "closed"],
    "interview_requested": ["rejected", "interview_scheduled", "closed"],
    "interview_scheduled": ["rejected", "closed"],
    "closed": [],
    "rejected": [],  # 终态
}

class ApplicationService:
    async def create_application(self, db, profile_id, job_id, ...):
        """创建申请，初始状态为 draft"""
        ...
    
    async def transition_status(self, db, application_id, new_status, actor_type, actor_id, comment=None):
        """状态转换，验证合法性并记录事件"""
        # 1. 验证转换合法性
        if new_status not in VALID_TRANSITIONS.get(current_status, []):
            raise ValueError(f"Invalid transition: {current_status} -> {new_status}")
        
        # 2. 更新状态
        # 3. 创建 ApplicationEvent
        event = ApplicationEvent(
            application_id=application_id,
            event_type="status_changed",
            from_status=current_status,
            to_status=new_status,
            actor_type=actor_type,
            actor_id=actor_id,
            comment=comment
        )
        db.add(event)
```

- [ ] **步骤 2: 提交**

---

## Phase 3: API 设计强化

### 任务 10: 添加 Idempotency 支持

**文件：**
- 创建：`backend/app/middleware/idempotency.py`
- 修改：`backend/app/api/deps.py`

- [ ] **步骤 1: 实现 IdempotencyMiddleware**

```python
# backend/app/middleware/idempotency.py
from fastapi import Request, HTTPException
import hashlib

IDEMPOTENCY_HEADER = "X-Idempotency-Key"
IDEMPOTENCY_CACHE_TTL = 86400  # 24 hours

class IdempotencyMiddleware:
    async def __call__(self, request: Request, call_next):
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return await call_next(request)
        
        idempotency_key = request.headers.get(IDEMPOTENCY_HEADER)
        if not idempotency_key:
            # POST/PUT/PATCH/DELETE without idempotency key - allow but warn
            return await call_next(request)
        
        # Check if already processed
        cache_key = f"idempotency:{hashlib.sha256(idempotency_key.encode()).hexdigest()}"
        cached_response = await self.redis.get(cache_key)
        
        if cached_response:
            return cached_response
        
        response = await call_next(request)
        
        if response.status_code < 400:
            await self.redis.setex(cache_key, IDEMPOTENCY_CACHE_TTL, response.body)
        
        return response
```

- [ ] **步骤 2: 提交**

---

### 任务 11: 添加 Request ID 中间件

**文件：**
- 创建：`backend/app/middleware/request_id.py`
- 修改：`backend/app/main.py`

- [ ] **步骤 1: 实现 RequestIDMiddleware**

```python
# backend/app/middleware/request_id.py
REQUEST_ID_HEADER = "X-Request-ID"

async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get(REQUEST_ID_HEADER) or generate_id("req_")
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response
```

- [ ] **步骤 2: 提交**

---

### 任务 12: Cursor 分页支持

**文件：**
- 创建：`backend/app/utils/pagination.py`
- 修改：`backend/app/api/v1/jobs.py`, `backend/app/api/v1/profiles.py`

- [ ] **步骤 1: 实现 CursorPaginator**

```python
# backend/app/utils/pagination.py
class CursorPaginator:
    def __init__(self, db, model, order_by="created_at", limit=20):
        ...
    
    async def paginate(self, after=None, before=None):
        query = self._build_query(after, before)
        results = await self.db.execute(query.limit(self.limit + 1))
        items = results.scalars().all()
        
        has_more = len(items) > self.limit
        if has_more:
            items = items[:-1]
        
        next_cursor = self._encode_cursor(items[-1]) if has_more and items else None
        
        return {
            "items": items,
            "next_cursor": next_cursor,
            "has_more": has_more
        }
```

- [ ] **步骤 2: 提交**

---

## Phase 4: 企业审核状态机

### 任务 13: 添加 EnterpriseVerificationCase 模型

**文件：**
- 创建：`backend/app/models/enterprise_verification.py`
- 修改：`backend/app/models/__init__.py`

- [ ] **步骤 1: 创建 EnterpriseVerificationCase 模型**

```python
# backend/app/models/enterprise_verification.py
class EnterpriseVerificationCase(Base):
    """企业审核案例 - 企业实名审核的状态机"""
    __tablename__ = "enterprise_verification_cases"
    
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    enterprise_id: Mapped[str] = mapped_column(String(32), ForeignKey("enterprises.id"))
    status: Mapped[str] = mapped_column(String(32))  # draft | submitted | under_review | needs_resubmission | approved | rejected | suspended
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(32))  # admin principal_id
    review_comment: Mapped[Optional[str]] = mapped_column(Text)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **步骤 2: 提交**

---

## 自我审查清单

- [ ] Phase 1 所有任务是否完成
- [ ] 模型字段与 PRD v2 一致
- [ ] 状态机转换规则正确
- [ ] API 设计原则（幂等/pagination/request_id）已实现
- [ ] 测试覆盖核心逻辑

---

## 执行选项

**选项 1: 子 Agent 驱动（推荐）**
- 每个 Phase/任务派发独立子 Agent
- 两阶段审查（规格合规 → 代码质量）

**选项 2: 内联执行**
- 我在当前 session 逐步执行
- 适合需要人工审查的关键节点

**建议：** 选 1，后续任务多且独立，适合并行
