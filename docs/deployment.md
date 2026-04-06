# AgentHire 部署指南

本文档介绍如何搭建和部署AgentHire开发及生产环境。

---

## 目录

- [环境要求](#环境要求)
- [开发环境搭建](#开发环境搭建)
- [Docker部署](#docker部署)
- [环境变量说明](#环境变量说明)
- [生产环境部署](#生产环境部署)
- [故障排查](#故障排查)

---

## 环境要求

### 基础要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Docker | 20.10.0 | 24.0.0+ |
| Docker Compose | 2.0.0 | 2.20.0+ |
| Python | 3.11 | 3.11+ |
| PostgreSQL | 15 | 15+ |
| Redis | 7 | 7+ |

### 系统要求

- **CPU**: 4核+
- **内存**: 8GB+
- **磁盘**: 50GB+ SSD
- **网络**: 可访问互联网（拉取镜像和模型）

---

## 开发环境搭建

### 1. 克隆项目

```bash
git clone https://github.com/your-org/agenthire.git
cd agenthire
```

### 2. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
nano .env  # 或 vim .env
```

### 3. 使用Docker Compose启动

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
```

### 4. 验证安装

```bash
# 健康检查
curl http://localhost:8000/health

# 预期响应
{"status": "healthy", "version": "0.1.0"}
```

### 5. 访问服务

| 服务 | URL | 说明 |
|------|-----|------|
| API文档 | http://localhost:8000/docs | Swagger UI |
| ReDoc | http://localhost:8000/redoc | 替代文档 |
| MinIO控制台 | http://localhost:9001 | 对象存储管理 |
| Nginx | http://localhost | 反向代理入口 |

---

## Docker部署

### 服务架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│  FastAPI    │────▶│ PostgreSQL  │
│   (80)      │     │   (8000)    │     │  (5432)     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Celery    │     │  pgvector   │
                    │   Worker    │     │  extension  │
                    └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    Redis    │────▶│   MinIO     │
                    │   (6379)    │     │  (9000)     │
                    └─────────────┘     └─────────────┘
```

### 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 停止并删除数据卷（谨慎使用）
docker-compose down -v

# 重启服务
docker-compose restart api

# 重建并启动
docker-compose up -d --build

# 查看服务日志
docker-compose logs -f [service_name]

# 进入容器
docker-compose exec api bash

# 执行数据库迁移
docker-compose exec api alembic upgrade head

# 查看资源使用
docker-compose stats
```

### 服务说明

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| api | agenthire-api | 8000 | FastAPI主服务 |
| worker | agenthire-worker | - | Celery异步任务 |
| scheduler | agenthire-scheduler | - | Celery定时任务 |
| db | agenthire-db | 5432 | PostgreSQL数据库 |
| redis | agenthire-redis | 6379 | Redis缓存/队列 |
| minio | agenthire-minio | 9000/9001 | 对象存储 |
| nginx | agenthire-nginx | 80 | 反向代理 |

---

## 环境变量说明

### 核心配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `ENVIRONMENT` | 否 | `development` | 运行环境: development/staging/production |
| `DEBUG` | 否 | `true` | 调试模式 |
| `LOG_LEVEL` | 否 | `DEBUG` | 日志级别: DEBUG/INFO/WARNING/ERROR |

### 数据库配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `POSTGRES_DB` | 否 | `agenthire` | 数据库名 |
| `POSTGRES_USER` | 否 | `agenthire` | 数据库用户 |
| `POSTGRES_PASSWORD` | 是 | - | 数据库密码（生产环境必须修改） |
| `DATABASE_URL` | 否 | - | 完整数据库URL，优先级高于分项配置 |

### Redis配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `REDIS_URL` | 否 | `redis://redis:6379/0` | Redis连接URL |
| `CELERY_BROKER_URL` | 否 | `redis://redis:6379/1` | Celery Broker |
| `CELERY_RESULT_BACKEND` | 否 | `redis://redis:6379/2` | Celery结果存储 |

### MinIO配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `MINIO_ENDPOINT` | 否 | `minio:9000` | MinIO服务端点 |
| `MINIO_ACCESS_KEY` | 否 | `minioadmin` | 访问密钥 |
| `MINIO_SECRET_KEY` | 否 | `minioadmin123` | 秘密密钥 |
| `MINIO_BUCKET_NAME` | 否 | `agenthire` | 默认Bucket名称 |
| `MINIO_USE_SSL` | 否 | `false` | 是否使用SSL |

### 安全配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `JWT_SECRET_KEY` | 是 | - | JWT签名密钥（生产环境必须设置） |
| `JWT_ALGORITHM` | 否 | `HS256` | JWT算法 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | `60` | Token过期时间(分钟) |

### LLM API配置（简历解析和意图理解需要）

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `OPENAI_API_KEY` | 否 | - | OpenAI API密钥 |
| `ANTHROPIC_API_KEY` | 否 | - | Anthropic API密钥 |
| `LLM_PROVIDER` | 否 | `openai` | LLM提供商: openai/anthropic/local |
| `LLM_MODEL` | 否 | `gpt-4` | 使用的模型 |

### 向量模型配置

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `EMBEDDING_MODEL` | 否 | `BAAI/bge-large-zh` | 嵌入模型名称 |
| `EMBEDDING_DIMENSION` | 否 | `384` | 向量维度 |
| `VECTOR_SEARCH_TOP_K` | 否 | `100` | 向量搜索返回数量 |

### 邮件配置（企业认证通知）

| 变量名 | 必需 | 默认值 | 说明 |
|--------|------|--------|------|
| `SMTP_HOST` | 否 | - | SMTP服务器地址 |
| `SMTP_PORT` | 否 | `587` | SMTP端口 |
| `SMTP_USER` | 否 | - | SMTP用户名 |
| `SMTP_PASSWORD` | 否 | - | SMTP密码 |
| `EMAIL_FROM` | 否 | - | 发件人地址 |

### 完整.env.example参考

```bash
# ===========================================
# AgentHire 环境变量配置
# ===========================================

# 基础配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG

# 数据库配置
POSTGRES_DB=agenthire
POSTGRES_USER=agenthire
POSTGRES_PASSWORD=agenthire123

# Redis配置
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# MinIO配置
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=agenthire
MINIO_USE_SSL=false

# 安全配置（生产环境必须修改！）
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60

# LLM API配置（可选，用于简历解析）
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 向量模型配置
EMBEDDING_MODEL=BAAI/bge-large-zh
EMBEDDING_DIMENSION=384
```

---

## 生产环境部署

### 1. 准备工作

```bash
# 1. 准备服务器（推荐Ubuntu 22.04 LTS）
# 2. 安装Docker和Docker Compose
curl -fsSL https://get.docker.com | sh

# 3. 克隆项目
git clone https://github.com/your-org/agenthire.git /opt/agenthire
cd /opt/agenthire

# 4. 切换到生产分支
git checkout main
```

### 2. 配置生产环境

```bash
# 创建生产环境配置
cp .env.example .env.production
nano .env.production
```

**生产环境必须修改的配置：**

```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 强密码！
POSTGRES_PASSWORD=<随机生成的强密码>
JWT_SECRET_KEY=<随机生成的32位以上密钥>
MINIO_SECRET_KEY=<随机生成的强密码>

# 使用外部LLM服务
OPENAI_API_KEY=sk-...
```

### 3. 使用生产配置启动

```bash
# 使用生产环境配置
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 或者使用Makefile
make deploy-production
```

### 4. 配置SSL证书

使用Let's Encrypt免费证书：

```bash
# 安装certbot
docker-compose exec nginx certbot --nginx -d api.agenthire.io

# 自动续期
echo "0 12 * * * docker-compose exec nginx certbot renew" | crontab -
```

### 5. 配置监控

```bash
# 启动监控栈（Prometheus + Grafana）
docker-compose -f docker-compose.monitoring.yml up -d
```

### 6. 备份策略

```bash
# 数据库备份脚本
#!/bin/bash
BACKUP_DIR="/backup/agenthire"
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U agenthire agenthire > $BACKUP_DIR/db_$DATE.sql

# 保留最近7天备份
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
```

添加到crontab：
```bash
0 2 * * * /opt/agenthire/scripts/backup.sh
```

---

## 故障排查

### 常见问题

#### 1. 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 8000

# 检查日志
docker-compose logs api

# 检查环境变量
docker-compose exec api env | grep DATABASE
```

#### 2. 数据库连接失败

```bash
# 检查数据库状态
docker-compose ps db
docker-compose logs db

# 进入数据库容器检查
docker-compose exec db psql -U agenthire -d agenthire -c "\dt"
```

#### 3. 迁移失败

```bash
# 查看迁移状态
docker-compose exec api alembic current

# 手动执行迁移
docker-compose exec api alembic upgrade head

# 回滚迁移（谨慎使用）
docker-compose exec api alembic downgrade -1
```

#### 4. 内存不足

```bash
# 查看资源使用
docker-compose stats

# 限制服务内存（docker-compose.yml）
services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

#### 5. 权限问题

```bash
# 修复文件权限
sudo chown -R 1000:1000 ./backend

# 检查SELinux（如果启用）
getenforce
setenforce 0  # 临时关闭
```

### 调试命令

```bash
# 进入API容器
docker-compose exec api bash

# 运行测试
docker-compose exec api pytest

# 检查Python环境
docker-compose exec api pip list

# 查看网络
docker-compose exec api ping db

# 检查Redis
docker-compose exec redis redis-cli ping
```

### 日志收集

```bash
# 导出所有日志
docker-compose logs > agenthire_logs_$(date +%Y%m%d).txt

# 查看特定时间段的错误
docker-compose logs api | grep ERROR | tail -100
```

---

## 升级指南

### 平滑升级步骤

```bash
# 1. 备份数据
./scripts/backup.sh

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建镜像
docker-compose build --no-cache

# 4. 执行数据库迁移
docker-compose up -d db
docker-compose run --rm api alembic upgrade head

# 5. 重启服务
docker-compose up -d

# 6. 验证健康检查
curl http://localhost:8000/health
```

---

## 性能优化

### 数据库优化

```sql
-- 添加常用查询索引
CREATE INDEX CONCURRENTLY idx_job_matches_status ON job_matches(seeker_id, status);
CREATE INDEX CONCURRENTLY idx_jobs_status_expires ON job_postings(status, expires_at);

-- 分析表
ANALYZE seeker_profiles;
ANALYZE job_postings;
```

### 缓存策略

```bash
# Redis缓存配置
# 在docker-compose.yml中调整
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

---

## 安全建议

1. **修改默认密码** - 所有默认密码在生产环境必须修改
2. **使用HTTPS** - 生产环境强制SSL
3. **限制端口访问** - 仅开放80/443，数据库不暴露公网
4. **定期更新** - 及时更新基础镜像和依赖
5. **日志审计** - 启用访问日志并定期审计

---

## 获取帮助

- **GitHub Issues**: https://github.com/your-org/agenthire/issues
- **文档**: https://docs.agenthire.io
- **邮件**: support@agenthire.io
