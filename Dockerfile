FROM registry.cn-beijing.aliyuncs.com/moseeker/python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

COPY flow.py .

ENV PYTHONUNBUFFERED=1
ENV PREFECT_LOGGING_LEVEL=INFO

CMD ["python", "flow.py"]
