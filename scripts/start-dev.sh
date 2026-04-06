#!/bin/bash
# AgentHire 开发环境启动脚本
# 由 DevOps Agent 维护

echo "=== AgentHire 开发环境启动 ==="

# 检查 Docker
docker --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "错误: Docker 未安装"
    exit 1
fi

docker-compose --version > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "错误: Docker Compose 未安装"
    exit 1
fi

# 创建必要目录
echo "创建数据目录..."
mkdir -p data/postgres data/redis data/minio

# 启动服务
echo "启动服务..."
docker-compose -f docker-compose.dev.yml up -d

# 等待数据库就绪
echo "等待数据库就绪..."
sleep 5

# 执行数据库迁移
echo "执行数据库迁移..."
cd backend
alembic upgrade head

echo "=== 开发环境启动完成 ==="
echo "API: http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""
echo "查看日志: docker-compose -f docker-compose.dev.yml logs -f"
echo "停止服务: docker-compose -f docker-compose.dev.yml down"
