# 使用多阶段构建优化镜像大小
FROM python:3.12-slim as builder

# 设置构建时的工作目录
WORKDIR /build

# 使用清华大学镜像源加速包下载
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖（仅在构建阶段需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制pip配置
COPY pip.conf /etc/pip.conf

# 复制依赖文件并安装Python包
COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt \
    && pip list > /build/installed_packages.txt

# 运行时阶段
FROM python:3.12-slim as runtime

# 设置标签
LABEL maintainer="prefect-cicd-team" \
      version="1.0" \
      description="Prefect CI/CD Example Application"

# 使用清华大学镜像源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 创建非root用户
RUN useradd -m -u 1000 -s /bin/bash prefect

# 设置工作目录
WORKDIR /app

# 从构建阶段复制Python包
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY --chown=prefect:prefect . .

# 设置构建参数
ARG PREFECT_API_URL
ARG IMAGE_REPO
ARG IMAGE_TAG
ARG WORK_POOL_NAME=my-docker-pool2

# 设置环境变量
ENV PREFECT_API_URL=${PREFECT_API_URL} \
    IMAGE_REPO=${IMAGE_REPO} \
    IMAGE_TAG=${IMAGE_TAG} \
    WORK_POOL_NAME=${WORK_POOL_NAME} \
    PYTHONUNBUFFERED=1 \
    PREFECT_LOGGING_LEVEL=INFO \
    PYTHONPATH=/app \
    PATH="/home/prefect/.local/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 切换到非root用户
USER prefect

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from config import config; print('健康检查通过')" || exit 1

# 设置默认命令
CMD ["python", "flow.py"]