# AgentHire 后端 Dockerfile
# 支持多阶段构建：development 和 production

# ==========================================
# 基础镜像 - 用于开发和生产
# ==========================================
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    # 简历解析相关依赖
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    poppler-utils \
    libmagic1 \
    # 其他工具
    wget \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# ==========================================
# 开发阶段
# ==========================================
FROM base as development

# 复制依赖文件
COPY pyproject.toml poetry.lock* README.md ./

# 安装所有依赖（包括开发依赖）
RUN pip install -e ".[dev]"

# 复制应用代码（开发环境会通过 volume 挂载覆盖）
COPY . .

# 安装应用
RUN pip install -e .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 默认命令（开发环境使用热重载）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ==========================================
# 构建阶段 - 用于生产
# ==========================================
FROM base as builder

# 复制依赖文件
COPY pyproject.toml poetry.lock* README.md ./

# 安装生产依赖
RUN pip install -e .

# 复制应用代码
COPY . .

# 安装应用
RUN pip install -e .

# ==========================================
# 生产阶段
# ==========================================
FROM python:3.11-slim as production

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    APP_HOME=/app \
    PORT=8000

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    # 简历解析相关运行时依赖
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-chi-tra \
    poppler-utils \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR ${APP_HOME}

# 从构建阶段复制虚拟环境
COPY --from=builder /app/.venv /app/.venv

# 复制应用代码
COPY --from=builder /app/app ./app
COPY --from=builder /app/pyproject.toml ./

# 设置虚拟环境路径
ENV PATH="/app/.venv/bin:$PATH"

# 创建必要的目录并设置权限
RUN mkdir -p /tmp/prometheus /var/log/agenthire && \
    chown -R appuser:appuser ${APP_HOME} /tmp/prometheus /var/log/agenthire

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE ${PORT}

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 使用 gunicorn 作为生产服务器
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "--capture-output", "--enable-stdio-inheritance", "app.main:app"]
