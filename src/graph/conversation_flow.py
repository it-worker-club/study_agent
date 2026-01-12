"""Conversation flow control for the education tutoring system.

This module provides functions for maintaining conversation context,
handling agent transitions, and supporting conversation branching.

Validates:
    - Requirements 9.1: Maintain conversation context throughout the session
    - Requirements 9.2: Provide smooth transitions when switching between agents
    - Requirements 9.3: Support conversation branching and returning to previous topics
    - Requirements 9.4: Summarize results before proceeding when a subtask is completed
"""

from datetime import datetime
from typing import Dict, List, Optional

from src.graph.helpers import add_message
from src.graph.state import AgentState
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ConversationContext:
    """
    Manages conversation context and history.
    
    This class provides methods to:
    - Track conversation topics and subtasks
    - Maintain context across agent transitions
    - Support topic switching and returning
    """
    
    def __init__(self):
        """Initialize conversation context manager."""
        self.topic_stack: List[Dict[str, any]] = []
        self.subtask_history: List[Dict[str, any]] = []
    
    def push_topic(self, topic: str, context: Dict[str, any]) -> None:
        """
        Push a new topic onto the stack.
        
        Args:
            topic: Topic name/description
            context: Context information for this topic
        """
        self.topic_stack.append({
            "topic": topic,
            "context": context,
            "timestamp": datetime.now(),
        })
        logger.info(f"Pushed topic onto stack: {topic}")
    
    def pop_topic(self) -> Optional[Dict[str, any]]:
        """
        Pop the most recent topic from the stack.
        
        Returns:
            Topic information, or None if stack is empty
        """
        if self.topic_stack:
            topic = self.topic_stack.pop()
            logger.info(f"Popped topic from stack: {topic['topic']}")
            return topic
        return None
    
    def get_current_topic(self) -> Optional[Dict[str, any]]:
        """
        Get the current topic without removing it.
        
        Returns:
            Current topic information, or None if stack is empty
        """
        if self.topic_stack:
            return self.topic_stack[-1]
        return None
    
    def record_subtask(self, subtask: str, result: Dict[str, any]) -> None:
        """
        Record a completed subtask.
        
        Args:
            subtask: Subtask name/description
            result: Result information
        """
        self.subtask_history.append({
            "subtask": subtask,
            "result": result,
            "timestamp": datetime.now(),
        })
        logger.info(f"Recorded subtask: {subtask}")
    
    def get_subtask_history(self) -> List[Dict[str, any]]:
        """
        Get the history of completed subtasks.
        
        Returns:
            List of subtask records
        """
        return self.subtask_history.copy()


def maintain_context_on_transition(
    state: AgentState,
    from_agent: str,
    to_agent: str,
) -> AgentState:
    """
    Maintain conversation context during agent transitions.
    
    This function ensures smooth transitions by:
    1. Preserving all conversation history
    2. Adding a transition message if appropriate
    3. Maintaining user profile and task context
    
    Args:
        state: Current agent state
        from_agent: Name of the agent we're transitioning from
        to_agent: Name of the agent we're transitioning to
    
    Returns:
        Updated agent state with transition context
        
    Validates:
        - Requirements 9.1: Maintain conversation context throughout the session
        - Requirements 9.2: Provide smooth transitions when switching between agents
    """
    logger.info(f"Maintaining context on transition: {from_agent} -> {to_agent}")
    
    # All context is already maintained in the state object
    # Messages, user_profile, course_candidates, learning_plan are all preserved
    
    # Add a subtle transition message for certain transitions
    # This helps users understand what's happening
    transition_messages = {
        ("coordinator", "course_advisor"): "让我为您查找相关课程...",
        ("coordinator", "learning_planner"): "让我为您制定学习计划...",
        ("course_advisor", "coordinator"): None,  # No message needed
        ("learning_planner", "coordinator"): None,  # No message needed
        ("learning_planner", "human_input"): None,  # Plan already presented
        ("human_input", "coordinator"): None,  # Feedback already processed
    }
    
    # Get the transition message
    transition_key = (from_agent, to_agent)
    message = transition_messages.get(transition_key)
    
    # Add transition message if defined
    if message:
        state = add_message(
            state,
            role="assistant",
            content=message,
            agent="system",
        )
        logger.debug(f"Added transition message: {message}")
    
    # Log context preservation
    logger.debug(
        f"Context preserved: {len(state['messages'])} messages, "
        f"{len(state['course_candidates'])} courses, "
        f"learning_plan={'present' if state['learning_plan'] else 'absent'}"
    )
    
    return state


