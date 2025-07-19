# Docker镜像加速器配置指南

在中国大陆地区，由于网络原因，直接从Docker Hub拉取镜像可能会很慢或失败。以下是几种常用的加速器配置方法：

## 方法1: 配置Docker镜像加速器（推荐）

### 阿里云镜像加速器
1. 登录阿里云控制台：https://cr.console.aliyun.com/
2. 在左侧导航栏选择"镜像加速器"
3. 获取您的专属加速器地址
4. 配置Docker：

```bash
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": ["https://你的加速器地址.mirror.aliyuncs.com"]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

### 其他镜像加速器

```bash
# 网易云镜像加速器
{
  "registry-mirrors": ["http://hub-mirror.c.163.com"]
}

# 腾讯云镜像加速器
{
  "registry-mirrors": ["https://mirror.ccs.tencentyun.com"]
}

# 中科大镜像加速器
{
  "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn"]
}

# 清华大学镜像加速器
{
  "registry-mirrors": ["https://mirrors.tuna.tsinghua.edu.cn"]
}
```

## 方法2: 直接使用镜像仓库

如果配置镜像加速器不可行，可以直接修改Dockerfile中的FROM指令：

```dockerfile
# 原始
FROM python:3.12-slim

# 替换为网易云镜像
FROM hub.c.163.com/library/python:3.12-slim

# 或DaoCloud镜像
FROM daocloud.io/library/python:3.12-slim
```

## 验证配置

配置完成后，运行以下命令验证：

```bash
docker info | grep "Registry Mirrors"
```

应该显示您配置的镜像加速器地址。

## 常见问题

1. **配置后仍然很慢**：尝试更换其他镜像加速器
2. **权限错误**：检查Docker daemon是否有权限访问配置文件
3. **网络问题**：确认网络连接正常，可以访问镜像仓库

## 本项目的优化

本项目已经进行了以下优化：
- 使用清华大学的apt源和pip源
- 提供了镜像替换的注释说明
- 支持通过环境变量配置镜像源