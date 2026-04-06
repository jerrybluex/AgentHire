#!/bin/bash
# AgentHire 项目启动脚本
# 用法: ./start.sh [环境]
# 示例: ./start.sh dev    # 启动开发环境
#       ./start.sh prod   # 启动生产环境预览

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

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

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    # 检查 Docker 是否运行
    if ! docker info &> /dev/null; then
        print_error "Docker 守护进程未运行，请启动 Docker"
        exit 1
    fi

    print_success "Docker 环境检查通过"
}

# 检查环境变量文件
check_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning ".env 文件不存在，从 .env.example 复制"
            cp .env.example .env
            print_warning "请编辑 .env 文件，设置必要的配置（如 API 密钥）"
        else
            print_error ".env.example 文件也不存在"
            exit 1
        fi
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p devops/nginx/logs
    mkdir -p devops/nginx/ssl
    mkdir -p logs
    print_success "目录创建完成"
}

# 启动开发环境
start_dev() {
    print_info "启动开发环境..."
    check_env
    create_directories

    # 构建并启动服务
    print_info "构建并启动服务..."
    docker-compose up --build -d

    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    print_info "检查服务状态..."
    docker-compose ps

    print_success "开发环境启动完成！"
    echo ""
    echo "服务访问地址："
    echo "  - API 文档: http://localhost/docs"
    echo "  - API 端点: http://localhost/api"
    echo "  - MinIO 控制台: http://localhost:9001"
    echo ""
    echo "常用命令："
    echo "  - 查看日志: docker-compose logs -f"
    echo "  - 停止服务: docker-compose down"
    echo "  - 重启服务: docker-compose restart"
}

# 启动生产环境预览
start_prod() {
    print_info "启动生产环境预览..."
    print_warning "这是生产环境的本地预览，实际生产部署请使用 Kubernetes"

    check_env
    create_directories

    # 检查 SSL 证书
    if [ ! -f "devops/nginx/ssl/cert.pem" ] || [ ! -f "devops/nginx/ssl/key.pem" ]; then
        print_warning "SSL 证书不存在，生成自签名证书..."
        mkdir -p devops/nginx/ssl
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout devops/nginx/ssl/key.pem \
            -out devops/nginx/ssl/cert.pem \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=AgentHire/CN=localhost"
        print_success "自签名证书生成完成"
    fi

    # 构建并启动服务
    print_info "构建并启动生产环境服务..."
    docker-compose -f docker-compose.prod.yml up --build -d

    sleep 10
    docker-compose -f docker-compose.prod.yml ps

    print_success "生产环境预览启动完成！"
    echo ""
    echo "服务访问地址："
    echo "  - API 文档: https://localhost/docs"
    echo "  - Flower 监控: https://localhost/flower"
}

# 停止服务
stop_services() {
    print_info "停止服务..."
    docker-compose down
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    print_success "服务已停止"
}

# 查看日志
show_logs() {
    local service=$1
    if [ -n "$service" ]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
}

# 重置环境（删除数据卷）
reset_env() {
    print_warning "这将删除所有数据卷，包括数据库数据！"
    read -p "确定要继续吗？(yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        print_info "停止服务并删除数据卷..."
        docker-compose down -v
        docker-compose -f docker-compose.prod.yml down -v 2>/dev/null || true
        docker volume prune -f
        print_success "环境已重置"
    else
        print_info "操作已取消"
    fi
}

# 显示帮助信息
show_help() {
    echo "AgentHire 项目启动脚本"
    echo ""
    echo "用法: $0 [命令] [参数]"
    echo ""
    echo "命令:"
    echo "  dev         启动开发环境"
    echo "  prod        启动生产环境预览"
    echo "  stop        停止所有服务"
    echo "  logs [服务]  查看日志（可指定服务名）"
    echo "  reset       重置环境（删除所有数据）"
    echo "  help        显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev              # 启动开发环境"
    echo "  $0 logs api         # 查看 API 服务日志"
    echo "  $0 logs             # 查看所有日志"
}

# 主函数
main() {
    local command=${1:-dev}

    case "$command" in
        dev)
            check_docker
            start_dev
            ;;
        prod)
            check_docker
            start_prod
            ;;
        stop)
            stop_services
            ;;
        logs)
            show_logs "$2"
            ;;
        reset)
            reset_env
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