def extract_conversation_context(state: AgentState) -> Dict[str, any]:
    """
    Extract key context information from the conversation state.
    
    This provides a summary of the current conversation context that can be
    used by agents to understand the situation.
    
    Args:
        state: Current agent state
    
    Returns:
        Dictionary containing context summary
    """
    # Get recent messages (last 5)
    recent_messages = state["messages"][-5:] if len(state["messages"]) > 5 else state["messages"]
    
    # Extract user goals from profile
    user_goals = state["user_profile"].get("learning_goals", [])
    
    # Check if we have course recommendations
    has_courses = len(state["course_candidates"]) > 0
    
    # Check if we have a learning plan
    has_plan = state["learning_plan"] is not None
    plan_status = state["learning_plan"]["status"] if has_plan else None
    
    # Determine current phase
    if has_plan and plan_status == "approved":
        phase = "plan_execution"
    elif has_plan:
        phase = "plan_review"
    elif has_courses:
        phase = "course_selection"
    elif user_goals:
        phase = "goal_clarification"
    else:
        phase = "initial_inquiry"
    
    context = {
        "phase": phase,
        "recent_messages": [
            {
                "role": msg["role"],
                "content": msg["content"][:100],  # Truncate for brevity
                "agent": msg.get("agent"),
            }
            for msg in recent_messages
        ],
        "user_goals": user_goals,
        "has_courses": has_courses,
        "num_courses": len(state["course_candidates"]),
        "has_plan": has_plan,
        "plan_status": plan_status,
        "current_task": state.get("current_task"),
    }
    
    logger.debug(f"Extracted context: phase={phase}, task={state.get('current_task')}")
    
    return context


def build_context_summary_for_agent(
    state: AgentState,
    agent_name: str,
) -> str:
    """
    Build a context summary string for an agent.
    
    This creates a natural language summary of the conversation context
    that can be included in agent prompts.
    
    Args:
        state: Current agent state
        agent_name: Name of the agent receiving the context
    
    Returns:
        Context summary string
    """
    context = extract_conversation_context(state)
    
    # Build summary based on phase
    summary_parts = []
    
    # Add user goals if present
    if context["user_goals"]:
        goals_str = "、".join(context["user_goals"])
        summary_parts.append(f"用户的学习目标：{goals_str}")
    
    # Add user background if present
    if state["user_profile"].get("background"):
        summary_parts.append(f"用户背景：{state['user_profile']['background']}")
    
    # Add skill level if present
    if state["user_profile"].get("skill_level"):
        level_map = {
            "beginner": "初学者",
            "intermediate": "中级",
            "advanced": "高级",
        }
        level = level_map.get(state["user_profile"]["skill_level"], state["user_profile"]["skill_level"])
        summary_parts.append(f"技能水平：{level}")
    
    # Add course information if present
    if context["has_courses"]:
        summary_parts.append(f"已推荐 {context['num_courses']} 门课程")
    
    # Add plan information if present
    if context["has_plan"]:
        status_map = {
            "draft": "草稿",
            "approved": "已批准",
            "in_progress": "进行中",
        }
        status = status_map.get(context["plan_status"], context["plan_status"])
        summary_parts.append(f"学习计划状态：{status}")
    
    # Add current task if present
    if context["current_task"]:
        summary_parts.append(f"当前任务：{context['current_task']}")
    
    # Combine into summary
    if summary_parts:
        summary = "对话上下文：\n" + "\n".join(f"- {part}" for part in summary_parts)
    else:
        summary = "对话上下文：这是一个新的对话。"
    
    logger.debug(f"Built context summary for {agent_name}: {len(summary)} chars")
    
    return summary


