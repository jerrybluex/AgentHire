# AgentHire Backend

AI Agent驱动的去中心化招聘平台后端服务

## 技术栈

- **框架**: FastAPI (Python 3.11+)
- **数据库**: PostgreSQL
- **ORM**: SQLAlchemy 2.0 + Alembic (迁移)
- **缓存/队列**: Redis + Celery
- **数据验证**: Pydantic v2
- **部署**: Docker + Docker Compose

## 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
# 或安装开发依赖
pip install -e ".[dev]"
```

### 2. 环境变量配置

```bash
cp .env.example .env
# 编辑 .env 文件配置数据库连接等
```

### 3. 数据库迁移

```bash
# 初始化迁移（首次）
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "initial migration"

# 执行迁移
alembic upgrade head
```

### 4. 启动服务

```bash
# 开发模式（热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── api/                 # API路由
│   │   ├── v1/
│   │   │   ├── skill.py     # Skill API
│   │   │   ├── profiles.py  # Profile管理
│   │   │   ├── jobs.py      # 职位管理
│   │   │   ├── matching.py  # 匹配引擎
│   │   │   └── enterprise.py # B端API
│   ├── core/                # 核心功能
│   │   ├── security.py      # 安全相关
│   │   ├── middleware.py    # 中间件
│   │   └── utils.py         # 工具函数
│   ├── models/              # SQLAlchemy模型
│   ├── schemas/             # Pydantic模型
│   └── services/            # 业务逻辑
├── alembic/                 # 数据库迁移
├── tests/                   # 测试
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pyproject.toml
```

## API文档

启动服务后访问：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 开发规范

- 使用 `ruff` 进行代码格式化
- 使用 `mypy` 进行类型检查
- 遵循 PEP 8 规范
- 所有函数必须添加类型注解

## Week 1 任务分配

### 当前阶段目标
搭建FastAPI项目框架，完成基础API结构和配置

### 具体任务清单

#### 1. 项目初始化 (优先级: P0)
- [ ] 创建 `requirements.txt`，包含以下依赖：
  - fastapi>=0.104.0
  - uvicorn[standard]>=0.24.0
  - pydantic>=2.5.0
  - pydantic-settings>=2.1.0
  - sqlalchemy>=2.0.0
  - alembic>=1.12.0
  - python-multipart>=0.0.6
  - python-jose[cryptography]>=3.3.0
  - passlib[bcrypt]>=1.7.4
  - httpx>=0.25.0
  - celery>=5.3.0
  - redis>=5.0.0
  - pytest>=7.4.0
  - pytest-asyncio>=0.21.0

#### 2. FastAPI应用结构 (优先级: P0)
- [ ] 创建 `backend/app/main.py` - 应用入口
  - 初始化FastAPI实例
  - 配置CORS中间件
  - 注册路由
  - 健康检查端点 `/health`

- [ ] 创建 `backend/app/core/config.py` - 配置管理
  - 使用Pydantic Settings
  - 支持.env文件加载
  - 配置项：DATABASE_URL, REDIS_URL, SECRET_KEY等

- [ ] 创建 `backend/app/core/__init__.py`

#### 3. 数据库连接 (优先级: P0)
- [ ] 创建 `backend/app/core/database.py`
  - SQLAlchemy引擎配置
  - SessionLocal工厂
  - 异步数据库支持配置
  - get_db()依赖函数

#### 4. API路由结构 (优先级: P0)
- [ ] 创建 `backend/app/api/__init__.py`
- [ ] 创建 `backend/app/api/v1/__init__.py`
- [ ] 创建 `backend/app/api/v1/api.py` - v1版本路由聚合
- [ ] 创建 `backend/app/api/deps.py` - 通用依赖（数据库、认证等）

#### 5. 基础模型 (优先级: P1)
- [ ] 创建 `backend/app/models/__init__.py`
- [ ] 创建基础Base类 `backend/app/models/base.py`
- [ ] 创建 `backend/app/models/seeker.py` - 求职者Profile模型（基础字段）
- [ ] 创建 `backend/app/models/job.py` - 职位模型（基础字段）
- [ ] 创建 `backend/app/models/enterprise.py` - 企业模型（基础字段）

#### 6. Pydantic Schema (优先级: P1)
- [ ] 创建 `backend/app/schemas/__init__.py`
- [ ] 创建 `backend/app/schemas/base.py` - 基础响应模型
- [ ] 创建 `backend/app/schemas/seeker.py` - Profile相关Schema
- [ ] 创建 `backend/app/schemas/job.py` - 职位相关Schema

#### 7. 工具函数 (优先级: P1)
- [ ] 创建 `backend/app/utils/__init__.py`
- [ ] 创建 `backend/app/utils/id_generator.py` - ID生成器（nanoid风格）
- [ ] 创建 `backend/app/utils/datetime_utils.py` - 时间处理工具

#### 8. 服务层接口 (优先级: P2)
- [ ] 创建 `backend/app/services/__init__.py`
- [ ] 创建 `backend/app/services/base.py` - 服务基类

### 依赖关系
- 依赖 Database Agent: 需要数据库schema作为参考
- 输出给 Testing Agent: 提供API结构用于测试

### 验收标准
1. `docker-compose up` 能正常启动API服务
2. 访问 `http://localhost:8000/health` 返回 `{"status": "ok"}`
3. 访问 `http://localhost:8000/docs` 显示Swagger文档
4. 代码通过 `pytest` 基础测试
5. 所有模型和Schema有类型注解

### 接口约定
- API版本: v1
- 基础路径: `/api/v1`
- 响应格式统一:
```json
{
  "success": true,
  "data": {},
  "message": null
}
```

---

## 许可证

MIT License
