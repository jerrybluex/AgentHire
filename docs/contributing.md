# AgentHire 贡献指南

感谢你对AgentHire项目的关注！本文档将帮助你了解如何参与项目贡献。

---

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [代码规范](#代码规范)
- [提交PR流程](#提交pr流程)
- [开发工作流](#开发工作流)
- [测试要求](#测试要求)
- [文档规范](#文档规范)

---

## 行为准则

参与本项目即表示你同意遵守以下准则：

- 尊重所有参与者，保持友善和建设性
- 接受建设性批评，专注于对社区最有利的事情
- 禁止任何形式的骚扰、歧视或不尊重行为

---

## 如何贡献

### 报告Bug

如果你发现了bug，请通过 [GitHub Issues](https://github.com/your-org/agenthire/issues) 提交，并包含以下信息：

- 问题的清晰描述
- 复现步骤
- 预期行为 vs 实际行为
- 环境信息（OS、Python版本等）
- 相关日志或截图

### 提交功能建议

- 使用清晰的标题描述功能
- 详细说明功能的用例和价值
- 如果可能，提供实现思路

### 提交代码

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 代码规范

### Python 代码规范

我们遵循 [PEP 8](https://pep8.org/) 规范，使用以下工具确保代码质量：

#### 1. 代码格式化

```bash
# 使用black格式化代码
black backend/app

# 使用isort排序导入
isort backend/app
```

#### 2. 代码检查

```bash
# 使用flake8检查代码
flake8 backend/app

# 使用mypy进行类型检查
mypy backend/app
```

#### 3. 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块/包 | 小写，下划线分隔 | `job_matching.py` |
| 类 | 大驼峰 | `JobMatcher` |
| 函数/方法 | 小写，下划线分隔 | `calculate_match_score` |
| 常量 | 大写，下划线分隔 | `MAX_MATCH_RESULTS` |
| 变量 | 小写，下划线分隔 | `match_score` |
| 私有属性 | 下划线前缀 | `_internal_cache` |

#### 4. 文档字符串规范

使用Google风格文档字符串：

```python
def calculate_match_score(
    profile: SeekerProfile,
    job: JobPosting
) -> float:
    """Calculate match score between a profile and job posting.

    Args:
        profile: The seeker's profile containing skills and preferences.
        job: The job posting with requirements.

    Returns:
        A float between 0 and 1 representing the match score.
        Higher values indicate better matches.

    Raises:
        ValueError: If profile or job is missing required fields.

    Example:
        >>> score = calculate_match_score(profile, job)
        >>> print(f"Match score: {score:.2f}")
        Match score: 0.85
    """
    ...
```

#### 5. 类型注解

所有函数参数和返回值都应添加类型注解：

```python
from typing import List, Optional, Dict, Any

async def find_matches(
    profile_id: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[MatchResult]:
    ...
```

### 项目结构规范

```
backend/app/
├── api/                 # API路由层
│   └── v1/
│       ├── api.py       # 路由聚合
│       └── endpoints/   # 具体端点
├── core/                # 核心配置
│   ├── config.py        # 配置管理
│   ├── security.py      # 安全相关
│   └── middleware.py    # 中间件
├── models/              # SQLAlchemy模型
├── schemas/             # Pydantic模型
├── services/            # 业务逻辑层
├── utils/               # 工具函数
└── tests/               # 测试代码
```

### 数据库规范

#### 表命名
- 小写，复数形式，下划线分隔
- 示例：`seeker_profiles`, `job_postings`

#### 字段命名
- 小写，下划线分隔
- 避免SQL保留字
- 示例：`created_at`, `match_score`

#### ID格式
- Profile: `prof_` + nanoid (12位)
- Job: `job_` + nanoid (12位)
- Enterprise: `ent_` + nanoid (12位)
- Match: `match_` + nanoid (12位)

### API设计规范

#### RESTful原则

| 操作 | HTTP方法 | URL |
|------|---------|-----|
| 创建 | POST | `/api/v1/resource` |
| 读取(列表) | GET | `/api/v1/resource` |
| 读取(单个) | GET | `/api/v1/resource/{id}` |
| 更新 | PUT/PATCH | `/api/v1/resource/{id}` |
| 删除 | DELETE | `/api/v1/resource/{id}` |

#### 响应格式

```json
{
  "success": true,
  "data": { },
  "message": null,
  "error": null
}
```

#### 错误处理

```python
# 使用HTTPException
from fastapi import HTTPException

raise HTTPException(
    status_code=404,
    detail={
        "code": "RESOURCE_NOT_FOUND",
        "message": "Profile not found",
        "details": {"profile_id": "prof_xxx"}
    }
)
```

---

## 提交PR流程

### 1. 准备工作

```bash
# 同步上游仓库
git remote add upstream https://github.com/your-org/agenthire.git
git fetch upstream
git checkout main
git merge upstream/main

# 创建特性分支
git checkout -b feature/your-feature-name
```

### 2. 开发规范

- 每个PR专注于一个功能或修复
- 保持提交历史整洁
- 提交信息清晰描述变更

### 3. 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Type说明

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug修复 |
| `docs` | 文档更新 |
| `style` | 代码格式（不影响功能） |
| `refactor` | 重构 |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具相关 |

#### 示例

```
feat(matching): add vector similarity search

- Implement cosine similarity calculation
- Add pgvector index for fast search
- Update API to support vector filters

Closes #123
```

### 4. 提交前检查

```bash
# 运行代码检查
make lint

# 运行测试
make test

# 检查测试覆盖率
make coverage
```

### 5. 创建PR

在GitHub上创建PR时，请包含：

- **标题**: 简洁描述变更
- **描述**: 
  - 变更的目的和背景
  - 主要的代码变更
  - 测试覆盖情况
  - 相关Issue链接

#### PR模板

```markdown
## 描述
简要描述这个PR做了什么

## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 破坏性变更
- [ ] 文档更新

## 测试
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试通过

## 检查清单
- [ ] 代码遵循项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 所有检查通过
```

### 6. 代码审查

- 至少需要一个维护者审查
- 解决所有审查意见
- 保持CI检查通过

### 7. 合并

- 使用 **Squash and Merge** 保持历史整洁
- 删除已合并的分支

---

## 开发工作流

### 本地开发

```bash
# 1. 启动开发环境
docker-compose up -d

# 2. 进入API容器
docker-compose exec api bash

# 3. 安装开发依赖
pip install -e ".[dev]"

# 4. 运行开发服务器（热重载）
uvicorn app.main:app --reload
```

### 数据库迁移

```bash
# 创建迁移
docker-compose exec api alembic revision --autogenerate -m "Add new table"

# 执行迁移
docker-compose exec api alembic upgrade head

# 回滚迁移
docker-compose exec api alembic downgrade -1
```

### 运行测试

```bash
# 运行所有测试
make test

# 运行特定测试
docker-compose exec api pytest tests/test_matching.py -v

# 运行测试并生成覆盖率报告
make coverage
```

---

## 测试要求

### 测试覆盖率要求

- 整体覆盖率 >= 80%
- 核心业务逻辑 >= 90%
- API端点必须有集成测试

### 测试结构

```python
# tests/test_services/test_matching.py
import pytest
from app.services.matching import calculate_match_score

class TestMatchingService:
    """Test cases for matching service."""

    def test_calculate_match_score_exact_match(self):
        """Test matching with identical skills."""
        profile = create_test_profile(skills=["Python", "FastAPI"])
        job = create_test_job(requirements=["Python", "FastAPI"])
        
        score = calculate_match_score(profile, job)
        
        assert score == 1.0

    def test_calculate_match_score_partial_match(self):
        """Test matching with partial skill overlap."""
        ...

    @pytest.mark.parametrize("skill_count,expected", [
        (0, 0.0),
        (5, 0.5),
        (10, 1.0),
    ])
    def test_match_score_with_various_skills(self, skill_count, expected):
        """Test match score calculation with different skill counts."""
        ...
```

### 测试数据

使用fixtures提供测试数据：

```python
# tests/conftest.py
import pytest

@pytest.fixture
def test_profile():
    return {
        "id": "prof_test123",
        "nickname": "Test User",
        "skills": ["Python", "FastAPI"],
        "experience_years": 3
    }
```

---

## 文档规范

### 代码文档

- 所有公共API必须有文档字符串
- 复杂逻辑需要注释说明
- 使用类型注解

### API文档

- 使用FastAPI自动生成的OpenAPI文档
- 所有端点必须有summary和description
- 使用Pydantic模型定义请求/响应

```python
@router.post(
    "/profiles",
    response_model=ProfileResponse,
    summary="Create seeker profile",
    description="Create a new seeker profile with job intent and preferences.",
    tags=["profiles"]
)
async def create_profile(
    data: ProfileCreate,
    db: AsyncSession = Depends(get_db)
):
    ...
```

### 变更日志

重要变更需要更新 [CHANGELOG.md](../CHANGELOG.md)：

```markdown
## [Unreleased]

### Added
- New feature X

### Changed
- Behavior of Y

### Fixed
- Bug in Z
```

---

## 获取帮助

- **GitHub Discussions**: 一般性问题讨论
- **GitHub Issues**: Bug报告和功能请求
- **邮件**: dev@agenthire.io

---

## 许可证

通过贡献代码，你同意你的贡献将在 [MIT License](../LICENSE) 下发布。

---

感谢你的贡献！
