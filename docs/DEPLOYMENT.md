# 部署指南 / Deployment Guide

本文档提供教育辅导系统的部署指南，涵盖开发、测试和生产环境。

This document provides deployment instructions for the Education Tutoring System, covering development, testing, and production environments.

## 目录 / Table of Contents

- [部署架构](#部署架构--deployment-architecture)
- [前置要求](#前置要求--prerequisites)
- [开发环境部署](#开发环境部署--development-deployment)
- [测试环境部署](#测试环境部署--testing-deployment)
- [生产环境部署](#生产环境部署--production-deployment)
- [Docker 部署](#docker-部署--docker-deployment)
- [云平台部署](#云平台部署--cloud-deployment)
- [监控和维护](#监控和维护--monitoring-and-maintenance)
- [故障排除](#故障排除--troubleshooting)

## 部署架构 / Deployment Architecture

### 系统组件 / System Components

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面 / User Interface             │
│                    (CLI / Web API)                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              教育辅导系统 / Tutoring System              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Coordinator  │  │Course Advisor│  │Learning Plan │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────┐
│ vLLM Server  │ │   SQLite  │ │ MCP Tools  │
│              │ │  Database │ │ (Playwright│
│              │ │           │ │ Web Search)│
└──────────────┘ └───────────┘ └────────────┘
```

### 部署模式 / Deployment Modes

1. **单机部署 / Single Machine**: 所有组件在一台服务器上
2. **分布式部署 / Distributed**: vLLM 服务器独立部署
3. **容器化部署 / Containerized**: 使用 Docker/Kubernetes
4. **云平台部署 / Cloud**: AWS/Azure/GCP

## 前置要求 / Prerequisites

### 硬件要求 / Hardware Requirements

#### 开发环境 / Development
- CPU: 4 核心 / 4 cores
- 内存 / RAM: 8 GB
- 磁盘 / Disk: 20 GB

#### 生产环境 / Production
- CPU: 8+ 核心 / 8+ cores
- 内存 / RAM: 16+ GB
- 磁盘 / Disk: 100+ GB (取决于数据量 / depends on data volume)

### 软件要求 / Software Requirements

- **操作系统 / OS**: Linux (Ubuntu 20.04+), macOS, Windows
- **Python**: 3.10 或更高 / 3.10 or higher
- **uv**: 最新版本 / Latest version
- **vLLM 服务器 / vLLM Server**: 独立部署或访问权限 / Deployed separately or access credentials
- **数据库 / Database**: SQLite (内置 / built-in)

### 网络要求 / Network Requirements

- 访问 vLLM 服务器 / Access to vLLM server
- 访问极客时间网站 / Access to GeekTime website
- 访问搜索引擎 / Access to search engines
- 端口 / Ports: 8000 (可选，用于 API / optional, for API)

## 开发环境部署 / Development Deployment

### 快速开始 / Quick Start

```bash
# 1. 克隆仓库 / Clone repository
git clone <repository-url>
cd education-tutoring-system

# 2. 安装 uv / Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 安装依赖 / Install dependencies
uv sync --extra dev

# 4. 配置系统 / Configure system
cp config/system_config.yaml config/system_config.dev.yaml
vim config/system_config.dev.yaml

# 5. 运行系统 / Run system
python main.py --config config/system_config.dev.yaml
```

### 开发配置 / Development Configuration

```yaml
# config/system_config.dev.yaml
vllm:
  api_base: "http://localhost:8000/v1"
  model_name: "your-dev-model"
  temperature: 0.7

system:
  database_path: "./data/dev_tutoring.db"
  max_loop_count: 10

logging:
  level: "DEBUG"
  file: "./logs/dev.log"

mcp:
  browser_headless: false  # 显示浏览器窗口以便调试
```

### 开发工具 / Development Tools

```bash
# 代码格式化 / Code formatting
uv run black src tests

# 代码检查 / Linting
uv run ruff check src tests

# 类型检查 / Type checking
uv run mypy src

# 运行测试 / Run tests
uv run pytest

# 生成覆盖率报告 / Generate coverage report
uv run pytest --cov=src --cov-report=html
```

## 测试环境部署 / Testing Deployment

### 部署步骤 / Deployment Steps

```bash
# 1. 准备服务器 / Prepare server
ssh user@test-server

# 2. 安装系统依赖 / Install system dependencies
sudo apt update
sudo apt install -y python3.10 python3.10-venv git

# 3. 克隆代码 / Clone code
git clone <repository-url>
cd education-tutoring-system

# 4. 安装 uv / Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 5. 安装依赖 / Install dependencies
uv sync

# 6. 配置系统 / Configure system
cp config/system_config.yaml config/system_config.test.yaml
vim config/system_config.test.yaml

# 7. 创建数据目录 / Create data directory
mkdir -p data logs

# 8. 运行测试 / Run tests
uv run pytest

# 9. 启动系统 / Start system
python main.py --config config/system_config.test.yaml
```

### 测试配置 / Testing Configuration

```yaml
# config/system_config.test.yaml
vllm:
  api_base: "http://test-vllm-server:8000/v1"
  model_name: "test-model"

system:
  database_path: "/var/lib/tutoring/test_tutoring.db"

logging:
  level: "INFO"
  file: "/var/log/tutoring/test.log"

mcp:
  browser_headless: true
```

## 生产环境部署 / Production Deployment

### 部署架构 / Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    负载均衡器 / Load Balancer            │
│                    (Nginx / HAProxy)                     │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────┐
│  Instance 1  │ │Instance 2 │ │ Instance 3 │
│              │ │           │ │            │
└──────────────┘ └───────────┘ └────────────┘
        │            │            │
        └────────────┼────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌─▼──────────┐
│ vLLM Cluster │ │  Database │ │   Redis    │
│              │ │  (SQLite/ │ │  (Cache)   │
│              │ │ PostgreSQL)│ │            │
└──────────────┘ └───────────┘ └────────────┘
```

### 部署步骤 / Deployment Steps

#### 1. 服务器准备 / Server Preparation

```bash
# 更新系统 / Update system
sudo apt update && sudo apt upgrade -y

# 安装依赖 / Install dependencies
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    git \
    nginx \
    supervisor \
    sqlite3

# 创建应用用户 / Create application user
sudo useradd -m -s /bin/bash tutoring
sudo su - tutoring
```

#### 2. 应用部署 / Application Deployment

```bash
# 克隆代码 / Clone code
cd /opt
sudo git clone <repository-url> tutoring-system
sudo chown -R tutoring:tutoring tutoring-system
cd tutoring-system

# 安装 uv / Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装依赖 / Install dependencies
uv sync

# 创建目录 / Create directories
sudo mkdir -p /var/lib/tutoring /var/log/tutoring
sudo chown tutoring:tutoring /var/lib/tutoring /var/log/tutoring
```

#### 3. 配置文件 / Configuration Files

```yaml
# /opt/tutoring-system/config/system_config.prod.yaml
vllm:
  api_base: "http://vllm-cluster:8000/v1"
  api_key: "${VLLM_API_KEY}"  # 从环境变量读取
  model_name: "production-model"
  temperature: 0.7
  max_tokens: 2000
  timeout: 60

system:
  database_path: "/var/lib/tutoring/tutoring_system.db"
  max_loop_count: 10
  enable_human_input: true
  session_timeout: 30

logging:
  level: "INFO"
  file: "/var/log/tutoring/system.log"
  max_file_size: 50
  backup_count: 10

mcp:
  browser_headless: true
  browser_timeout: 30000

web_search:
  enabled: true
  provider: "duckduckgo"
  max_results: 5
```

#### 4. Systemd 服务 / Systemd Service

```ini
# /etc/systemd/system/tutoring.service
[Unit]
Description=Education Tutoring System
After=network.target

[Service]
Type=simple
User=tutoring
Group=tutoring
WorkingDirectory=/opt/tutoring-system
Environment="PATH=/home/tutoring/.cargo/bin:/usr/local/bin:/usr/bin:/bin"
Environment="VLLM_API_KEY=your-api-key"
ExecStart=/home/tutoring/.cargo/bin/uv run python main.py --config config/system_config.prod.yaml
Restart=always
RestartSec=10

# 日志 / Logging
StandardOutput=append:/var/log/tutoring/stdout.log
StandardError=append:/var/log/tutoring/stderr.log

# 安全 / Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

启动服务 / Start service:

```bash
# 重载 systemd / Reload systemd
sudo systemctl daemon-reload

# 启动服务 / Start service
sudo systemctl start tutoring

# 设置开机自启 / Enable on boot
sudo systemctl enable tutoring

# 查看状态 / Check status
sudo systemctl status tutoring

# 查看日志 / View logs
sudo journalctl -u tutoring -f
```

#### 5. Nginx 反向代理 / Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/tutoring
upstream tutoring_backend {
    server 127.0.0.1:8000;
    # 如果有多个实例 / If multiple instances
    # server 127.0.0.1:8001;
    # server 127.0.0.1:8002;
}

server {
    listen 80;
    server_name tutoring.example.com;

    # 重定向到 HTTPS / Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tutoring.example.com;

    # SSL 证书 / SSL certificates
    ssl_certificate /etc/ssl/certs/tutoring.crt;
    ssl_certificate_key /etc/ssl/private/tutoring.key;

    # SSL 配置 / SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 日志 / Logs
    access_log /var/log/nginx/tutoring_access.log;
    error_log /var/log/nginx/tutoring_error.log;

    # 代理配置 / Proxy configuration
    location / {
        proxy_pass http://tutoring_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时配置 / Timeout configuration
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查 / Health check
    location /health {
        proxy_pass http://tutoring_backend/health;
    }
}
```

启用配置 / Enable configuration:

```bash
# 创建符号链接 / Create symbolic link
sudo ln -s /etc/nginx/sites-available/tutoring /etc/nginx/sites-enabled/

# 测试配置 / Test configuration
sudo nginx -t

# 重载 Nginx / Reload Nginx
sudo systemctl reload nginx
```

#### 6. 数据库备份 / Database Backup

```bash
# 创建备份脚本 / Create backup script
sudo vim /opt/tutoring-system/scripts/backup.sh
```

```bash
#!/bin/bash
# /opt/tutoring-system/scripts/backup.sh

BACKUP_DIR="/var/backups/tutoring"
DB_PATH="/var/lib/tutoring/tutoring_system.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/tutoring_$DATE.db"

# 创建备份目录 / Create backup directory
mkdir -p $BACKUP_DIR

# 备份数据库 / Backup database
sqlite3 $DB_PATH ".backup $BACKUP_FILE"

# 压缩备份 / Compress backup
gzip $BACKUP_FILE

# 删除 7 天前的备份 / Delete backups older than 7 days
find $BACKUP_DIR -name "tutoring_*.db.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

```bash
# 设置权限 / Set permissions
sudo chmod +x /opt/tutoring-system/scripts/backup.sh

# 添加到 crontab / Add to crontab
sudo crontab -e
```

```cron
# 每天凌晨 2 点备份 / Backup daily at 2 AM
0 2 * * * /opt/tutoring-system/scripts/backup.sh >> /var/log/tutoring/backup.log 2>&1
```

## Docker 部署 / Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.10-slim

# 设置工作目录 / Set working directory
WORKDIR /app

# 安装系统依赖 / Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv / Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:${PATH}"

# 复制项目文件 / Copy project files
COPY . .

# 安装依赖 / Install dependencies
RUN uv sync

# 创建数据目录 / Create data directories
RUN mkdir -p /app/data /app/logs

# 暴露端口 / Expose port
EXPOSE 8000

# 健康检查 / Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 启动命令 / Start command
CMD ["python", "main.py", "--config", "config/system_config.yaml"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  tutoring-system:
    build: .
    container_name: tutoring-system
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - VLLM_API_BASE=http://vllm-server:8000/v1
      - VLLM_API_KEY=${VLLM_API_KEY}
      - LOG_LEVEL=INFO
    depends_on:
      - vllm-server
    networks:
      - tutoring-network

  vllm-server:
    image: vllm/vllm-openai:latest
    container_name: vllm-server
    restart: unless-stopped
    ports:
      - "8001:8000"
    volumes:
      - ./models:/models
    environment:
      - MODEL_NAME=your-model
    networks:
      - tutoring-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

networks:
  tutoring-network:
    driver: bridge

volumes:
  data:
  logs:
```

### 部署命令 / Deployment Commands

```bash
# 构建镜像 / Build image
docker-compose build

# 启动服务 / Start services
docker-compose up -d

# 查看日志 / View logs
docker-compose logs -f tutoring-system

# 停止服务 / Stop services
docker-compose down

# 重启服务 / Restart services
docker-compose restart tutoring-system
```

## 云平台部署 / Cloud Deployment

### AWS 部署 / AWS Deployment

#### 使用 EC2 / Using EC2

```bash
# 1. 创建 EC2 实例 / Create EC2 instance
# - AMI: Ubuntu 20.04 LTS
# - Instance Type: t3.large (或更大 / or larger)
# - Storage: 100 GB

# 2. 配置安全组 / Configure security group
# - SSH (22): 你的 IP / Your IP
# - HTTP (80): 0.0.0.0/0
# - HTTPS (443): 0.0.0.0/0
# - Custom (8000): 内网 / Internal network

# 3. 连接到实例 / Connect to instance
ssh -i your-key.pem ubuntu@ec2-instance-ip

# 4. 按照生产环境部署步骤操作 / Follow production deployment steps
```

#### 使用 ECS / Using ECS

```yaml
# task-definition.json
{
  "family": "tutoring-system",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "tutoring-system",
      "image": "your-ecr-repo/tutoring-system:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "VLLM_API_BASE",
          "value": "http://vllm-service:8000/v1"
        }
      ],
      "secrets": [
        {
          "name": "VLLM_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:vllm-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/tutoring-system",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Azure 部署 / Azure Deployment

```bash
# 使用 Azure Container Instances / Using Azure Container Instances
az container create \
  --resource-group tutoring-rg \
  --name tutoring-system \
  --image your-acr.azurecr.io/tutoring-system:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    VLLM_API_BASE=http://vllm-service:8000/v1 \
  --secure-environment-variables \
    VLLM_API_KEY=your-api-key
```

### GCP 部署 / GCP Deployment

```bash
# 使用 Cloud Run / Using Cloud Run
gcloud run deploy tutoring-system \
  --image gcr.io/your-project/tutoring-system:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars VLLM_API_BASE=http://vllm-service:8000/v1 \
  --set-secrets VLLM_API_KEY=vllm-api-key:latest
```

## 监控和维护 / Monitoring and Maintenance

### 日志监控 / Log Monitoring

```bash
# 实时查看日志 / View logs in real-time
tail -f /var/log/tutoring/system.log

# 搜索错误 / Search for errors
grep ERROR /var/log/tutoring/system.log

# 分析日志 / Analyze logs
cat /var/log/tutoring/system.log | grep "LLM_CALL" | wc -l
```

### 性能监控 / Performance Monitoring

```bash
# 系统资源 / System resources
htop

# 磁盘使用 / Disk usage
df -h

# 数据库大小 / Database size
du -h /var/lib/tutoring/tutoring_system.db

# 进程状态 / Process status
ps aux | grep python
```

### 健康检查 / Health Checks

```bash
# 创建健康检查脚本 / Create health check script
cat > /opt/tutoring-system/scripts/health_check.sh << 'EOF'
#!/bin/bash

# 检查进程 / Check process
if ! pgrep -f "python main.py" > /dev/null; then
    echo "ERROR: Process not running"
    exit 1
fi

# 检查数据库 / Check database
if ! sqlite3 /var/lib/tutoring/tutoring_system.db "SELECT 1" > /dev/null 2>&1; then
    echo "ERROR: Database not accessible"
    exit 1
fi

# 检查日志 / Check logs
if ! tail -n 100 /var/log/tutoring/system.log | grep -q "ERROR"; then
    echo "OK: System healthy"
    exit 0
else
    echo "WARNING: Errors in logs"
    exit 1
fi
EOF

chmod +x /opt/tutoring-system/scripts/health_check.sh
```

### 自动重启 / Auto Restart

```bash
# 添加到 crontab / Add to crontab
*/5 * * * * /opt/tutoring-system/scripts/health_check.sh || systemctl restart tutoring
```

## 故障排除 / Troubleshooting

### 常见问题 / Common Issues

#### 1. 服务无法启动 / Service Won't Start

```bash
# 查看服务状态 / Check service status
sudo systemctl status tutoring

# 查看日志 / Check logs
sudo journalctl -u tutoring -n 100

# 检查配置 / Check configuration
python -c "from src.utils.config import load_config; load_config('config/system_config.prod.yaml')"
```

#### 2. 数据库锁定 / Database Locked

```bash
# 检查进程 / Check processes
lsof /var/lib/tutoring/tutoring_system.db

# 删除锁文件 / Remove lock files
rm -f /var/lib/tutoring/tutoring_system.db-wal
rm -f /var/lib/tutoring/tutoring_system.db-shm

# 重启服务 / Restart service
sudo systemctl restart tutoring
```

#### 3. 内存不足 / Out of Memory

```bash
# 检查内存使用 / Check memory usage
free -h

# 增加交换空间 / Increase swap space
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 优化配置 / Optimize configuration
# 减少 max_tokens 和 max_loop_count
```

#### 4. vLLM 连接失败 / vLLM Connection Failed

```bash
# 测试连接 / Test connection
curl http://vllm-server:8000/v1/models

# 检查网络 / Check network
ping vllm-server
telnet vllm-server 8000

# 检查防火墙 / Check firewall
sudo ufw status
```

### 紧急恢复 / Emergency Recovery

```bash
# 1. 停止服务 / Stop service
sudo systemctl stop tutoring

# 2. 备份当前数据 / Backup current data
cp /var/lib/tutoring/tutoring_system.db /var/backups/tutoring/emergency_backup.db

# 3. 恢复最近的备份 / Restore recent backup
gunzip -c /var/backups/tutoring/tutoring_YYYYMMDD_HHMMSS.db.gz > /var/lib/tutoring/tutoring_system.db

# 4. 重启服务 / Restart service
sudo systemctl start tutoring

# 5. 验证 / Verify
sudo systemctl status tutoring
```

## 安全最佳实践 / Security Best Practices

1. **使用 HTTPS / Use HTTPS**: 配置 SSL/TLS 证书
2. **限制访问 / Restrict Access**: 使用防火墙和安全组
3. **定期更新 / Regular Updates**: 保持系统和依赖最新
4. **备份数据 / Backup Data**: 定期备份数据库
5. **监控日志 / Monitor Logs**: 定期检查异常活动
6. **使用密钥管理 / Use Secret Management**: 不要在配置文件中硬编码密钥

## 性能优化 / Performance Optimization

1. **数据库优化 / Database Optimization**
   ```sql
   -- 创建索引 / Create indexes
   CREATE INDEX idx_conversation_id ON messages(conversation_id);
   CREATE INDEX idx_user_id ON user_profiles(user_id);
   
   -- 定期清理 / Regular cleanup
   DELETE FROM messages WHERE timestamp < datetime('now', '-30 days');
   VACUUM;
   ```

2. **缓存配置 / Cache Configuration**
   - 使用 Redis 缓存频繁查询的数据
   - 缓存 LLM 响应以减少 API 调用

3. **负载均衡 / Load Balancing**
   - 部署多个实例
   - 使用 Nginx 或 HAProxy 进行负载均衡

## 更多信息 / More Information

- [配置指南](CONFIGURATION.md) / [Configuration Guide](CONFIGURATION.md)
- [README](../README.md)
- [故障排除指南](TROUBLESHOOTING.md) / [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
