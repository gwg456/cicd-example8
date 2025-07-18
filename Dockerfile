FROM registry.cn-beijing.aliyuncs.com/moseeker/python:3.12-slim

WORKDIR /app

# 安装Docker CLI
RUN apt-get update && \
    apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://mirrors.aliyun.com/docker-ce/linux/debian $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y docker-ce-cli && \
    apt-get clean && \
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