def ensure_context_consistency(state: AgentState) -> tuple[bool, Optional[str]]:
    """
    Verify that conversation context is consistent.
    
    This checks for common consistency issues:
    - Learning plan references courses that don't exist in candidates
    - User profile has goals but no courses or plan
    - Conflicting task and agent states
    
    Args:
        state: Current agent state
    
    Returns:
        (is_consistent, issue_description) tuple
    """
    issues = []
    
    # Check if learning plan references valid courses
    if state["learning_plan"]:
        plan_courses = state["learning_plan"].get("recommended_courses", [])
        candidate_urls = {c["url"] for c in state["course_candidates"]}
        
        for plan_course in plan_courses:
            if plan_course.get("url") and plan_course["url"] not in candidate_urls:
                issues.append(
                    f"Learning plan references course not in candidates: {plan_course.get('title')}"
                )
    
    # Check if requires_human_input is consistent with next_agent
    if state["requires_human_input"] and state["next_agent"] != "human_input":
        issues.append(
            f"requires_human_input is True but next_agent is {state['next_agent']}"
        )
    
    # Check if is_complete is consistent with next_agent
    if state["is_complete"] and state["next_agent"] not in [None, "end"]:
        issues.append(
            f"is_complete is True but next_agent is {state['next_agent']}"
        )
    
    if issues:
        issue_str = "; ".join(issues)
        logger.warning(f"Context consistency issues: {issue_str}")
        return False, issue_str
    
    logger.debug("Context consistency check passed")
    return True, None


# ============================================================================
# Conversation Branching Support (Requirements 9.3, 9.4)
# ============================================================================


def detect_topic_switch(state: AgentState) -> Optional[str]:
    """
    Detect if the user is switching to a new topic.
    
    This analyzes the most recent user message to determine if they're
    changing the subject or returning to a previous topic.
    
    Args:
        state: Current agent state
    
    Returns:
        New topic description if detected, None otherwise
    """
    # Get the last user message
    user_messages = [msg for msg in state["messages"] if msg["role"] == "user"]
    
    if not user_messages:
        return None
    
    last_message = user_messages[-1]["content"].lower()
    
    # Keywords that indicate topic switching
    switch_keywords = [
        "换个话题",
        "另外",
        "还有",
        "对了",
        "顺便问一下",
        "我想问",
        "我还想",
        "by the way",
        "also",
        "another question",
    ]
    
    # Keywords that indicate returning to previous topic
    return_keywords = [
        "回到",
        "之前",
        "刚才",
        "前面",
        "earlier",
        "previous",
        "back to",
    ]
    
    # Check for topic switch
    for keyword in switch_keywords:
        if keyword in last_message:
            logger.info(f"Detected topic switch with keyword: {keyword}")
            return "new_topic"
    
    # Check for return to previous topic
    for keyword in return_keywords:
        if keyword in last_message:
            logger.info(f"Detected return to previous topic with keyword: {keyword}")
            return "previous_topic"
    
    return None


def handle_topic_switch(
    state: AgentState,
    new_topic: str,
) -> AgentState:
    """
    Handle a topic switch in the conversation.
    
    This function:
    1. Saves the current topic context
    2. Acknowledges the topic switch
    3. Prepares for the new topic
    
    Args:
        state: Current agent state
        new_topic: Description of the new topic
    
    Returns:
        Updated agent state
        
    Validates:
        - Requirements 9.3: Support conversation branching and returning to previous topics
    """
    logger.info(f"Handling topic switch to: {new_topic}")
    
    # Save current context in state metadata (using preferences as a simple store)
    current_context = extract_conversation_context(state)
    
    # Store in user preferences (this is a simple approach)
    if "conversation_stack" not in state["user_profile"]["preferences"]:
        state["user_profile"]["preferences"]["conversation_stack"] = []
    
    state["user_profile"]["preferences"]["conversation_stack"].append({
        "context": current_context,
        "timestamp": datetime.now().isoformat(),
    })
    
    # Acknowledge the topic switch
    state = add_message(
        state,
        role="assistant",
        content="好的，我明白了。让我们来讨论这个新话题。",
        agent="system",
    )
    
    # Clear current task to allow coordinator to reassess
    state["current_task"] = None
    state["next_agent"] = "coordinator"
    
    logger.debug(f"Topic switch handled, routing to coordinator")
    
    return state


