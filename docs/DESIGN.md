# 教育辅导系统 - 详细设计文档

## 目录

1. [系统概述](#系统概述)
2. [架构设计](#架构设计)
3. [核心组件](#核心组件)
4. [数据模型](#数据模型)
5. [工作流程](#工作流程)
6. [技术实现](#技术实现)
7. [测试策略](#测试策略)
8. [部署指南](#部署指南)

---

## 1. 系统概述

### 1.1 项目简介

教育辅导系统是一个基于 LangGraph 的多智能体协作平台，旨在为用户提供个性化的学习建议和课程推荐。系统采用 Supervisor 模式，通过协调器智能体管理课程顾问和学习规划师两个专业智能体，实现智能对话和服务。

### 1.2 核心特性

- **多智能体协作**: 3 个专业智能体（协调器、课程顾问、学习规划师）协同工作
- **智能路由**: 基于用户意图的动态路由决策
- **状态管理**: 统一的状态模型和跨智能体状态共享
- **工具集成**: MCP Playwright（极客时间）和 Web Search
- **记忆持久化**: SQLite 数据库存储对话历史和用户画像
- **人机协同**: 关键决策点的用户确认和反馈
- **错误处理**: 完善的错误检测和恢复机制
- **对话管理**: 多轮对话上下文维护和话题切换

### 1.3 技术栈

- **Python**: 3.10+
- **LangGraph**: 多智能体编排框架
- **LangChain**: LLM 集成和工具管理
- **vLLM**: 独立部署的 LLM 推理服务
- **SQLite**: 本地数据持久化
- **Pydantic**: 数据验证和配置管理
- **Pytest**: 测试框架
- **uv**: 项目和依赖管理

---

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                 │
│                    (CLI / API Interface)                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                    LangGraph 应用层                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  入口节点  │───▶│ 协调器   │───▶│ 路由器   │───▶│ 结束节点  │ │
│  └──────────┘    └──────────┘    └─────┬────┘    └──────────┘ │
│                                         │                        │
│                        ┌────────────────┼────────────────┐      │
│                        │                │                │      │
│                   ┌────▼────┐    ┌─────▼─────┐   ┌─────▼─────┐│
│                   │课程顾问  │    │学习规划师  │   │人机交互   ││
│                   └─────────┘    └───────────┘   └───────────┘│
│                                                                  │
│                   ┌──────────────────────────────┐             │
│                   │      共享状态 (AgentState)    │             │
│                   └──────────────────────────────┘             │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      外部服务层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ vLLM服务  │  │MCP工具   │  │Web搜索   │  │SQLite DB │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 架构模式

系统采用 **Supervisor 模式**，具有以下特点：

1. **协调器（Supervisor）**: 负责理解用户意图、任务分配和流程控制
2. **专业智能体（Worker Agents）**: 各自负责特定领域的任务执行
3. **共享状态（Shared State）**: 所有智能体通过统一的状态对象交换信息
4. **条件路由（Conditional Routing）**: 根据任务类型和状态动态选择执行路径

### 2.3 设计原则

- **单一职责**: 每个智能体专注于特定领域
- **松耦合**: 智能体之间通过状态通信，不直接依赖
- **可扩展**: 易于添加新的智能体和工具
- **容错性**: 完善的错误处理和恢复机制
- **可测试**: 模块化设计便于单元测试和集成测试

---

## 3. 核心组件

### 3.1 协调器智能体 (Coordinator)

#### 职责
- 分析用户输入，识别意图
- 决定任务路由（课程咨询/学习规划/人机交互）
- 管理对话流程和状态转换
- 汇总结果并生成最终响应

#### 核心功能

```python
class CoordinatorAgent:
    """协调器智能体"""
    
    def __init__(self, vllm_client, config):
        self.vllm_client = vllm_client
        self.config = config
        self.role = "coordinator"
    
    def analyze_and_route(self, state: AgentState) -> dict:
        """分析用户意图并做出路由决策"""
        # 1. 提取用户输入
        # 2. 构建 Prompt
        # 3. 调用 vLLM
        # 4. 解析决策结果
        return {
            "next_agent": "course_advisor",  # 或 learning_planner/human_input/end
            "current_task": "推荐 Python 课程",
            "requires_human_input": False
        }
```

#### Prompt 模板
```
你是一个教育辅导系统的协调器。你的职责是：
1. 理解用户的需求和意图
2. 决定由哪个专业智能体处理任务
3. 在必要时请求用户确认

可用的智能体：
- course_advisor: 课程顾问，负责推荐和介绍课程
- learning_planner: 学习规划师，负责制定学习计划

当前对话历史：{conversation_history}
用户最新输入：{user_input}

请分析用户意图，并以 JSON 格式返回决策：
{
  "next_agent": "course_advisor",
  "current_task": "任务描述",
  "requires_human_input": false
}
```

### 3.2 课程顾问智能体 (Course Advisor)

#### 职责
- 通过 MCP Playwright 访问极客时间网站搜索课程
- 通过 Web 搜索工具获取补充资源
- 分析课程内容和用户需求的匹配度
- 生成课程推荐和详细说明

#### 核心功能
```python
class CourseAdvisorAgent:
    """课程顾问智能体"""
    
    def __init__(self, vllm_client, tool_manager, config):
        self.vllm_client = vllm_client
        self.tool_manager = tool_manager
        self.config = config
        self.role = "course_advisor"
    
    def recommend_courses(self, state: AgentState) -> List[CourseInfo]:
        """推荐课程"""
        # 1. 搜索课程
        courses = self.search_courses(state["current_task"])
        
        # 2. 分析匹配度
        # 3. 生成推荐
        return courses
    
    def search_courses(self, query: str) -> List[CourseInfo]:
        """搜索课程"""
        # 使用 MCP Playwright 和 Web Search
        geektime_courses = self.tool_manager.search_courses(query)
        web_resources = self.tool_manager.search_web(query)
        return geektime_courses + web_resources
```

#### 工具集成
- `search_geektime_courses(query)`: 搜索极客时间课程
- `get_course_details(url)`: 获取课程详细信息
- `web_search(query)`: Web 搜索补充资源

### 3.3 学习规划师智能体 (Learning Planner)

#### 职责
- 根据用户目标制定结构化学习计划
- 将目标分解为可执行的里程碑
- 估算学习时间和资源需求
- 整合推荐课程到学习计划中

#### 核心功能

```python
class LearningPlannerAgent:
    """学习规划师智能体"""
    
    def __init__(self, vllm_client, tool_manager, config):
        self.vllm_client = vllm_client
        self.tool_manager = tool_manager
        self.config = config
        self.role = "learning_planner"
    
    def create_learning_plan(self, state: AgentState) -> LearningPlan:
        """创建学习计划"""
        # 1. 分析学习目标
        # 2. 搜索学习路径
        # 3. 分解里程碑
        # 4. 估算时间
        # 5. 整合课程
        return learning_plan
```

### 3.4 状态管理

#### AgentState 定义
```python
from typing import TypedDict, List, Dict, Optional, Literal
from datetime import datetime

class Message(TypedDict):
    """消息结构"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    agent: Optional[str]

class UserProfile(TypedDict):
    """用户画像"""
    user_id: str
    background: Optional[str]
    skill_level: Optional[str]  # beginner/intermediate/advanced
    learning_goals: List[str]
    time_availability: Optional[str]
    preferences: Dict[str, any]

class CourseInfo(TypedDict):
    """课程信息"""
    title: str
    url: str
    description: str
    difficulty: str
    duration: Optional[str]
    rating: Optional[float]
    source: str

class LearningPlan(TypedDict):
    """学习计划"""
    goal: str
    milestones: List[Dict[str, any]]
    recommended_courses: List[CourseInfo]
    estimated_duration: str
    created_at: datetime
    status: str

class AgentState(TypedDict):
    """系统状态"""
    # 对话相关
    messages: List[Message]
    conversation_id: str
    
    # 用户相关
    user_profile: UserProfile
    
    # 任务相关
    current_task: Optional[str]
    next_agent: Optional[str]
    
    # 数据相关
    course_candidates: List[CourseInfo]
    learning_plan: Optional[LearningPlan]
    
    # 控制相关
    requires_human_input: bool
    human_feedback: Optional[str]
    loop_count: int
    is_complete: bool
```

#### 状态辅助函数
```python
def create_initial_state(conversation_id: str, user_id: str = None) -> AgentState:
    """创建初始状态"""
    return {
        "messages": [],
        "conversation_id": conversation_id,
        "user_profile": {
            "user_id": user_id or conversation_id,
            "background": None,
            "skill_level": None,
            "learning_goals": [],
            "time_availability": None,
            "preferences": {}
        },
        "current_task": None,
        "next_agent": None,
        "course_candidates": [],
        "learning_plan": None,
        "requires_human_input": False,
        "human_feedback": None,
        "loop_count": 0,
        "is_complete": False
    }
```

### 3.5 路由逻辑

#### 路由函数

```python
def route_next(state: AgentState, max_loop_count: int = 10) -> str:
    """路由决策函数"""
    # 1. 检查循环次数
    if state["loop_count"] > max_loop_count:
        return "end"
    
    # 2. 检查是否需要人工输入
    if state["requires_human_input"]:
        return "human_input"
    
    # 3. 检查是否完成
    if state["is_complete"]:
        return "end"
    
    # 4. 根据 next_agent 路由
    next_agent = state.get("next_agent")
    if next_agent == "course_advisor":
        return "course_advisor"
    elif next_agent == "learning_planner":
        return "learning_planner"
    elif next_agent == "coordinator":
        return "coordinator"
    else:
        return "end"
```

### 3.6 人机交互节点

```python
def human_input_node(state: AgentState) -> AgentState:
    """人机交互节点"""
    # 1. 检查是否有反馈
    if not state.get("human_feedback"):
        # 等待用户输入
        return state
    
    # 2. 处理反馈
    feedback = state["human_feedback"]
    
    # 3. 识别反馈类型
    if any(keyword in feedback.lower() for keyword in ["同意", "确认", "好的", "可以"]):
        # 用户同意
        state["requires_human_input"] = False
        state["next_agent"] = "coordinator"
    elif any(keyword in feedback.lower() for keyword in ["修改", "调整", "不满意"]):
        # 用户要求修改
        state["requires_human_input"] = False
        state["next_agent"] = "learning_planner"  # 或其他智能体
    else:
        # 一般反馈
        state["requires_human_input"] = False
        state["next_agent"] = "coordinator"
    
    # 4. 添加反馈到消息历史
    state["messages"].append({
        "role": "user",
        "content": feedback,
        "timestamp": datetime.now(),
        "agent": None
    })
    
    # 5. 清除反馈
    state["human_feedback"] = None
    
    return state
```

---

## 4. 数据模型

### 4.1 数据库 Schema

```sql
-- 对话会话表
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

-- 消息表
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

-- 用户画像表
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    background TEXT,
    skill_level TEXT,
    learning_goals TEXT,  -- JSON 数组
    time_availability TEXT,
    preferences TEXT,  -- JSON 对象
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习计划表
CREATE TABLE learning_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    plan_content TEXT NOT NULL,  -- JSON 对象
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);
```

### 4.2 配置模型

```python
from pydantic import BaseModel, Field

class VLLMConfig(BaseModel):
    """vLLM 服务配置"""
    api_base: str
    api_key: Optional[str] = None
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60

class MCPConfig(BaseModel):
    """MCP 工具配置"""
    playwright_enabled: bool = True
    geektime_url: str = "https://time.geekbang.org/"
    browser_headless: bool = True

class SystemConfig(BaseModel):
    """系统配置"""
    vllm: VLLMConfig
    mcp: MCPConfig
    database_path: str = "./data/tutoring_system.db"
    max_loop_count: int = 10
    enable_human_input: bool = True
```

---

## 5. 工作流程

### 5.1 课程推荐流程

```
用户输入: "我想学习 Python 数据分析"
    ↓
入口节点 → 创建初始状态
    ↓
协调器节点 → 分析意图: "课程咨询"
    ↓
路由器 → 路由到课程顾问
    ↓
课程顾问节点 → 搜索课程 → 生成推荐
    ↓
路由器 → 返回协调器
    ↓
协调器节点 → 生成最终响应
    ↓
结束节点 → 返回结果
```

### 5.2 学习计划制定流程

```
用户输入: "帮我制定学习计划"
    ↓
协调器节点 → 分析意图: "学习规划"
    ↓
路由器 → 路由到学习规划师
    ↓
学习规划师节点 → 制定计划
    ↓
路由器 → 路由到人机交互
    ↓
人机交互节点 → 等待用户确认
    ↓
用户反馈 → 处理反馈
    ↓
路由器 → 根据反馈决定下一步
```

### 5.3 错误处理流程

```
智能体执行 → 发生错误
    ↓
错误处理器 → 识别错误类型
    ↓
记录日志 + 生成用户消息
    ↓
更新状态 → requires_human_input = True
    ↓
路由到人机交互 → 通知用户
```

---

## 6. 技术实现

### 6.1 LangGraph 图构建

```python
from langgraph.graph import StateGraph, END

def create_graph(config: SystemConfig, checkpointer=None):
    """创建 LangGraph 图"""
    # 1. 创建 StateGraph
    graph = StateGraph(AgentState)
    
    # 2. 添加节点
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("course_advisor", course_advisor_node)
    graph.add_node("learning_planner", learning_planner_node)
    graph.add_node("human_input", human_input_node)
    
    # 3. 设置入口点
    graph.set_entry_point("coordinator")
    
    # 4. 添加条件边
    graph.add_conditional_edges(
        "coordinator",
        route_next,
        {
            "course_advisor": "course_advisor",
            "learning_planner": "learning_planner",
            "human_input": "human_input",
            "end": END
        }
    )
    
    # 5. 添加返回边
    graph.add_edge("course_advisor", "coordinator")
    graph.add_edge("learning_planner", "coordinator")
    graph.add_edge("human_input", "coordinator")
    
    # 6. 编译图
    return graph.compile(checkpointer=checkpointer)
```

### 6.2 vLLM 客户端

```python
from openai import OpenAI

class VLLMClient:
    """vLLM 客户端"""
    
    def __init__(self, config: VLLMConfig):
        self.client = OpenAI(
            api_key=config.api_key or "EMPTY",
            base_url=config.api_base
        )
        self.config = config
    
    def generate(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        response = self.client.chat.completions.create(
            model=self.config.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens)
        )
        return response.choices[0].message.content
```

### 6.3 工具管理器

```python
class ToolManager:
    """工具管理器"""
    
    def __init__(self, config: MCPConfig):
        self.mcp_client = MCPPlaywrightClient(config)
        self.web_search_client = WebSearchClient()
    
    def search_courses(self, query: str) -> List[CourseInfo]:
        """搜索课程"""
        try:
            return self.mcp_client.search_geektime_courses(query)
        except Exception as e:
            logger.error(f"MCP search failed: {e}")
            return self.web_search_client.search(query)
    
    def search_web(self, query: str) -> List[Dict]:
        """Web 搜索"""
        return self.web_search_client.search(query)
```

### 6.4 记忆持久化

```python
from langgraph.checkpoint.sqlite import AsyncSQLiteSaver

async def create_checkpointer(db_path: str):
    """创建检查点保存器"""
    return AsyncSQLiteSaver.from_conn_string(db_path)

def persist_state(db: Database, state: AgentState):
    """持久化状态"""
    # 保存对话
    db.create_conversation(
        state["conversation_id"],
        state["user_profile"]["user_id"]
    )
    
    # 保存消息
    for message in state["messages"]:
        db.save_message(state["conversation_id"], message)
    
    # 保存用户画像
    db.save_user_profile(state["user_profile"])
    
    # 保存学习计划
    if state["learning_plan"]:
        db.save_learning_plan(
            state["conversation_id"],
            state["user_profile"]["user_id"],
            state["learning_plan"]
        )
```

---

## 7. 测试策略

### 7.1 单元测试

测试单个组件的功能：

```python
def test_coordinator_initialization():
    """测试协调器初始化"""
    coordinator = CoordinatorAgent(mock_vllm, config)
    assert coordinator.role == "coordinator"

def test_route_next_to_course_advisor():
    """测试路由到课程顾问"""
    state = create_initial_state("test")
    state["next_agent"] = "course_advisor"
    assert route_next(state) == "course_advisor"
```

### 7.2 集成测试

测试多个组件协作：

```python
def test_complete_course_recommendation_flow():
    """测试完整课程推荐流程"""
    graph = create_graph(config)
    state = create_initial_state("test")
    state["messages"].append({
        "role": "user",
        "content": "推荐 Python 课程",
        "timestamp": datetime.now()
    })
    
    result = graph.invoke(state)
    assert len(result["course_candidates"]) > 0
```

### 7.3 测试覆盖率

- **目标覆盖率**: > 80%
- **当前覆盖率**: 68%
- **核心模块覆盖**: 90%+

---

## 8. 部署指南

### 8.1 环境准备

```bash
# 1. 安装 Python 3.10+
python --version

# 2. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 克隆项目
git clone <repository-url>
cd education-tutoring-system

# 4. 安装依赖
uv sync
```

### 8.2 配置

编辑 `config/system_config.yaml`:

```yaml
vllm:
  api_base: "http://your-vllm-server:8000/v1"
  model_name: "your-model-name"
  temperature: 0.7
  max_tokens: 2000

mcp:
  playwright_enabled: true
  geektime_url: "https://time.geekbang.org/"
  browser_headless: true

system:
  database_path: "./data/tutoring_system.db"
  max_loop_count: 10
  enable_human_input: true
```

### 8.3 初始化数据库

```bash
python -c "from src.memory.database import Database; Database('./data/tutoring_system.db').init_database()"
```

### 8.4 运行系统

```bash
# CLI 模式
python src/main.py

# API 模式（需要安装 FastAPI）
python src/main.py --mode api --port 8000
```

### 8.5 运行测试

```bash
# 运行所有测试
pytest tests/

# 查看覆盖率
pytest tests/ --cov=src --cov-report=html
```

---

## 附录

### A. 项目结构

```
education-tutoring-system/
├── src/
│   ├── agents/              # 智能体实现
│   ├── graph/               # LangGraph 图
│   ├── tools/               # 工具集成
│   ├── memory/              # 记忆持久化
│   ├── llm/                 # LLM 集成
│   ├── utils/               # 工具类
│   └── main.py              # 主应用
├── tests/
│   ├── unit/                # 单元测试
│   └── integration/         # 集成测试
├── config/
│   └── system_config.yaml   # 系统配置
├── docs/                    # 文档
├── examples/                # 示例代码
└── data/                    # 数据文件
```

### B. 参考文档

- [配置指南](CONFIGURATION.md)
- [部署指南](DEPLOYMENT.md)
- [README](../README.md)

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
