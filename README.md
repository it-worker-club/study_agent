# 教育辅导系统

一个基于 LangGraph 的多智能体教育辅导系统，提供个性化的课程推荐和学习计划制定服务。

## 概述

本系统采用 Supervisor 模式的多智能体架构，通过协调器（Coordinator）管理课程顾问（Course Advisor）和学习规划师（Learning Planner）两个专业智能体，实现智能化的教育咨询服务。系统集成了外部工具（MCP Playwright 访问极客时间网站、Web 搜索），支持对话记忆持久化、条件路由和人机协同交互。

## 核心特性

- **多智能体协作架构**：协调器、课程顾问和学习规划师协同工作
- **LangGraph 状态管理**：基于 LangGraph 的健壮状态管理和工作流编排
- **外部工具集成**：
  - MCP Playwright 访问极客时间课程信息
  - Web 搜索获取补充学习资源
- **记忆持久化**：基于 SQLite 的对话历史和用户画像存储
- **人机协同**：关键决策点的交互式用户反馈
- **vLLM 集成**：通过外部 vLLM 服务器提供高性能 LLM 推理
- **错误处理与恢复**：完善的错误处理和降级服务机制
- **性能监控**：实时性能指标和统计信息

## 项目结构

```
education-tutoring-system/
├── src/                      # 源代码
│   ├── agents/              # 智能体实现
│   │   ├── coordinator.py   # 协调器智能体
│   │   ├── course_advisor.py # 课程顾问智能体
│   │   └── learning_planner.py # 学习规划师智能体
│   ├── graph/               # LangGraph 状态和图定义
│   │   ├── state.py         # 状态模式定义
│   │   ├── nodes.py         # 节点函数实现
│   │   ├── builder.py       # 图构建器
│   │   ├── helpers.py       # 辅助函数
│   │   └── conversation_flow.py # 对话流程控制
│   ├── tools/               # 外部工具集成
│   │   ├── mcp_playwright.py # MCP Playwright 集成
│   │   ├── web_search.py    # Web 搜索工具
│   │   └── tool_manager.py  # 工具管理器
│   ├── memory/              # 记忆和持久化层
│   │   ├── database.py      # 数据库操作
│   │   └── checkpointer.py  # 检查点保存器
│   ├── llm/                 # vLLM 客户端集成
│   │   └── vllm_client.py   # vLLM 客户端
│   ├── utils/               # 工具函数和配置
│   │   ├── config.py        # 配置管理
│   │   ├── error_handler.py # 错误处理器
│   │   ├── logger.py        # 日志配置
│   │   └── monitoring.py    # 性能监控
│   └── main.py              # 应用入口
├── tests/                    # 测试
│   ├── unit/                # 单元测试
│   ├── property/            # 属性测试
│   └── integration/         # 集成测试
├── config/                   # 配置文件
│   └── system_config.yaml   # 系统配置
├── data/                     # 数据库和数据文件
│   └── tutoring_system.db   # SQLite 数据库
├── logs/                     # 日志文件
│   └── tutoring_system.log  # 应用日志
├── docs/                     # 文档
│   ├── CONFIGURATION.md     # 配置指南
│   └── DEPLOYMENT.md        # 部署指南
├── examples/                 # 示例代码
├── pyproject.toml           # 项目配置和依赖
├── uv.lock                  # 依赖锁定文件
└── README.md                # 本文件
```

## 安装

