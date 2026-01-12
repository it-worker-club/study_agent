# 配置指南 / Configuration Guide

本文档详细说明教育辅导系统的配置选项。

This document provides detailed information about configuration options for the Education Tutoring System.

## 目录 / Table of Contents

- [配置文件结构](#配置文件结构--configuration-file-structure)
- [vLLM 服务配置](#vllm-服务配置--vllm-service-configuration)
- [MCP 工具配置](#mcp-工具配置--mcp-tools-configuration)
- [Web 搜索配置](#web-搜索配置--web-search-configuration)
- [系统配置](#系统配置--system-configuration)
- [日志配置](#日志配置--logging-configuration)
- [智能体配置](#智能体配置--agent-configuration)
- [环境变量](#环境变量--environment-variables)
- [高级配置](#高级配置--advanced-configuration)

## 配置文件结构 / Configuration File Structure

配置文件位于 `config/system_config.yaml`，采用 YAML 格式。

The configuration file is located at `config/system_config.yaml` and uses YAML format.

```yaml
vllm:           # vLLM 服务配置
mcp:            # MCP 工具配置
web_search:     # Web 搜索配置
system:         # 系统配置
logging:        # 日志配置
agents:         # 智能体配置
```

## vLLM 服务配置 / vLLM Service Configuration

vLLM 是系统的核心 LLM 推理服务。

vLLM is the core LLM inference service for the system.

### 配置项 / Configuration Options

```yaml
vllm:
  # API 端点 / API endpoint
  # 格式 / Format: http://host:port/v1
  api_base: "http://117.50.214.73:8000/v1"
  
  # API 密钥 / API key
  # 如不需要认证，设为 null / Set to null if authentication is not required
  api_key: "your-api-key"
  
  # 模型名称 / Model name
  # 必须与 vLLM 服务器上部署的模型匹配
  # Must match the model deployed on the vLLM server
  model_name: "Qwen3-30B-A3B-GPTQ-Int4"
  
  # 温度参数 / Temperature parameter
  # 范围 / Range: 0.0 - 1.0
  # 较低值产生更确定的输出 / Lower values produce more deterministic output
  # 较高值产生更多样化的输出 / Higher values produce more diverse output
  temperature: 0.7
  
  # 最大生成 token 数 / Maximum tokens to generate
  # 建议范围 / Recommended range: 1000 - 4000
  max_tokens: 2000
  
  # 请求超时时间（秒）/ Request timeout in seconds
  # 建议范围 / Recommended range: 30 - 120
  timeout: 60
```

### 最佳实践 / Best Practices

1. **API 端点 / API Endpoint**
   - 确保 vLLM 服务器可访问 / Ensure vLLM server is accessible
   - 使用内网地址以提高性能 / Use internal network address for better performance
   - 配置负载均衡以提高可用性 / Configure load balancing for high availability

2. **温度参数 / Temperature**
   - 协调器：0.7（平衡创造性和准确性）/ Coordinator: 0.7 (balance creativity and accuracy)
   - 课程顾问：0.6（更注重准确性）/ Course Advisor: 0.6 (more accuracy-focused)
   - 学习规划师：0.5（最注重准确性）/ Learning Planner: 0.5 (most accuracy-focused)

3. **Token 限制 / Token Limits**
   - 根据模型上下文窗口调整 / Adjust based on model context window
   - 考虑对话历史长度 / Consider conversation history length
   - 监控 token 使用以优化成本 / Monitor token usage to optimize costs

### 故障排除 / Troubleshooting

**连接失败 / Connection Failed**
```bash
# 测试连接 / Test connection
curl http://your-vllm-server:8000/v1/models

# 检查防火墙 / Check firewall
telnet your-vllm-server 8000
```

**认证错误 / Authentication Error**
```yaml
# 确保 API 密钥正确 / Ensure API key is correct
api_key: "correct-api-key"

# 或禁用认证 / Or disable authentication
api_key: null
```

## MCP 工具配置 / MCP Tools Configuration

MCP (Model Context Protocol) 用于集成外部工具，如 Playwright。

MCP (Model Context Protocol) is used to integrate external tools like Playwright.

### 配置项 / Configuration Options

```yaml
mcp:
  # 启用/禁用 Playwright 集成 / Enable/disable Playwright integration
  playwright_enabled: true
  
  # 极客时间网站 URL / GeekTime website URL
  geektime_url: "https://time.geekbang.org/"
  
  # 浏览器无头模式 / Browser headless mode
  # true: 后台运行（生产环境推荐）/ true: run in background (recommended for production)
  # false: 显示浏览器窗口（调试时使用）/ false: show browser window (for debugging)
  browser_headless: true
  
  # 浏览器超时时间（毫秒）/ Browser timeout in milliseconds
  # 建议范围 / Recommended range: 10000 - 60000
  browser_timeout: 30000
```

### 最佳实践 / Best Practices

1. **生产环境 / Production Environment**
   ```yaml
   browser_headless: true
   browser_timeout: 30000
   ```

2. **开发/调试环境 / Development/Debug Environment**
   ```yaml
   browser_headless: false  # 可以看到浏览器操作
   browser_timeout: 60000   # 更长的超时时间
   ```

3. **性能优化 / Performance Optimization**
   - 使用无头模式减少资源消耗 / Use headless mode to reduce resource consumption
   - 根据网络状况调整超时时间 / Adjust timeout based on network conditions
   - 考虑使用浏览器池以提高并发性能 / Consider using browser pool for better concurrency

### 故障排除 / Troubleshooting

**Playwright 安装 / Playwright Installation**
```bash
# 安装 Playwright 浏览器 / Install Playwright browsers
playwright install chromium

# 或安装所有浏览器 / Or install all browsers
playwright install
```

**超时错误 / Timeout Error**
```yaml
# 增加超时时间 / Increase timeout
browser_timeout: 60000

# 或禁用 Playwright / Or disable Playwright
playwright_enabled: false
```

## Web 搜索配置 / Web Search Configuration

Web 搜索工具用于获取补充学习资源。

Web search tool is used to fetch supplementary learning resources.

### 配置项 / Configuration Options

```yaml
web_search:
  # 启用/禁用 Web 搜索 / Enable/disable web search
  enabled: true
  
  # 搜索提供商 / Search provider
  # 选项 / Options: duckduckgo, google, bing
  provider: "duckduckgo"
  
  # 最大搜索结果数 / Maximum number of search results
  # 建议范围 / Recommended range: 3 - 10
  max_results: 5
```

### 搜索提供商对比 / Search Provider Comparison

| 提供商 / Provider | 优点 / Pros | 缺点 / Cons |
|------------------|------------|------------|
| DuckDuckGo | 无需 API 密钥，隐私友好 / No API key needed, privacy-friendly | 结果可能较少 / Fewer results |
| Google | 结果质量高 / High-quality results | 需要 API 密钥和配额 / Requires API key and quota |
| Bing | 结果丰富 / Rich results | 需要 API 密钥 / Requires API key |

### 最佳实践 / Best Practices

1. **开发环境 / Development**
   ```yaml
   provider: "duckduckgo"  # 无需配置
   max_results: 3          # 减少请求时间
   ```

2. **生产环境 / Production**
   ```yaml
   provider: "google"      # 更好的结果质量
   max_results: 5          # 平衡质量和性能
   ```

## 系统配置 / System Configuration

系统级别的配置选项。

System-level configuration options.

### 配置项 / Configuration Options

```yaml
system:
  # 数据库路径 / Database path
  # 相对或绝对路径 / Relative or absolute path
  database_path: "./data/tutoring_system.db"
  
  # 最大循环次数 / Maximum loop count
  # 防止无限循环 / Prevent infinite loops
  # 建议范围 / Recommended range: 5 - 20
  max_loop_count: 10
  
  # 启用人机交互 / Enable human-in-the-loop
  # true: 关键决策需要用户确认 / true: critical decisions require user confirmation
  # false: 完全自动化 / false: fully automated
  enable_human_input: true
  
  # 会话超时时间（分钟）/ Session timeout in minutes
  # 建议范围 / Recommended range: 15 - 60
  session_timeout: 30
```

### 最佳实践 / Best Practices

1. **数据库位置 / Database Location**
   ```yaml
   # 开发环境 / Development
   database_path: "./data/tutoring_system.db"
   
   # 生产环境 / Production
   database_path: "/var/lib/tutoring/tutoring_system.db"
   ```

2. **循环控制 / Loop Control**
   - 较低值（5-8）：更严格的控制，适合简单任务 / Lower values (5-8): stricter control, suitable for simple tasks
   - 中等值（10-15）：平衡，适合大多数场景 / Medium values (10-15): balanced, suitable for most scenarios
   - 较高值（15-20）：更灵活，适合复杂任务 / Higher values (15-20): more flexible, suitable for complex tasks

3. **人机交互 / Human-in-the-Loop**
   ```yaml
   # 教育场景（推荐）/ Educational scenario (recommended)
   enable_human_input: true
   
   # 自动化场景 / Automated scenario
   enable_human_input: false
   ```

## 日志配置 / Logging Configuration

日志系统配置。

Logging system configuration.

### 配置项 / Configuration Options

```yaml
logging:
  # 日志级别 / Log level
  # 选项 / Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: "INFO"
  
  # 日志格式 / Log format
  # 支持 Python logging 格式字符串 / Supports Python logging format strings
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # 日志文件路径 / Log file path
  # 设为 null 仅输出到控制台 / Set to null for console output only
  file: "./logs/tutoring_system.log"
  
  # 最大日志文件大小（MB）/ Maximum log file size in MB
  max_file_size: 10
  
  # 保留的备份日志文件数 / Number of backup log files to keep
  backup_count: 5
```

### 日志级别说明 / Log Level Description

| 级别 / Level | 用途 / Purpose | 适用场景 / Use Case |
|-------------|---------------|-------------------|
| DEBUG | 详细的调试信息 / Detailed debug info | 开发和故障排除 / Development and troubleshooting |
| INFO | 一般信息 / General information | 生产环境监控 / Production monitoring |
| WARNING | 警告信息 / Warning messages | 潜在问题 / Potential issues |
| ERROR | 错误信息 / Error messages | 错误追踪 / Error tracking |
| CRITICAL | 严重错误 / Critical errors | 系统故障 / System failures |

### 最佳实践 / Best Practices

1. **开发环境 / Development**
   ```yaml
   level: "DEBUG"
   file: "./logs/dev.log"
   max_file_size: 50  # 更大的日志文件
   ```

2. **生产环境 / Production**
   ```yaml
   level: "INFO"
   file: "/var/log/tutoring/system.log"
   max_file_size: 10
   backup_count: 10  # 保留更多历史日志
   ```

3. **日志格式 / Log Format**
   ```yaml
   # 详细格式（包含文件和行号）/ Detailed format (with file and line number)
   format: "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
   
   # JSON 格式（便于日志分析）/ JSON format (for log analysis)
   format: '{"time":"%(asctime)s","name":"%(name)s","level":"%(levelname)s","message":"%(message)s"}'
   ```

## 智能体配置 / Agent Configuration

各智能体的个性化配置。

Individual agent configuration.

### 配置项 / Configuration Options

```yaml
agents:
  # 协调器配置 / Coordinator configuration
  coordinator:
    temperature: 0.7
    max_tokens: 1500
  
  # 课程顾问配置 / Course advisor configuration
  course_advisor:
    temperature: 0.6
    max_tokens: 2000
  
  # 学习规划师配置 / Learning planner configuration
  learning_planner:
    temperature: 0.5
    max_tokens: 2500
```

### 智能体特性 / Agent Characteristics

| 智能体 / Agent | 温度 / Temperature | Token 限制 / Max Tokens | 特点 / Characteristics |
|---------------|-------------------|------------------------|----------------------|
| Coordinator | 0.7 | 1500 | 平衡创造性和准确性 / Balanced creativity and accuracy |
| Course Advisor | 0.6 | 2000 | 更注重准确性，需要详细描述 / More accuracy-focused, needs detailed descriptions |
| Learning Planner | 0.5 | 2500 | 最注重准确性，生成结构化计划 / Most accuracy-focused, generates structured plans |

### 最佳实践 / Best Practices

1. **温度调优 / Temperature Tuning**
   - 创造性任务：0.7-0.9 / Creative tasks: 0.7-0.9
   - 平衡任务：0.5-0.7 / Balanced tasks: 0.5-0.7
   - 精确任务：0.1-0.5 / Precise tasks: 0.1-0.5

2. **Token 限制 / Token Limits**
   - 简短响应：500-1000 / Short responses: 500-1000
   - 中等响应：1000-2000 / Medium responses: 1000-2000
   - 详细响应：2000-4000 / Detailed responses: 2000-4000

## 环境变量 / Environment Variables

系统支持通过环境变量覆盖配置。

The system supports overriding configuration via environment variables.

### 支持的环境变量 / Supported Environment Variables

```bash
# vLLM 配置 / vLLM configuration
export VLLM_API_BASE="http://your-server:8000/v1"
export VLLM_API_KEY="your-api-key"
export VLLM_MODEL_NAME="your-model"

# 数据库配置 / Database configuration
export DATABASE_PATH="/path/to/database.db"

# 日志配置 / Logging configuration
export LOG_LEVEL="DEBUG"
export LOG_FILE="/path/to/log.log"

# 系统配置 / System configuration
export MAX_LOOP_COUNT="15"
export SESSION_TIMEOUT="60"
```

### 优先级 / Priority

1. 环境变量（最高）/ Environment variables (highest)
2. 配置文件 / Configuration file
3. 默认值（最低）/ Default values (lowest)

## 高级配置 / Advanced Configuration

### 性能优化 / Performance Optimization

```yaml
# 启用缓存 / Enable caching
cache:
  enabled: true
  ttl: 3600  # 缓存生存时间（秒）/ Cache TTL in seconds
  max_size: 1000  # 最大缓存条目数 / Maximum cache entries

# 并发控制 / Concurrency control
concurrency:
  max_workers: 4  # 最大并发工作线程 / Maximum concurrent workers
  queue_size: 100  # 任务队列大小 / Task queue size
```

### 安全配置 / Security Configuration

```yaml
security:
  # 启用 API 认证 / Enable API authentication
  api_auth_enabled: true
  
  # API 密钥 / API keys
  api_keys:
    - "key1"
    - "key2"
  
  # 速率限制 / Rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 60
```

### 监控配置 / Monitoring Configuration

```yaml
monitoring:
  # 启用性能监控 / Enable performance monitoring
  enabled: true
  
  # 指标收集间隔（秒）/ Metrics collection interval in seconds
  interval: 60
  
  # 导出格式 / Export format
  export_format: "prometheus"  # prometheus, json, csv
```

## 配置验证 / Configuration Validation

验证配置文件是否正确：

Validate the configuration file:

```bash
# 使用验证脚本 / Use validation script
python -c "from src.utils.config import load_config; load_config('config/system_config.yaml')"

# 或运行系统进行验证 / Or run the system to validate
python main.py --config config/system_config.yaml --mode query --query "test"
```

## 配置示例 / Configuration Examples

### 最小配置 / Minimal Configuration

```yaml
vllm:
  api_base: "http://localhost:8000/v1"
  model_name: "your-model"

system:
  database_path: "./data/tutoring.db"
```

### 完整配置 / Full Configuration

参考 `config/system_config.yaml` 文件。

Refer to the `config/system_config.yaml` file.

## 故障排除 / Troubleshooting

### 配置加载失败 / Configuration Loading Failed

```bash
# 检查 YAML 语法 / Check YAML syntax
python -c "import yaml; yaml.safe_load(open('config/system_config.yaml'))"

# 检查文件权限 / Check file permissions
ls -l config/system_config.yaml
```

### 配置不生效 / Configuration Not Taking Effect

1. 检查环境变量是否覆盖了配置 / Check if environment variables override config
2. 确认配置文件路径正确 / Confirm config file path is correct
3. 重启应用以加载新配置 / Restart application to load new config

## 更多信息 / More Information

- [部署指南](DEPLOYMENT.md) / [Deployment Guide](DEPLOYMENT.md)
- [README](../README.md)
- [故障排除指南](TROUBLESHOOTING.md) / [Troubleshooting Guide](TROUBLESHOOTING.md)

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
