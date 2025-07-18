FROM registry.cn-beijing.aliyuncs.com/moseeker/python:3.12-slim

WORKDIR /app

# 完全重置apt源配置，确保只使用阿里云源
RUN set -eux; \
    # 备份原始源配置（以防万一）
    if [ -f /etc/apt/sources.list ]; then \
        mv /etc/apt/sources.list /etc/apt/sources.list.bak; \
    fi; \
    # 删除所有其他源配置
    rm -rf /etc/apt/sources.list.d/*; \
    # 创建新的阿里云源配置
    echo "deb https://mirrors.aliyun.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list; \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list; \
    # 配置apt优先使用阿里云源
    echo 'Acquire::http::Timeout "120";' > /etc/apt/apt.conf.d/99timeout; \
    echo 'Acquire::Retries "3";' >> /etc/apt/apt.conf.d/99timeout; \
    # 禁用官方源
    echo 'Acquire::http::Proxy::deb.debian.org "DIRECT";' > /etc/apt/apt.conf.d/99proxy; \
    echo 'Acquire::http::Proxy::security.debian.org "DIRECT";' >> /etc/apt/apt.conf.d/99proxy; \
    # 更新包索引
    apt-get clean; \
    apt-get update -o Acquire::Check-Valid-Until=false; \
    # 安装必要的包
    apt-get install -y --no-install-recommends \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release; \
    # 添加阿里云Docker源
    mkdir -p /etc/apt/keyrings; \
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list; \
    # 再次更新包索引并安装Docker CLI
    apt-get update -o Acquire::Check-Valid-Until=false; \
    apt-get install -y --no-install-recommends docker-ce-cli; \
    # 清理
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

COPY flow.py .

# 设置环境变量（构建时可以覆盖）
ARG PREFECT_API_URL
ARG IMAGE_REPO
ARG IMAGE_TAG
ARG WORK_POOL_NAME=my-docker-pool2

# 将构建参数转换为环境变量
ENV PREFECT_API_URL=${PREFECT_API_URL}
ENV IMAGE_REPO=${IMAGE_REPO}
ENV IMAGE_TAG=${IMAGE_TAG}
ENV WORK_POOL_NAME=${WORK_POOL_NAME}
ENV PYTHONUNBUFFERED=1
ENV PREFECT_LOGGING_LEVEL=INFO

CMD ["python", "flow.py"]