def return_to_previous_topic(state: AgentState) -> AgentState:
    """
    Return to a previous topic in the conversation.
    
    This function:
    1. Retrieves the previous topic context
    2. Acknowledges the return
    3. Restores relevant context
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state
        
    Validates:
        - Requirements 9.3: Support conversation branching and returning to previous topics
    """
    logger.info("Attempting to return to previous topic")
    
    # Retrieve conversation stack
    conversation_stack = state["user_profile"]["preferences"].get("conversation_stack", [])
    
    if not conversation_stack:
        # No previous topic to return to
        state = add_message(
            state,
            role="assistant",
            content="我们还没有讨论过其他话题。您想讨论什么呢？",
            agent="system",
        )
        logger.debug("No previous topic found")
        return state
    
    # Pop the most recent previous context
    previous_context = conversation_stack.pop()
    state["user_profile"]["preferences"]["conversation_stack"] = conversation_stack
    
    # Acknowledge the return
    phase = previous_context["context"].get("phase", "unknown")
    phase_descriptions = {
        "plan_execution": "学习计划执行",
        "plan_review": "学习计划审核",
        "course_selection": "课程选择",
        "goal_clarification": "目标明确",
        "initial_inquiry": "初始咨询",
    }
    
    phase_desc = phase_descriptions.get(phase, "之前的话题")
    
    state = add_message(
        state,
        role="assistant",
        content=f"好的，让我们回到{phase_desc}。",
        agent="system",
    )
    
    # Restore task context if available
    if previous_context["context"].get("current_task"):
        state["current_task"] = previous_context["context"]["current_task"]
    
    # Route to coordinator to continue
    state["next_agent"] = "coordinator"
    
    logger.debug(f"Returned to previous topic: {phase}")
    
    return state


def summarize_subtask_completion(
    state: AgentState,
    subtask_name: str,
    subtask_result: Dict[str, any],
) -> AgentState:
    """
    Summarize the completion of a subtask before proceeding.
    
    This function:
    1. Creates a summary of what was accomplished
    2. Adds the summary to the conversation
    3. Prepares for the next step
    
    Args:
        state: Current agent state
        subtask_name: Name/description of the completed subtask
        subtask_result: Result information from the subtask
    
    Returns:
        Updated agent state with summary
        
    Validates:
        - Requirements 9.4: Summarize results before proceeding when a subtask is completed
    """
    logger.info(f"Summarizing subtask completion: {subtask_name}")
    
    # Build summary based on subtask type
    summary = ""
    
    if subtask_name == "course_search":
        num_courses = subtask_result.get("num_courses", 0)
        summary = (
            f"✓ 课程搜索完成：找到了 {num_courses} 门相关课程。\n"
            "您可以查看上述推荐，或告诉我您的反馈。"
        )
    
    elif subtask_name == "learning_plan_creation":
        num_milestones = len(subtask_result.get("milestones", []))
        duration = subtask_result.get("estimated_duration", "未知")
        summary = (
            f"✓ 学习计划制定完成：包含 {num_milestones} 个里程碑，"
            f"预计学习时长 {duration}。\n"
            "请查看上述计划并告诉我您的意见。"
        )
    
    elif subtask_name == "plan_approval":
        status = subtask_result.get("status", "unknown")
        if status == "approved":
            summary = (
                "✓ 学习计划已确认。\n"
                "接下来我会继续协助您执行这个计划。"
            )
        else:
            summary = (
                "✓ 已收到您的反馈。\n"
                "让我根据您的建议调整计划。"
            )
    
    elif subtask_name == "course_recommendation_feedback":
        feedback_type = subtask_result.get("feedback_type", "general")
        if feedback_type == "satisfied":
            summary = (
                "✓ 很高兴您对推荐满意。\n"
                "如果需要制定学习计划或有其他问题，请告诉我。"
            )
        elif feedback_type == "more":
            summary = (
                "✓ 收到，让我为您寻找更多课程。"
            )
        else:
            summary = (
                "✓ 已收到您的反馈。\n"
                "让我根据您的需求调整推荐。"
            )
    
    else:
        # Generic summary
        summary = f"✓ {subtask_name} 已完成。"
    
    # Add summary message
    state = add_message(
        state,
        role="assistant",
        content=summary,
        agent="system",
    )
    
    logger.debug(f"Added subtask summary: {summary[:50]}...")
    
    return state


