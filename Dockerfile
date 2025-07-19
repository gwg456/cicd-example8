FROM registry.cn-hangzhou.aliyuncs.com/library/python:3.12-slim

WORKDIR /app

# 更换apt源为阿里云
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# 配置pip使用阿里云源
COPY pip.conf /etc/pip.conf

# 复制并安装Python依赖
COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY config.py flow.py ./

# 设置环境变量（构建时可以覆盖）
ARG PREFECT_API_URL
ARG IMAGE_REPO
ARG IMAGE_TAG
ARG WORK_POOL_NAME=my-docker-pool2

# 将构建参数转换为环境变量
ENV PREFECT_API_URL=${PREFECT_API_URL} \
    IMAGE_REPO=${IMAGE_REPO} \
    IMAGE_TAG=${IMAGE_TAG} \
    WORK_POOL_NAME=${WORK_POOL_NAME} \
    PYTHONUNBUFFERED=1 \
    PREFECT_LOGGING_LEVEL=INFO

# 创建非root用户（安全最佳实践）
RUN useradd -m -u 1000 prefect && chown -R prefect:prefect /app
USER prefect

CMD ["python", "flow.py"]
