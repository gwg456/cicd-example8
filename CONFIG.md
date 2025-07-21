# 配置文档

## 环境变量配置

### Prefect 配置
- `PREFECT_API_URL`: Prefect 服务器 API 地址 (默认: http://localhost:4200/api)
- `WORK_POOL_NAME`: Prefect 工作池名称 (默认: my-docker-pool2)

### Docker 配置
- `IMAGE_REPO`: Docker 镜像仓库地址 (默认: ghcr.io/samples28/cicd-example)
- `IMAGE_TAG`: Docker 镜像标签 (可选)

### 应用配置
- `LOG_LEVEL`: 日志级别 (默认: INFO)
- `ENVIRONMENT`: 运行环境 (默认: development)
- `DEPLOY_MODE`: 是否为部署模式 (默认: false)

### 调度配置
- `SCHEDULE_INTERVAL`: 定时任务执行间隔，单位秒 (默认: 3600)

### 超时配置
- `PREFECT_API_TIMEOUT`: Prefect API 请求超时时间，单位秒 (默认: 300)
- `DEPLOYMENT_TIMEOUT`: 部署操作超时时间，单位秒 (默认: 60)

## 配置示例

参考 `.env.example` 文件获取完整的配置示例。

## 配置验证

使用以下命令验证配置：

```bash
make validate
```

或者直接运行：

```bash
python -c "from config import config; missing = config.validate_required_settings(); print('配置验证:', '✅ 通过' if not missing else f'❌ 缺少: {missing}')"
```