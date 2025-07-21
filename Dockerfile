FROM python:3.12-slim

WORKDIR /app

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

COPY pip.conf /etc/pip.conf

COPY requirements.txt .
RUN pip install --upgrade pip --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

ARG PREFECT_API_URL
ARG IMAGE_REPO
ARG IMAGE_TAG
ARG WORK_POOL_NAME=my-docker-pool2

ENV PREFECT_API_URL=${PREFECT_API_URL} \
    IMAGE_REPO=${IMAGE_REPO} \
    IMAGE_TAG=${IMAGE_TAG} \
    WORK_POOL_NAME=${WORK_POOL_NAME} \
    PYTHONUNBUFFERED=1 \
    PREFECT_LOGGING_LEVEL=INFO \
    PYTHONPATH=/app

RUN useradd -m -u 1000 prefect && chown -R prefect:prefect /app
USER prefect

CMD ["python", "flow.py"]