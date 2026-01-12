"""State management for the education tutoring system.

This module defines the state schema used by LangGraph to manage
conversation context, user information, and intermediate results
across multiple agents.
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict


class Message(TypedDict):
    """消息结构
    
    Attributes:
        role: 消息角色 (user/assistant/system)
        content: 消息内容
        timestamp: 消息时间戳
        agent: 发送消息的智能体名称（可选）
    """
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime
    agent: Optional[str]


class UserProfile(TypedDict):
    """用户画像
    
    Attributes:
        user_id: 用户唯一标识
        background: 技术背景（可选）
        skill_level: 技能水平 (beginner/intermediate/advanced)
        learning_goals: 学习目标列表
        time_availability: 可用学习时间（可选）
        preferences: 其他偏好设置
    """
    user_id: str
    background: Optional[str]
    skill_level: Optional[str]
    learning_goals: List[str]
    time_availability: Optional[str]
    preferences: Dict[str, Any]


class CourseInfo(TypedDict):
    """课程信息
    
    Attributes:
        title: 课程标题
        url: 课程链接
        description: 课程描述
        difficulty: 课程难度
        duration: 课程时长（可选）
        rating: 课程评分（可选）
        source: 课程来源 (geektime/web_search)
    """
    title: str
    url: str
    description: str
    difficulty: str
    duration: Optional[str]
    rating: Optional[float]
    source: str


class LearningPlan(TypedDict):
    """学习计划
    
    Attributes:
        goal: 学习目标
        milestones: 里程碑列表
        recommended_courses: 推荐课程列表
        estimated_duration: 预计学习时长
        created_at: 创建时间
        status: 计划状态 (draft/approved/in_progress)
    """
    goal: str
    milestones: List[Dict[str, Any]]
    recommended_courses: List[CourseInfo]
    estimated_duration: str
    created_at: datetime
    status: str


class AgentState(TypedDict):
    """系统状态
    
    这是 LangGraph 使用的核心状态对象，包含所有必要的上下文信息。
    所有智能体通过读写这个共享状态来交换信息。
    
    Attributes:
        messages: 对话消息历史
        conversation_id: 对话会话唯一标识
        user_profile: 用户画像信息
        current_task: 当前任务类型（可选）
        next_agent: 下一个执行的智能体（可选）
        course_candidates: 候选课程列表
        learning_plan: 学习计划（可选）
        requires_human_input: 是否需要人工输入
        human_feedback: 人工反馈内容（可选）
        loop_count: 循环计数，用于防止无限循环
        is_complete: 任务是否完成
    """
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
