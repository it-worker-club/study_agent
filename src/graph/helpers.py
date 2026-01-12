"""Helper functions for state management.

This module provides utility functions for creating, validating,
and manipulating the AgentState object, as well as persistence
functions for user profiles and learning plans.
"""

import uuid
from datetime import datetime
from typing import Optional

from src.graph.state import AgentState, UserProfile, LearningPlan


def create_initial_state(
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> AgentState:
    """创建初始状态对象
    
    Args:
        conversation_id: 对话会话ID，如果未提供则自动生成
        user_id: 用户ID，如果未提供则自动生成
        
    Returns:
        初始化的 AgentState 对象
    """
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    
    if user_id is None:
        user_id = str(uuid.uuid4())
    
    # 创建默认用户画像
    user_profile: UserProfile = {
        "user_id": user_id,
        "background": None,
        "skill_level": None,
        "learning_goals": [],
        "time_availability": None,
        "preferences": {},
    }
    
    # 创建初始状态
    state: AgentState = {
        # 对话相关
        "messages": [],
        "conversation_id": conversation_id,
        
        # 用户相关
        "user_profile": user_profile,
        
        # 任务相关
        "current_task": None,
        "next_agent": None,
        
        # 数据相关
        "course_candidates": [],
        "learning_plan": None,
        
        # 控制相关
        "requires_human_input": False,
        "human_feedback": None,
        "loop_count": 0,
        "is_complete": False,
    }
    
    return state


def validate_state(state: AgentState) -> tuple[bool, Optional[str]]:
    """验证状态对象的完整性和有效性
    
    Args:
        state: 要验证的状态对象
        
    Returns:
        (is_valid, error_message) 元组
        - is_valid: 状态是否有效
        - error_message: 如果无效，返回错误信息；否则为 None
    """
    # 检查必需字段
    required_fields = [
        "messages",
        "conversation_id",
        "user_profile",
        "current_task",
        "next_agent",
        "course_candidates",
        "learning_plan",
        "requires_human_input",
        "human_feedback",
        "loop_count",
        "is_complete",
    ]
    
    for field in required_fields:
        if field not in state:
            return False, f"Missing required field: {field}"
    
    # 验证 conversation_id
    if not state["conversation_id"] or not isinstance(state["conversation_id"], str):
        return False, "conversation_id must be a non-empty string"
    
    # 验证 messages
    if not isinstance(state["messages"], list):
        return False, "messages must be a list"
    
    for i, msg in enumerate(state["messages"]):
        if not isinstance(msg, dict):
            return False, f"Message at index {i} must be a dict"
        
        if "role" not in msg or msg["role"] not in ["user", "assistant", "system"]:
            return False, f"Message at index {i} has invalid role"
        
        if "content" not in msg or not isinstance(msg["content"], str):
            return False, f"Message at index {i} must have string content"
        
        if "timestamp" not in msg:
            return False, f"Message at index {i} must have timestamp"
    
    # 验证 user_profile
    if not isinstance(state["user_profile"], dict):
        return False, "user_profile must be a dict"
    
    profile = state["user_profile"]
    if "user_id" not in profile or not isinstance(profile["user_id"], str):
        return False, "user_profile must have a valid user_id"
    
    if "learning_goals" not in profile or not isinstance(profile["learning_goals"], list):
        return False, "user_profile must have learning_goals list"
    
    if "preferences" not in profile or not isinstance(profile["preferences"], dict):
        return False, "user_profile must have preferences dict"
    
    # 验证 skill_level（如果存在）
    if profile.get("skill_level") is not None:
        valid_levels = ["beginner", "intermediate", "advanced"]
        if profile["skill_level"] not in valid_levels:
            return False, f"skill_level must be one of {valid_levels}"
    
    # 验证 course_candidates
    if not isinstance(state["course_candidates"], list):
        return False, "course_candidates must be a list"
    
    for i, course in enumerate(state["course_candidates"]):
        if not isinstance(course, dict):
            return False, f"Course at index {i} must be a dict"
        
        required_course_fields = ["title", "url", "description", "difficulty", "source"]
        for field in required_course_fields:
            if field not in course:
                return False, f"Course at index {i} missing field: {field}"
    
    # 验证 learning_plan（如果存在）
    if state["learning_plan"] is not None:
        plan = state["learning_plan"]
        if not isinstance(plan, dict):
            return False, "learning_plan must be a dict"
        
        required_plan_fields = [
            "goal",
            "milestones",
            "recommended_courses",
            "estimated_duration",
            "created_at",
            "status",
        ]
        for field in required_plan_fields:
            if field not in plan:
                return False, f"learning_plan missing field: {field}"
        
        if not isinstance(plan["milestones"], list):
            return False, "learning_plan.milestones must be a list"
        
        if not isinstance(plan["recommended_courses"], list):
            return False, "learning_plan.recommended_courses must be a list"
        
        valid_statuses = ["draft", "approved", "in_progress"]
        if plan["status"] not in valid_statuses:
            return False, f"learning_plan.status must be one of {valid_statuses}"
    
    # 验证控制字段
    if not isinstance(state["requires_human_input"], bool):
        return False, "requires_human_input must be a boolean"
    
    if not isinstance(state["loop_count"], int):
        return False, "loop_count must be an integer"
    
    if state["loop_count"] < 0:
        return False, "loop_count must be non-negative"
    
    if not isinstance(state["is_complete"], bool):
        return False, "is_complete must be a boolean"
    
    # 验证 next_agent（如果存在）
    if state["next_agent"] is not None:
        valid_agents = [
            "coordinator",
            "course_advisor",
            "learning_planner",
            "human_input",
            "end",
        ]
        if state["next_agent"] not in valid_agents:
            return False, f"next_agent must be one of {valid_agents}"
    
    return True, None


def add_message(
    state: AgentState,
    role: str,
    content: str,
    agent: Optional[str] = None,
) -> AgentState:
    """向状态添加新消息
    
    Args:
        state: 当前状态
        role: 消息角色 (user/assistant/system)
        content: 消息内容
        agent: 发送消息的智能体名称（可选）
        
    Returns:
        更新后的状态
    """
    from src.graph.state import Message
    
    message: Message = {
        "role": role,  # type: ignore
        "content": content,
        "timestamp": datetime.now(),
        "agent": agent,
    }
    
    state["messages"].append(message)
    return state


def increment_loop_count(state: AgentState) -> AgentState:
    """增加循环计数
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    state["loop_count"] += 1
    return state


def reset_loop_count(state: AgentState) -> AgentState:
    """重置循环计数
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    state["loop_count"] = 0
    return state


def mark_complete(state: AgentState) -> AgentState:
    """标记任务完成
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    state["is_complete"] = True
    state["next_agent"] = "end"
    return state


def request_human_input(state: AgentState) -> AgentState:
    """请求人工输入
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    state["requires_human_input"] = True
    state["next_agent"] = "human_input"
    return state


def clear_human_input_request(state: AgentState) -> AgentState:
    """清除人工输入请求
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    state["requires_human_input"] = False
    state["human_feedback"] = None
    return state


def route_next(state: AgentState, max_loop_count: int = 10) -> str:
    """路由决策函数
    
    根据当前状态决定下一个要执行的节点。实现以下逻辑：
    1. 检查循环次数，防止无限循环
    2. 检查是否需要人工输入
    3. 检查任务是否完成
    4. 根据 next_agent 字段路由到相应节点
    
    这个函数被 LangGraph 用作条件边的路由函数。
    
    Args:
        state: 当前状态
        max_loop_count: 最大循环次数，默认为 10
        
    Returns:
        下一个节点的名称（字符串）
        可能的返回值：
        - "coordinator": 协调器节点
        - "course_advisor": 课程顾问节点
        - "learning_planner": 学习规划师节点
        - "human_input": 人机交互节点
        - "end": 结束节点
        
    Validates:
        - Requirements 5.2: 支持基于对话状态的条件路由
        - Requirements 9.5: 检测和处理对话循环或死胡同
    """
    # 1. 检查循环次数，防止无限循环
    # Property 24: Loop Prevention
    if state["loop_count"] > max_loop_count:
        return "end"
    
    # 2. 检查任务是否完成
    if state["is_complete"]:
        return "end"
    
    # 3. 检查是否需要人工输入
    # Property 11: Human-in-the-Loop for Critical Decisions
    if state["requires_human_input"]:
        return "human_input"
    
    # 4. 根据 next_agent 字段路由
    # Property 8: Routing Correctness
    next_agent = state.get("next_agent")
    
    # 定义有效的智能体节点
    valid_agents = {
        "coordinator",
        "course_advisor",
        "learning_planner",
        "human_input",
        "end",
    }
    
    # 如果 next_agent 有效，返回它
    if next_agent in valid_agents:
        return next_agent
    
    # 如果 next_agent 无效或为 None，默认路由到 end
    # 这是一个安全的默认行为，防止系统卡住
    return "end"



def persist_state_to_database(
    state: AgentState,
    database_path: str,
) -> bool:
    """将状态持久化到数据库
    
    保存用户画像、学习计划和消息到数据库。
    
    Args:
        state: 当前状态
        database_path: 数据库文件路径
        
    Returns:
        是否保存成功
    """
    from src.memory.database import (
        get_database_manager,
        create_conversation,
        save_message,
    )
    from src.memory.checkpointer import (
        save_user_profile,
        save_learning_plan,
    )
    
    try:
        db_manager = get_database_manager(database_path)
        
        # 1. 确保对话会话存在
        create_conversation(
            db_manager,
            state["conversation_id"],
            state["user_profile"]["user_id"],
        )
        
        # 2. 保存用户画像
        save_user_profile(db_manager, state["user_profile"])
        
        # 3. 保存消息（只保存新消息）
        # 注意：在实际使用中，应该跟踪哪些消息已经保存
        # 这里简化处理，假设调用者会管理消息保存
        for message in state["messages"]:
            save_message(
                db_manager,
                state["conversation_id"],
                message["role"],
                message["content"],
                message.get("agent"),
                message["timestamp"],
            )
        
        # 4. 保存学习计划（如果存在）
        if state["learning_plan"] is not None:
            save_learning_plan(
                db_manager,
                state["conversation_id"],
                state["user_profile"]["user_id"],
                state["learning_plan"],
            )
        
        return True
    
    except Exception as e:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to persist state to database: {e}")
        return False


def load_state_from_database(
    conversation_id: str,
    database_path: str,
) -> Optional[AgentState]:
    """从数据库加载状态
    
    加载对话历史、用户画像和学习计划。
    
    Args:
        conversation_id: 对话 ID
        database_path: 数据库文件路径
        
    Returns:
        加载的状态对象，如果不存在则返回 None
    """
    from src.memory.database import (
        get_database_manager,
        load_messages,
    )
    from src.memory.checkpointer import (
        load_user_profile,
        load_learning_plan,
    )
    
    try:
        db_manager = get_database_manager(database_path)
        
        # 1. 加载消息
        messages = load_messages(db_manager, conversation_id)
        
        if not messages:
            # 对话不存在
            return None
        
        # 2. 从消息中提取 user_id（假设第一条消息包含用户信息）
        # 或者从 conversations 表查询
        query = "SELECT user_id FROM conversations WHERE conversation_id = ?"
        row = db_manager.execute_query(query, (conversation_id,), fetch_one=True)
        
        if not row:
            return None
        
        user_id = row["user_id"]
        
        # 3. 加载用户画像
        user_profile = load_user_profile(db_manager, user_id)
        
        if not user_profile:
            # 创建默认用户画像
            user_profile = {
                "user_id": user_id,
                "background": None,
                "skill_level": None,
                "learning_goals": [],
                "time_availability": None,
                "preferences": {},
            }
        
        # 4. 加载学习计划
        learning_plan = load_learning_plan(
            db_manager,
            conversation_id=conversation_id,
        )
        
        # 5. 构建状态对象
        state: AgentState = {
            "messages": messages,
            "conversation_id": conversation_id,
            "user_profile": user_profile,
            "current_task": None,
            "next_agent": None,
            "course_candidates": [],
            "learning_plan": learning_plan,
            "requires_human_input": False,
            "human_feedback": None,
            "loop_count": 0,
            "is_complete": False,
        }
        
        return state
    
    except Exception as e:
        from src.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to load state from database: {e}")
        return None


def update_user_profile_in_state(
    state: AgentState,
    database_path: str,
    **profile_updates,
) -> AgentState:
    """更新状态中的用户画像并持久化
    
    Args:
        state: 当前状态
        database_path: 数据库文件路径
        **profile_updates: 要更新的用户画像字段
        
    Returns:
        更新后的状态
    """
    from src.memory.database import get_database_manager
    from src.memory.checkpointer import save_user_profile
    
    # 更新状态中的用户画像
    for key, value in profile_updates.items():
        if key in state["user_profile"]:
            state["user_profile"][key] = value  # type: ignore
    
    # 持久化到数据库
    db_manager = get_database_manager(database_path)
    save_user_profile(db_manager, state["user_profile"])
    
    return state


def save_learning_plan_from_state(
    state: AgentState,
    database_path: str,
) -> Optional[int]:
    """从状态保存学习计划到数据库
    
    Args:
        state: 当前状态
        database_path: 数据库文件路径
        
    Returns:
        学习计划 ID，如果保存失败则返回 None
    """
    from src.memory.database import get_database_manager
    from src.memory.checkpointer import save_learning_plan
    
    if state["learning_plan"] is None:
        return None
    
    db_manager = get_database_manager(database_path)
    
    return save_learning_plan(
        db_manager,
        state["conversation_id"],
        state["user_profile"]["user_id"],
        state["learning_plan"],
    )