本项目使用 [uv](https://github.com/astral-sh/uv) 进行依赖管理。

### 前置要求

- Python 3.10 或更高版本
- uv 包管理器
- 运行中的 vLLM 服务器（用于 LLM 推理）

### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 使用 pip
pip install uv
```

### 设置步骤

1. **克隆仓库**：
```bash
git clone <repository-url>
cd education-tutoring-system
```

2. **安装依赖**：
```bash
# 安装基础依赖
uv sync

# 安装开发依赖
uv sync --extra dev

# 安装 API 依赖（可选）
uv sync --extra api
```

3. **配置系统**：
```bash
# 编辑配置文件
vim config/system_config.yaml
```

详细配置说明请参考 [配置指南](docs/CONFIGURATION.md)。

4. **初始化数据库**：
```bash
# 数据库会在首次运行时自动创建
python main.py
```

## 配置

编辑 `config/system_config.yaml` 配置以下内容：

- **vLLM 服务**：API 端点、模型名称、生成参数
- **MCP 工具**：Playwright 设置、极客时间 URL
- **Web 搜索**：搜索提供商和结果限制
- **系统**：数据库路径、循环限制、会话超时
- **日志**：日志级别、格式、文件位置
- **智能体**：各智能体的个性化参数

详细配置说明请参考 [配置指南](docs/CONFIGURATION.md)。

### 快速配置示例

```yaml
vllm:
  api_base: "http://your-vllm-server:8000/v1"
  api_key: "your-api-key"  # 如不需要认证设为 null
  model_name: "your-model-name"
  temperature: 0.7
  max_tokens: 2000

system:
  database_path: "./data/tutoring_system.db"
  max_loop_count: 10
  enable_human_input: true
```

## 使用方法

### 运行应用

系统提供两种运行模式：

#### 交互模式（默认）

在交互式 CLI 模式下运行系统，支持多轮对话：

```bash
# 启动交互模式
python main.py

# 使用自定义配置
python main.py --config path/to/config.yaml

# 使用调试日志
python main.py --log-level DEBUG
```

交互模式特性：
- 与辅导系统进行多轮对话
- 会话管理和持久化
- 实时性能统计
- 命令支持：`quit`、`exit`、`new`、`help`、`stats`

#### 单次查询模式

运行单次查询后退出（适用于脚本调用）：

```bash
# 单次查询
python main.py --mode query --query "我想学习Python数据分析"

# 指定用户 ID
python main.py --mode query --query "推荐课程" --user-id user123
```

### 命令行选项

```
--config PATH          配置文件路径（默认：config/system_config.yaml）
--mode MODE           运行模式：interactive 或 query（默认：interactive）
--query TEXT          单次查询模式的查询文本
--user-id ID          用户标识符（默认：cli_user）
--log-level LEVEL     日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL
```

### 示例会话

```
欢迎使用教育辅导智能体系统
============================================================

输入 'quit' 或 'exit' 退出系统
输入 'new' 开始新对话
输入 'help' 查看帮助信息
输入 'stats' 查看性能统计

请输入您的用户ID（或按回车使用默认）: 

已为用户 default_user 创建会话 abc123
请输入您的问题或需求：

您: 我想学习Python数据分析

[Coordinator]: 我理解您想学习Python数据分析。让我为您搜索相关课程...

[Course Advisor]: 我为您找到了以下课程推荐：

1. **Python数据分析实战**
   - 难度：中级
   - 来源：极客时间
   - 简介：全面讲解Python数据分析的核心技术...

2. **数据分析入门与实践**
   - 难度：初级
   - 来源：极客时间
   - 简介：从零开始学习数据分析...

3. **Python数据科学手册**
   - 难度：中高级
   - 来源：Web搜索
   - 简介：深入探讨数据科学的各个方面...

您想了解哪门课程的详细信息，或者需要我为您制定学习计划吗？

您: 请为我制定学习计划

[Learning Planner]: 好的，我将为您制定一个Python数据分析的学习计划...

学习计划已生成：
- 目标：掌握Python数据分析技能
- 预计时间：3-4个月
- 里程碑：
  1. Python基础（2周）
  2. 数据处理与清洗（3周）
  3. 数据可视化（2周）
  4. 统计分析（3周）
  5. 实战项目（4周）

您: stats

性能统计
============================================================

LLM 调用统计：
  总计：3
  成功：3
  平均耗时：1.23s
  总 tokens：1250

工具调用统计：
  search_geektime_courses: 1 次，平均 2.34s
  web_search: 1 次，平均 1.56s

节点执行统计：
  coordinator: 2 次，平均 1.45s
  course_advisor: 1 次，平均 3.89s
  learning_planner: 1 次，平均 2.67s
```

### 性能监控

系统包含全面的性能监控功能：

- **LLM 调用延迟和 token 使用**
- **工具执行时间**
- **节点执行时间**
- **对话统计**

在会话期间输入 `stats` 查看统计信息，或查看日志文件获取详细指标。

## 开发

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 仅运行单元测试
uv run pytest tests/unit

# 运行属性测试
uv run pytest tests/property

# 运行集成测试
uv run pytest tests/integration

# 生成覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 代码质量

```bash
# 格式化代码
uv run black src tests

# 代码检查
uv run ruff check src tests

# 类型检查
uv run mypy src
```

### 添加新智能体

1. 在 `src/agents/` 创建新的智能体类
2. 在 `src/graph/nodes.py` 添加节点函数
3. 在 `src/graph/builder.py` 注册智能体
4. 更新路由逻辑
5. 添加相应的测试

详细说明请参考开发文档。

## 架构

系统采用 **Supervisor 模式**，具有以下特点：

1. **协调器（Supervisor）**：负责理解用户意图、任务分配和流程控制
2. **专业智能体（Worker Agents）**：各自负责特定领域的任务执行
   - **课程顾问**：搜索和推荐课程
   - **学习规划师**：制定个性化学习计划
3. **共享状态（Shared State）**：所有智能体通过统一的状态对象交换信息
4. **条件路由（Conditional Routing）**：根据任务类型和状态动态选择执行路径

### 工作流程

```
用户输入 → 协调器分析意图 → 路由到专业智能体 → 执行任务 → 返回结果 → 协调器汇总 → 输出给用户
```

### 状态管理

系统使用 LangGraph 的 `StateGraph` 管理状态，包括：
- 对话历史
- 用户画像
- 任务上下文
- 中间结果

所有状态通过 SQLite 持久化，支持会话恢复。

## 故障排除

### 常见问题

**1. vLLM 连接失败**
```
错误：Failed to connect to vLLM service
解决方案：
- 检查 vLLM 服务器是否运行
- 验证配置文件中的 API 端点
- 检查网络连接
```

**2. 数据库锁定**
```
错误：Database is locked
解决方案：
- 确保没有其他进程访问数据库
- 检查文件权限
- 删除 .db-wal 和 .db-shm 文件
```

**3. MCP Playwright 超时**
```
错误：Playwright navigation timeout
解决方案：
- 增加 browser_timeout 配置
- 检查网络连接
- 验证目标网站可访问
```

**4. 内存不足**
```
错误：MemoryError
解决方案：
- 减少 max_tokens 配置
- 限制对话历史长度
- 增加系统内存
```

### 日志分析

查看日志文件获取详细错误信息：

```bash
# 查看最新日志
tail -f logs/tutoring_system.log

# 搜索错误
grep ERROR logs/tutoring_system.log

# 查看特定会话
grep "conversation_id=abc123" logs/tutoring_system.log
```

## 部署

详细的部署指南请参考 [部署文档](docs/DEPLOYMENT.md)。

### 快速部署

```bash
# 1. 克隆仓库
git clone <repository-url>
cd education-tutoring-system

# 2. 安装依赖
uv sync

# 3. 配置系统
vim config/system_config.yaml

# 4. 运行系统
python main.py
```

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m 'Add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 开启 Pull Request

### 开发规范

- 遵循 PEP 8 代码风格
- 为新功能添加测试
- 更新文档
- 确保所有测试通过

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph) - 多智能体框架
- [vLLM](https://github.com/vllm-project/vllm) - 高性能 LLM 推理
- [uv](https://github.com/astral-sh/uv) - 快速 Python 包管理器

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 Issue：[GitHub Issues](https://github.com/it-worker-club/study_agent/issues)
- GitHub 仓库：[study_agent](https://github.com/it-worker-club/study_agent)

## 作者

**Tango**

- 项目维护者
- 主要开发者

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。
