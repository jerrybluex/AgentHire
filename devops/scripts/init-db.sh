#!/bin/bash
# AgentHire 数据库初始化脚本
# 用于开发环境数据库的初始化和迁移

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
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

# 加载环境变量
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    print_warning ".env 文件不存在，使用默认配置"
fi

# 数据库连接参数
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${POSTGRES_DB:-agenthire}
DB_USER=${POSTGRES_USER:-agenthire}
DB_PASSWORD=${POSTGRES_PASSWORD:-agenthire123}

print_info "数据库配置:"
print_info "  Host: $DB_HOST"
print_info "  Port: $DB_PORT"
print_info "  Database: $DB_NAME"
print_info "  User: $DB_USER"

# 等待数据库就绪
wait_for_db() {
    print_info "等待数据库就绪..."
    local retries=30
    local wait_time=2

    for i in $(seq 1 $retries); do
        if PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
            print_success "数据库已就绪"
            return 0
        fi
        print_info "等待数据库... ($i/$retries)"
        sleep $wait_time
    done

    print_error "数据库连接超时"
    return 1
}

# 检查 pgvector 扩展
check_pgvector() {
    print_info "检查 pgvector 扩展..."
    local result=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT * FROM pg_extension WHERE extname = 'vector';" 2>/dev/null)

    if [ -n "$result" ]; then
        print_success "pgvector 扩展已安装"
        return 0
    else
        print_warning "pgvector 扩展未安装，尝试安装..."
        PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null
        if [ $? -eq 0 ]; then
            print_success "pgvector 扩展安装成功"
            return 0
        else
            print_error "pgvector 扩展安装失败"
            return 1
        fi
    fi
}

# 运行数据库迁移
run_migrations() {
    print_info "运行数据库迁移..."

    # 检查是否在 Docker 环境中
    if [ -f "/.dockerenv" ]; then
        # 在容器内运行迁移
        cd /app
        alembic upgrade head
    else
        # 在宿主机上通过 docker-compose 运行迁移
        docker-compose exec -T api alembic upgrade head
    fi

    if [ $? -eq 0 ]; then
        print_success "数据库迁移完成"
        return 0
    else
        print_error "数据库迁移失败"
        return 1
    fi
}

# 初始化基础数据
seed_data() {
    print_info "初始化基础数据..."

    # 这里可以添加基础数据的初始化逻辑
    # 例如：创建默认管理员账户、基础配置等

    print_info "基础数据初始化完成"
}

# 显示数据库状态
show_status() {
    print_info "数据库状态:"
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
\dt
\dx
EOF
}

# 重置数据库（危险操作）
reset_db() {
    print_warning "警告：这将删除所有数据！"
    read -p "确定要重置数据库吗？(yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "操作已取消"
        return 0
    fi

    print_info "重置数据库..."

    # 删除并重新创建数据库
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

    print_success "数据库已重置"

    # 重新初始化
    init_db
}

# 主初始化流程
init_db() {
    print_info "开始数据库初始化..."

    # 等待数据库就绪
    wait_for_db || exit 1

    # 检查 pgvector 扩展
    check_pgvector || exit 1

    # 运行迁移
    run_migrations || exit 1

    # 初始化基础数据
    seed_data

    # 显示状态
    show_status

    print_success "数据库初始化完成！"
}

# 显示帮助
show_help() {
    echo "AgentHire 数据库初始化脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  init    初始化数据库（默认）"
    echo "  reset   重置数据库（删除所有数据）"
    echo "  status  显示数据库状态"
    echo "  wait    仅等待数据库就绪"
    echo "  help    显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 init     # 初始化数据库"
    echo "  $0 reset    # 重置数据库"
    echo "  $0 status   # 查看数据库状态"
}

# 主函数
main() {
    local command=${1:-init}

    case "$command" in
        init)
            init_db
            ;;
        reset)
            reset_db
            ;;
        status)
            wait_for_db && show_status
            ;;
        wait)
            wait_for_db
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