def create_conversation_summary(state: AgentState) -> str:
    """
    Create a summary of the entire conversation so far.
    
    This is useful for:
    - Providing context to new agents
    - Helping users understand progress
    - Debugging conversation flow
    
    Args:
        state: Current agent state
    
    Returns:
        Conversation summary string
    """
    summary_parts = []
    
    # Add conversation metadata
    summary_parts.append(f"对话 ID: {state['conversation_id']}")
    summary_parts.append(f"消息数量: {len(state['messages'])}")
    summary_parts.append(f"循环计数: {state['loop_count']}")
    
    # Add user information
    user_profile = state["user_profile"]
    if user_profile.get("learning_goals"):
        goals = "、".join(user_profile["learning_goals"])
        summary_parts.append(f"学习目标: {goals}")
    
    if user_profile.get("skill_level"):
        summary_parts.append(f"技能水平: {user_profile['skill_level']}")
    
    # Add progress information
    if state["course_candidates"]:
        summary_parts.append(f"推荐课程: {len(state['course_candidates'])} 门")
    
    if state["learning_plan"]:
        plan_status = state["learning_plan"]["status"]
        num_milestones = len(state["learning_plan"]["milestones"])
        summary_parts.append(
            f"学习计划: {plan_status} ({num_milestones} 个里程碑)"
        )
    
    # Add current state
    if state["current_task"]:
        summary_parts.append(f"当前任务: {state['current_task']}")
    
    if state["next_agent"]:
        summary_parts.append(f"下一个智能体: {state['next_agent']}")
    
    # Combine into summary
    summary = "\n".join(summary_parts)
    
    logger.debug(f"Created conversation summary: {len(summary)} chars")
    
    return summary


def check_conversation_health(state: AgentState) -> Dict[str, any]:
    """
    Check the health of the conversation flow.
    
    This identifies potential issues:
    - Excessive loop count
    - Stalled conversation (no progress)
    - Missing expected data
    
    Args:
        state: Current agent state
    
    Returns:
        Health check results dictionary
    """
    issues = []
    warnings = []
    
    # Check loop count
    if state["loop_count"] > 8:
        warnings.append(f"High loop count: {state['loop_count']}")
    
    if state["loop_count"] > 10:
        issues.append(f"Loop count exceeded limit: {state['loop_count']}")
    
    # Check for stalled conversation
    if len(state["messages"]) > 10:
        # Check if we have made progress
        has_courses = len(state["course_candidates"]) > 0
        has_plan = state["learning_plan"] is not None
        
        if not has_courses and not has_plan:
            warnings.append("No progress: no courses or plan after 10+ messages")
    
    # Check for missing user goals
    if len(state["messages"]) > 3 and not state["user_profile"]["learning_goals"]:
        warnings.append("User goals not captured after 3+ messages")
    
    # Check for inconsistent state
    is_consistent, consistency_issue = ensure_context_consistency(state)
    if not is_consistent:
        issues.append(f"Context inconsistency: {consistency_issue}")
    
    # Determine overall health
    if issues:
        health = "unhealthy"
    elif warnings:
        health = "warning"
    else:
        health = "healthy"
    
    result = {
        "health": health,
        "issues": issues,
        "warnings": warnings,
        "loop_count": state["loop_count"],
        "message_count": len(state["messages"]),
    }
    
    logger.debug(f"Conversation health check: {health}")
    
    return result

