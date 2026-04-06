# Testing Agent - Week 1 任务分配

## 角色职责
负责测试框架搭建、测试用例编写和CI集成

## Week 1 目标
搭建测试框架，编写基础测试用例，配置测试环境

## 具体任务清单

### 1. 测试框架配置 (优先级: P0)
- [ ] 创建 `testing/pytest.ini`
  - 测试配置
  - 异步测试支持
  - 测试路径配置
  - 覆盖率配置

- [ ] 创建 `testing/conftest.py`
  - 共享fixture定义
  - 数据库连接fixture
  - 测试客户端fixture
  - 异步事件循环fixture

### 2. 测试工具 (优先级: P0)
- [ ] 创建 `testing/utils/__init__.py`
- [ ] 创建 `testing/utils/factories.py`
  - 测试数据工厂
  - 使用factory_boy或类似工具

- [ ] 创建 `testing/utils/helpers.py`
  - 测试辅助函数
  - 数据库清理工具

### 3. 单元测试 (优先级: P0)
- [ ] 创建 `testing/unit/__init__.py`
- [ ] 创建 `testing/unit/test_config.py`
  - 配置加载测试
  - 环境变量测试

- [ ] 创建 `testing/unit/test_models/` 目录
  - 模型基础测试
  - 字段验证测试

- [ ] 创建 `testing/unit/test_utils/` 目录
  - ID生成器测试
  - 时间工具测试

### 4. 集成测试 (优先级: P1)
- [ ] 创建 `testing/integration/__init__.py`
- [ ] 创建 `testing/integration/test_api/` 目录
  - API端点测试
  - 响应格式测试

- [ ] 创建 `testing/integration/test_db/` 目录
  - 数据库连接测试
  - 迁移测试

### 5.  fixtures (优先级: P1)
- [ ] 创建 `testing/fixtures/seeker_profiles.json`
  - 测试用求职者数据
  - 包含向量数据

- [ ] 创建 `testing/fixtures/job_postings.json`
  - 测试用职位数据
  - 包含向量数据

- [ ] 创建 `testing/fixtures/enterprises.json`
  - 测试用企业数据

### 6. 测试数据 (优先级: P1)
- [ ] 创建 `testing/data/sample_resume.pdf`
  - 示例PDF简历（用于解析测试）

- [ ] 创建 `testing/data/sample_resume.docx`
  - 示例Word简历

- [ ] 创建 `testing/data/sample_resume.txt`
  - 简历文本内容（用于对比）

### 7. 测试脚本 (优先级: P2)
- [ ] 创建 `testing/scripts/run_tests.sh`
  - 运行所有测试
  - 生成覆盖率报告

- [ ] 创建 `testing/scripts/run_unit.sh`
  - 仅运行单元测试

- [ ] 创建 `testing/scripts/run_integration.sh`
  - 仅运行集成测试

## 依赖关系
- 依赖 Backend Agent: 需要API代码进行测试
- 依赖 DevOps Agent: 需要测试环境配置
- 依赖 Database Agent: 需要数据库schema

## 验收标准
1. `pytest` 命令能正常运行所有测试
2. 测试覆盖率报告生成成功
3. 所有fixture能正常工作
4. 测试数据库隔离，不影响开发数据
5. 测试能在CI环境中运行
6. 测试运行时间合理（单元测试<30秒）

## 测试结构
```
testing/
├── conftest.py          # 全局fixture
├── pytest.ini          # 测试配置
├── unit/               # 单元测试
│   ├── test_config.py
│   ├── test_models/
│   └── test_utils/
├── integration/        # 集成测试
│   ├── test_api/
│   └── test_db/
├── e2e/               # 端到端测试（预留）
├── fixtures/          # 测试数据
├── data/              # 测试文件
└── utils/             # 测试工具
```

## 测试示例
```python
# conftest.py示例
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    # 创建测试数据库会话
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

# 测试示例
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

## 参考文档
- PRD: `/docs/PRD.md` 第9.3节验收标准
- pytest文档: https://docs.pytest.org/
- FastAPI测试: https://fastapi.tiangolo.com/tutorial/testing/
