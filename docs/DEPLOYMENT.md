# 📦 Deployment Guide

## Prerequisites

### System Requirements
- Python 3.12+
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

### Required Services
- Prefect Server or Cloud account
- PostgreSQL 14+ (optional)
- Redis 7+ (optional)

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd prefect-cicd
```

### 2. Environment Setup
```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Local Development
```bash
# Start services with Docker Compose
docker-compose up -d

# Run application
python flow.py
```

## Production Deployment

### Docker Deployment

#### Build Image
```bash
# Production build
docker build -f Dockerfile.production -t prefect-cicd:production .

# Standard build
docker build -t prefect-cicd:latest .
```

#### Run Container
```bash
docker run -d \
  --name prefect-app \
  -e PREFECT_API_URL=$PREFECT_API_URL \
  -e WORK_POOL_NAME=$WORK_POOL_NAME \
  -e ENVIRONMENT=production \
  -e JWT_SECRET_KEY=$JWT_SECRET_KEY \
  -p 8000:8000 \
  prefect-cicd:production
```

### Docker Compose Deployment

#### Development Environment
```bash
docker-compose up -d
```

#### Production Environment
```bash
docker-compose -f docker-compose.production.yml up -d
```

### Kubernetes Deployment

#### Create Namespace
```bash
kubectl create namespace prefect-cicd
```

#### Apply Configurations
```bash
# ConfigMap
kubectl apply -f k8s/configmap.yaml

# Secrets
kubectl create secret generic prefect-secrets \
  --from-literal=jwt-secret=$JWT_SECRET_KEY \
  --from-literal=prefect-api-key=$PREFECT_API_KEY \
  -n prefect-cicd

# Deployment
kubectl apply -f k8s/deployment.yaml

# Service
kubectl apply -f k8s/service.yaml

# Ingress
kubectl apply -f k8s/ingress.yaml
```

#### Helm Deployment
```bash
# Add Helm repository
helm repo add prefect-cicd https://charts.example.com
helm repo update

# Install chart
helm install prefect-cicd prefect-cicd/app \
  --namespace prefect-cicd \
  --values values.yaml
```

## CI/CD Pipeline

### GitHub Actions

The project includes automated CI/CD with GitHub Actions:

1. **On Pull Request**: Run tests and linting
2. **On Main Push**: Build, test, and deploy

#### Required Secrets
Configure these in GitHub repository settings:
- `PREFECT_API_URL`: Prefect server URL
- `PREFECT_API_KEY`: API authentication key
- `DOCKER_REGISTRY_PASSWORD`: Registry credentials

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  script:
    - pip install -r requirements.txt
    - pytest tests/

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - docker run --rm \
        -e DEPLOY_MODE=true \
        $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main
```

## Configuration

### Environment Variables

#### Required
- `PREFECT_API_URL`: Prefect API endpoint
- `WORK_POOL_NAME`: Prefect work pool name
- `IMAGE_REPO`: Docker image repository

#### Optional
- `ENVIRONMENT`: Environment name (development/staging/production)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `DEPLOY_MODE`: Enable deployment mode (true/false)
- `JWT_SECRET_KEY`: JWT signing key (required in production)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

### Work Pool Setup

#### Create Docker Work Pool
```bash
prefect work-pool create my-docker-pool --type docker
```

#### Configure Work Pool
```bash
prefect work-pool update my-docker-pool \
  --base-job-template '{
    "job_configuration": {
      "image": "{{ image }}",
      "pull_policy": "Always"
    }
  }'
```

#### Start Worker
```bash
prefect worker start --pool my-docker-pool
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'prefect-app'
    static_configs:
      - targets: ['app:8000']
```

### Grafana Dashboard

1. Access Grafana: http://localhost:3000
2. Default credentials: admin/admin
3. Import dashboard from `monitoring/grafana/dashboards/`

### Health Checks

#### Endpoints
- `/health`: Comprehensive health check
- `/health/live`: Kubernetes liveness probe
- `/health/ready`: Kubernetes readiness probe
- `/metrics`: Prometheus metrics

#### Example Health Check
```bash
curl http://localhost:8000/health
```

## Scaling

### Horizontal Scaling

#### Docker Swarm
```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.production.yml prefect-stack

# Scale service
docker service scale prefect-stack_app=5
```

#### Kubernetes
```bash
# Manual scaling
kubectl scale deployment prefect-app --replicas=5 -n prefect-cicd

# Auto-scaling
kubectl autoscale deployment prefect-app \
  --min=2 --max=10 --cpu-percent=70 \
  -n prefect-cicd
```

### Load Balancing

#### Nginx Configuration
```nginx
upstream prefect_backend {
    least_conn;
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://prefect_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

#### 1. Prefect API Connection Failed
```bash
# Check connectivity
curl -v $PREFECT_API_URL/health

# Verify environment variable
echo $PREFECT_API_URL

# Check network
docker network ls
docker network inspect bridge
```

#### 2. Work Pool Not Found
```bash
# List work pools
prefect work-pool ls

# Create if missing
prefect work-pool create my-docker-pool --type docker
```

#### 3. Docker Build Failures
```bash
# Clean build cache
docker builder prune -a

# Build with no cache
docker build --no-cache -t prefect-cicd .

# Check disk space
df -h
```

#### 4. Container Crashes
```bash
# Check logs
docker logs prefect-app

# Inspect container
docker inspect prefect-app

# Debug shell
docker run -it --entrypoint /bin/bash prefect-cicd
```

### Logs

#### Application Logs
```bash
# Docker logs
docker logs -f prefect-app

# Kubernetes logs
kubectl logs -f deployment/prefect-app -n prefect-cicd

# Log aggregation
docker-compose logs -f app
```

#### Structured Log Query
```bash
# Search for errors
docker logs prefect-app 2>&1 | jq 'select(.level=="ERROR")'

# Filter by correlation ID
docker logs prefect-app 2>&1 | jq 'select(.correlation_id=="abc123")'
```

## Rollback Procedures

### Docker
```bash
# Tag current version
docker tag prefect-cicd:latest prefect-cicd:rollback

# Deploy previous version
docker stop prefect-app
docker run -d --name prefect-app prefect-cicd:v1.0.0
```

### Kubernetes
```bash
# View rollout history
kubectl rollout history deployment/prefect-app -n prefect-cicd

# Rollback to previous version
kubectl rollout undo deployment/prefect-app -n prefect-cicd

# Rollback to specific revision
kubectl rollout undo deployment/prefect-app --to-revision=2 -n prefect-cicd
```

## Security Considerations

### Secret Management
- Use environment variables for secrets
- Never commit secrets to version control
- Rotate secrets regularly
- Use secret management tools (Vault, AWS Secrets Manager)

### Network Security
- Use TLS/SSL for all connections
- Implement network policies in Kubernetes
- Use private networks for internal communication
- Regular security scanning

### Container Security
```bash
# Scan image for vulnerabilities
docker scan prefect-cicd:latest

# Run as non-root user
docker run --user 1000:1000 prefect-cicd

# Read-only filesystem
docker run --read-only prefect-cicd
```

## Backup and Recovery

### Database Backup
```bash
# PostgreSQL backup
pg_dump -h localhost -U prefect -d prefect > backup.sql

# Restore
psql -h localhost -U prefect -d prefect < backup.sql
```

### Configuration Backup
```bash
# Export Prefect configuration
prefect config view > prefect-config.yaml

# Backup Docker volumes
docker run --rm -v prefect-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/prefect-data.tar.gz /data
```