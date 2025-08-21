# 多阶段构建：构建阶段
FROM python:3.12-slim as builder

# 设置构建时的工作目录
WORKDIR /build

# 配置国内镜像源以加速构建
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制pip配置
COPY pip.conf /etc/pip.conf

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt

# 运行阶段
FROM python:3.12-slim as runtime

# 安全标签
LABEL maintainer="your.email@example.com" \
      version="1.0.0" \
      description="Prefect CI/CD Example Application" \
      security.scan="enabled"

# 创建非root用户
RUN groupadd -r prefect && useradd -r -g prefect -u 1000 prefect

# 设置工作目录
WORKDIR /app

# 配置国内镜像源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码（使用.dockerignore过滤）
COPY --chown=prefect:prefect . .

# 设置环境变量（不包含敏感信息）
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PREFECT_LOGGING_LEVEL=INFO \
    PREFECT_API_RESPONSE_TIMEOUT=300 \
    PREFECT_API_REQUEST_TIMEOUT=300

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# 切换到非root用户
USER prefect

# 暴露端口（如果需要）
# EXPOSE 8080

# 设置入口点
ENTRYPOINT ["python"]
CMD ["flow.py"]