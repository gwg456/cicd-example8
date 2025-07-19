# Docker Hub访问配置指南

在中国大陆地区，由于网络原因，直接从Docker Hub拉取镜像可能会很慢或失败。以下是通过配置 `/etc/hosts` 文件解决访问问题的方法：

## 方法1: 自动配置hosts（推荐）

### 使用自动脚本
```bash
# 运行自动配置脚本
sudo chmod +x scripts/update-docker-hosts.sh
sudo ./scripts/update-docker-hosts.sh
```

### 使用预设配置文件
```bash
# 直接使用预设的hosts配置
sudo cat docker-hosts.txt >> /etc/hosts
sudo systemctl restart docker
```

## 方法2: 手动配置hosts

### 编辑hosts文件
```bash
sudo vim /etc/hosts
```

### 添加以下内容到文件末尾：
```
# Docker Hub mirror configuration
52.4.71.198     registry-1.docker.io
54.85.56.253    auth.docker.io  
52.72.232.213   production.cloudflare.docker.com
52.1.38.175     index.docker.io
52.4.71.198     registry.docker.io
18.232.227.119  docker.io
3.211.234.87    hub.docker.com
# End Docker Hub configuration
```

### 重启Docker服务
```bash
sudo systemctl restart docker
```

## 验证配置

配置完成后，运行以下命令验证：

```bash
# 测试域名解析
nslookup registry-1.docker.io

# 测试连接
ping -c 3 registry-1.docker.io

# 测试Docker拉取
docker pull hello-world
```

## 获取最新IP地址

Docker Hub的IP地址可能会变化，可以使用以下方法获取最新IP：

```bash
# 使用不同的DNS服务器查询
nslookup registry-1.docker.io 8.8.8.8
nslookup registry-1.docker.io 1.1.1.1
nslookup registry-1.docker.io 223.5.5.5

# 或使用dig命令
dig @8.8.8.8 registry-1.docker.io
```

## GitHub Actions中的使用

项目的GitHub Actions工作流会自动：

1. 配置宿主机的 `/etc/hosts`
2. 将hosts配置传递给Docker构建过程
3. 在运行容器时也传递hosts配置

这确保了整个CI/CD流程都能正常访问Docker Hub。

## 常见问题

1. **配置后仍然很慢**：
   - 检查IP地址是否最新
   - 尝试更新为最新的IP地址
   - 确认网络连接正常

2. **权限错误**：
   - 确保使用sudo权限编辑/etc/hosts
   - 检查文件权限：`ls -la /etc/hosts`

3. **Docker构建失败**：
   - 重启Docker服务：`sudo systemctl restart docker`
   - 清理Docker缓存：`docker system prune`
   - 检查域名解析：`nslookup registry-1.docker.io`

## 本项目的优化

本项目已经进行了以下优化：
- 提供预设的hosts配置文件
- 自动提取和应用hosts配置的脚本
- GitHub Actions自动配置hosts
- 构建时传递hosts配置给容器