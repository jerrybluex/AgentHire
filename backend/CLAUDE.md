# AgentHire 后端开发说明

## 项目结构

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── agents.py      # Agent 注册/认证
│   │       ├── profiles.py    # 求职者 Profile CRUD
│   │       ├── jobs.py        # 职位 CRUD
│   │       ├── discover.py    # Agent 自主发现 API
│   │       ├── enterprise.py  # 企业注册/认证
│   │       └── skill.py       # 技能解析
│   ├── core/
│   │   ├── database.py       # 数据库连接
│   │   ├── config.py         # 配置管理
│   │   └── middleware.py     # 中间件
│   ├── models/
│   │   └── __init__.py       # SQLAlchemy 模型
│   ├── services/
│   │   ├── agent_service.py      # Agent 业务逻辑
│   │   ├── profile_service.py   # Profile 业务逻辑
│   │   ├── job_service.py       # Job 业务逻辑
│   │   ├── matching_service.py  # 自主发现服务（平台不做匹配，由 Agent 判断）
│   │   └── enterprise_service.py # 企业业务逻辑
│   └── deps.py               # 依赖注入（包含 verify_agent_signature）
├── config.py                # 应用配置
└── docker-compose.yml       # Docker 配置
```

## 核心定位

**平台 = 场地（交互协议）+ 裁判（信任安全），不做匹配算法**

Agent 自主判断是否匹配，平台只提供数据存储和搜索发现 API。

## API 路由

| 路径 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/api/v1/agents/register` | POST | 无 | 注册 Agent |
| `/api/v1/agents/authenticate` | POST | 无 | 认证 Agent |
| `/api/v1/agents/me` | GET | HMAC | 获取 Agent 信息 |
| `/api/v1/profiles` | POST | **HMAC** | 创建 Profile（需认证） |
| `/api/v1/profiles/{id}` | GET/PUT/DELETE | HMAC | Profile CRUD |
| `/api/v1/profiles` | GET | 无 | 列表 |
| `/api/v1/jobs` | POST | API Key | 发布职位 |
| `/api/v1/jobs` | GET | 无 | 搜索职位 |
| `/api/v1/discover/jobs` | GET | 无 | **Agent 自主发现职位** |
| `/api/v1/discover/profiles` | GET | 无 | **Agent 自主发现人才** |
| `/api/v1/enterprise/apply` | POST | 无 | 企业申请 |
| `/api/v1/enterprise/api-keys` | POST | Enterprise ID | 创建 API Key |
| `/api/v1/enterprise/verify` | POST | 无 | 审核企业（管理员） |

## 认证机制

### C 端（求职 Agent）- HMAC-SHA256

```python
# 签名计算
message = agent_id + timestamp
signature = HMAC-SHA256(agent_secret, message)

# 请求头
X-Agent-ID: agt_xxx
X-Timestamp: 1709337600
X-Signature: abc123...
```

### B 端（企业）- API Key

```python
# Header
X-API-Key: ah_live_xxx...

# 或
Authorization: Bearer ah_live_xxx...
```

## 依赖

认证函数 `verify_agent_signature` 定义在 `app/api/deps.py`，避免循环导入。

```python
from app.api.deps import verify_agent_signature

@router.post("/profiles")
async def create_profile(
    request: ProfileCreateRequest,
    agent_id: str = Depends(verify_agent_signature),
):
    ...
```

## 模型

核心模型位于 `app/models/__init__.py`：
- `Agent` - Agent 注册
- `SeekerProfile` - 求职者 Profile
- `JobPosting` - 职位
- `JobMatch` - 匹配记录（**保留但不再主动生成**）
- `Enterprise` - 企业
- `EnterpriseAPIKey` - API Key
- `BillingRecord` - 计费记录

## 数据库

使用 PostgreSQL。
本地开发可通过 `docker-compose.yml` 启动。

## 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## 注意事项

1. **平台不做匹配算法**：Agent 通过 `/discover/jobs` 和 `/discover/profiles` 获取原始数据，自己判断是否匹配
2. **Profile 创建需要认证**：已添加 `Depends(verify_agent_signature)`
3. **企业审核**：调用 `/enterprise/verify` 审核企业申请
4. **数据库初始化**：需要先运行迁移创建表结构
5. **JobMatch 表**：保留记录但不主动生成匹配，由 Agent 自主发现后创建