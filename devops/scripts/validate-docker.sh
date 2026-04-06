#!/bin/bash
# AgentHire Docker 配置验证脚本
# 用于验证 Docker 和 Docker Compose 配置是否正确

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

print_info "开始验证 Docker 配置..."
print_info "项目根目录: $PROJECT_ROOT"
echo ""

# 检查文件是否存在
check_files() {
    print_info "检查必要文件..."
    local files=(
        "docker-compose.yml"
        "backend/Dockerfile"
        "backend/Dockerfile.worker"
        "backend/.dockerignore"
        "devops/docker/.dockerignore"
        "devops/nginx/nginx.dev.conf"
        "devops/redis/redis.conf"
        "devops/init-scripts/01-init.sql"
        "devops/scripts/init-db.sh"
        "devops/scripts/start.sh"
        ".env.example"
    )

    local all_exist=true
    for file in "${files[@]}"; do
        if [ -f "$file" ]; then
            print_success "✓ $file"
        else
            print_error "✗ $file (缺失)"
            all_exist=false
        fi
    done

    if [ "$all_exist" = true ]; then
        print_success "所有必要文件都存在"
        return 0
    else
        print_error "部分文件缺失"
        return 1
    fi
}

# 验证 docker-compose.yml 语法
validate_compose() {
    print_info ""
    print_info "验证 docker-compose.yml 语法..."

    if command -v docker-compose &> /dev/null; then
        if docker-compose config > /dev/null 2>&1; then
            print_success "docker-compose.yml 语法正确"
            return 0
        else
            print_error "docker-compose.yml 语法错误"
            return 1
        fi
    elif docker compose version &> /dev/null; then
        if docker compose config > /dev/null 2>&1; then
            print_success "docker-compose.yml 语法正确"
            return 0
        else
            print_error "docker-compose.yml 语法错误"
            return 1
        fi
    else
        print_warning "Docker Compose 未安装，跳过语法验证"
        return 0
    fi
}

# 检查 Dockerfile 语法
validate_dockerfile() {
    print_info ""
    print_info "检查 Dockerfile..."

    if [ -f "backend/Dockerfile" ]; then
        # 简单检查 Dockerfile 是否包含必要指令
        if grep -q "FROM" backend/Dockerfile; then
            print_success "backend/Dockerfile 包含 FROM 指令"
        else
            print_error "backend/Dockerfile 缺少 FROM 指令"
        fi

        if grep -q "CMD\|ENTRYPOINT" backend/Dockerfile; then
            print_success "backend/Dockerfile 包含启动指令"
        else
            print_error "backend/Dockerfile 缺少启动指令"
        fi
    fi

    if [ -f "backend/Dockerfile.worker" ]; then
        if grep -q "FROM" backend/Dockerfile.worker; then
            print_success "backend/Dockerfile.worker 包含 FROM 指令"
        else
            print_error "backend/Dockerfile.worker 缺少 FROM 指令"
        fi
    fi
}

# 检查环境变量配置
check_env_config() {
    print_info ""
    print_info "检查环境变量配置..."

    if [ -f ".env.example" ]; then
        local required_vars=(
            "POSTGRES_DB"
            "POSTGRES_USER"
            "POSTGRES_PASSWORD"
            "DATABASE_URL"
            "REDIS_URL"
            "CELERY_BROKER_URL"
            "CELERY_RESULT_BACKEND"
            "JWT_SECRET_KEY"
        )

        local all_found=true
        for var in "${required_vars[@]}"; do
            if grep -q "$var" .env.example; then
                print_success "✓ $var"
            else
                print_error "✗ $var (缺失)"
                all_found=false
            fi
        done

        if [ "$all_found" = true ]; then
            print_success "所有必要环境变量都已定义"
        fi
    fi
}

# 显示配置摘要
show_summary() {
    print_info ""
    print_info "================== 配置摘要 =================="
    print_info ""
    print_info "服务列表:"
    print_info "  - api: FastAPI 后端服务 (端口: 8000)"
    print_info "  - worker: Celery Worker (异步任务)"
    print_info "  - scheduler: Celery Beat (定时任务)"
    print_info "  - db: PostgreSQL + pgvector (端口: 5432)"
    print_info "  - redis: Redis 缓存和消息队列 (端口: 6379)"
    print_info "  - minio: 对象存储 (端口: 9000, 9001)"
    print_info "  - nginx: 反向代理 (端口: 80)"
    print_info ""
    print_info "数据卷:"
    print_info "  - postgres_data: PostgreSQL 数据"
    print_info "  - redis_data: Redis 数据"
    print_info "  - minio_data: MinIO 数据"
    print_info ""
    print_info "网络:"
    print_info "  - agenthire-network (子网: 172.20.0.0/16)"
    print_info ""
    print_info "常用命令:"
    print_info "  docker-compose up -d          # 启动所有服务"
    print_info "  docker-compose logs -f        # 查看日志"
    print_info "  docker-compose ps             # 查看服务状态"
    print_info "  docker-compose down           # 停止服务"
    print_info "  docker-compose down -v        # 停止并删除数据卷"
    print_info ""
}

# 主函数
main() {
    echo "=========================================="
    echo "AgentHire Docker 配置验证"
    echo "=========================================="
    echo ""

    check_files
    validate_compose
    validate_dockerfile
    check_env_config
    show_summary

    print_success "验证完成！"
}

main "$@"
