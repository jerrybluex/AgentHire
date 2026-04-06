# DevOps Agent - Week 1 任务分配

## 角色职责
负责Docker配置、部署脚本和开发环境搭建

## Week 1 目标
配置完整的Docker开发环境，包括PostgreSQL + pgvector、Redis、API服务

## 具体任务清单

### 1. Docker配置 (优先级: P0)

#### 1.1 API服务Dockerfile
- [ ] 创建 `devops/docker/Dockerfile`
  - 基于python:3.11-slim
  - 安装系统依赖（gcc, libpq-dev等）
  - 安装Python依赖
  - 配置非root用户运行
  - 健康检查配置

- [ ] 创建 `devops/docker/Dockerfile.dev`
  - 开发环境专用
  - 挂载代码卷
  - 热重载配置

#### 1.2 Docker Compose
- [ ] 创建 `docker-compose.yml` (生产/基础配置)
  - api服务
  - db服务 (PostgreSQL + pgvector)
  - redis服务
  - celery-worker服务

- [ ] 创建 `docker-compose.dev.yml` (开发环境)
  - 代码卷挂载
  - 端口映射
  - 环境变量配置
  - 调试工具

- [ ] 创建 `docker-compose.test.yml` (测试环境)
  - 独立测试数据库
  - 测试专用配置

### 2. 环境配置 (优先级: P0)
- [ ] 创建 `.env.example`
  - 所有必需环境变量示例
  - 注释说明每个变量的用途

- [ ] 创建 `.env.dev`
  - 开发环境默认配置
  - 本地开发使用

- [ ] 创建 `devops/docker/.dockerignore`
  - 排除不需要的文件
  - 优化构建速度

### 3. 初始化脚本 (优先级: P0)
- [ ] 创建 `devops/scripts/init-dev.sh`
  - 初始化开发环境
  - 创建必要目录
  - 设置权限

- [ ] 创建 `devops/scripts/wait-for-db.sh`
  - 等待数据库就绪
  - 用于docker-compose依赖控制

- [ ] 创建 `devops/scripts/start-dev.sh`
  - 一键启动开发环境
  - 包含数据库迁移

- [ ] 创建 `devops/scripts/stop-dev.sh`
  - 停止开发环境
  - 可选数据清理

### 4. CI/CD配置 (优先级: P1)
- [ ] 创建 `.github/workflows/ci.yml`
  - 代码提交触发
  - 运行测试
  - 代码质量检查

- [ ] 创建 `.github/workflows/docker-build.yml`
  - Docker镜像构建
  - 推送到镜像仓库

### 5. Nginx配置 (优先级: P1)
- [ ] 创建 `devops/docker/nginx/nginx.conf`
  - 反向代理配置
  - 静态文件服务
  - 负载均衡（预留）

- [ ] 创建 `devops/docker/nginx/Dockerfile`

### 6. 监控配置 (优先级: P2)
- [ ] 创建 `devops/docker/prometheus/prometheus.yml`
  - 基础监控配置

- [ ] 创建 `devops/docker/grafana/dashboards/` 目录
  - 预留仪表盘配置

## 依赖关系
- 依赖 Database Agent: 需要数据库初始化脚本
- 依赖 Backend Agent: 需要Dockerfile构建上下文
- 输出给 Testing Agent: 提供测试环境配置

## 验收标准
1. `docker-compose -f docker-compose.dev.yml up` 能一键启动所有服务
2. 服务启动后，API健康检查通过
3. 数据库连接正常，pgvector扩展已启用
4. 代码修改后自动重载（开发模式）
5. 日志输出正常，便于调试
6. 容器资源限制合理

## 服务架构
```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  
  db:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: agenthire
      POSTGRES_USER: agenthire
      POSTGRES_PASSWORD: dev_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
  
  celery:
    build: .
    command: celery -A app.core.celery worker --loglevel=info
    depends_on:
      - db
      - redis
```

## 参考文档
- PRD: `/docs/PRD.md` 第8章部署架构
- Docker文档: https://docs.docker.com/
- pgvector Docker: https://hub.docker.com/r/ankane/pgvector
