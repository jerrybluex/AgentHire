# AgentHire Makefile
# 简化常用 Docker 命令

.PHONY: help build up down restart logs shell test lint format clean reset

# 默认目标
.DEFAULT_GOAL := help

# 变量
COMPOSE = docker-compose
COMPOSE_PROD = docker-compose -f docker-compose.prod.yml
PROJECT_NAME = agenthire

# 帮助信息
help: ## 显示帮助信息
	@echo "AgentHire 项目管理命令"
	@echo ""
	@echo "开发环境命令:"
	@echo "  make build       - 构建开发环境镜像"
	@echo "  make up          - 启动开发环境"
	@echo "  make down        - 停止开发环境"
	@echo "  make restart     - 重启开发环境"
	@echo "  make logs        - 查看开发环境日志"
	@echo "  make logs-api    - 查看 API 服务日志"
	@echo "  make logs-worker - 查看 Worker 服务日志"
	@echo "  make shell-api   - 进入 API 容器 shell"
	@echo "  make shell-db    - 进入数据库容器 shell"
	@echo ""
	@echo "生产环境命令:"
	@echo "  make build-prod  - 构建生产环境镜像"
	@echo "  make up-prod     - 启动生产环境预览"
	@echo "  make down-prod   - 停止生产环境"
	@echo ""
	@echo "其他命令:"
	@echo "  make test        - 运行测试"
	@echo "  make lint        - 运行代码检查"
	@echo "  make format      - 格式化代码"
	@echo "  make clean       - 清理临时文件"
	@echo "  make reset       - 重置环境（删除所有数据）"
	@echo "  make ps          - 查看运行中的容器"

# ==========================================
# 开发环境命令
# ==========================================

build: ## 构建开发环境镜像
	$(COMPOSE) build

up: ## 启动开发环境
	$(COMPOSE) up -d

down: ## 停止开发环境
	$(COMPOSE) down

restart: ## 重启开发环境
	$(COMPOSE) restart

logs: ## 查看开发环境日志
	$(COMPOSE) logs -f

logs-api: ## 查看 API 服务日志
	$(COMPOSE) logs -f api

logs-worker: ## 查看 Worker 服务日志
	$(COMPOSE) logs -f worker

logs-db: ## 查看数据库日志
	$(COMPOSE) logs -f db

logs-redis: ## 查看 Redis 日志
	$(COMPOSE) logs -f redis

shell-api: ## 进入 API 容器 shell
	$(COMPOSE) exec api /bin/bash

shell-worker: ## 进入 Worker 容器 shell
	$(COMPOSE) exec worker /bin/bash

shell-db: ## 进入数据库容器 shell
	$(COMPOSE) exec db psql -U agenthire -d agenthire

shell-redis: ## 进入 Redis 容器 shell
	$(COMPOSE) exec redis redis-cli

migrate: ## 运行数据库迁移
	$(COMPOSE) exec api alembic upgrade head

makemigrations: ## 创建数据库迁移
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(msg)"

# ==========================================
# 生产环境命令
# ==========================================

build-prod: ## 构建生产环境镜像
	$(COMPOSE_PROD) build

up-prod: ## 启动生产环境预览
	$(COMPOSE_PROD) up -d

down-prod: ## 停止生产环境
	$(COMPOSE_PROD) down

logs-prod: ## 查看生产环境日志
	$(COMPOSE_PROD) logs -f

# ==========================================
# 开发和测试命令
# ==========================================

test: ## 运行测试
	$(COMPOSE) exec api pytest -v

test-cov: ## 运行测试并生成覆盖率报告
	$(COMPOSE) exec api pytest --cov=app --cov-report=html

lint: ## 运行代码检查
	$(COMPOSE) exec api flake8 app
	$(COMPOSE) exec api mypy app

format: ## 格式化代码
	$(COMPOSE) exec api black app
	$(COMPOSE) exec api isort app

# ==========================================
# 维护命令
# ==========================================

ps: ## 查看运行中的容器
	$(COMPOSE) ps
	@echo ""
	@echo "所有容器:"
	docker ps -a --filter "name=agenthire"

clean: ## 清理临时文件
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage 2>/dev/null || true
	@echo "清理完成"

reset: ## 重置环境（删除所有数据）
	@echo "⚠️  警告：这将删除所有数据卷，包括数据库数据！"
	@read -p "确定要继续吗？输入 'yes' 确认: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(COMPOSE) down -v; \
		$(COMPOSE_PROD) down -v 2>/dev/null || true; \
		docker volume prune -f; \
		echo "环境已重置"; \
	else \
		echo "操作已取消"; \
	fi

backup-db: ## 备份数据库
	@mkdir -p backups
	$(COMPOSE) exec db pg_dump -U agenthire -d agenthire > backups/agenthire_$$(date +%Y%m%d_%H%M%S).sql
	@echo "数据库备份完成"

restore-db: ## 恢复数据库（用法: make restore-db file=backups/xxx.sql）
	@if [ -z "$(file)" ]; then \
		echo "请指定备份文件: make restore-db file=backups/xxx.sql"; \
		exit 1; \
	fi
	$(COMPOSE) exec -T db psql -U agenthire -d agenthire < $(file)
	@echo "数据库恢复完成"

# ==========================================
# 快捷命令
# ==========================================

dev: build up ## 构建并启动开发环境
	@echo "开发环境启动完成！"
	@echo "API 文档: http://localhost/docs"

prod: build-prod up-prod ## 构建并启动生产环境预览
	@echo "生产环境预览启动完成！"
	@echo "API 文档: https://localhost/docs"
