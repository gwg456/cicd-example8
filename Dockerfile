FROM registry.cn-beijing.aliyuncs.com/moseeker/python:3.12-slim
ENV PREFECT_API_URL=http://172.31.0.55:4200/api
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flow.py .

ENV PYTHONUNBUFFERED=1
ENV PREFECT_LOGGING_LEVEL=INFO

CMD ["python", "flow.py"]
