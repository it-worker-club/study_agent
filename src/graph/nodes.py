"""Node functions for the LangGraph state machine.

This module contains the node functions that are executed by LangGraph.
Each node function takes an AgentState and returns an updated AgentState.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from ..graph.helpers import add_message, increment_loop_count
from ..graph.state import AgentState
from ..graph.conversation_flow import (
    maintain_context_on_transition,
    summarize_subtask_completion,
    detect_topic_switch,
    handle_topic_switch,
    return_to_previous_topic,
)
from ..llm.vllm_client import VLLMClient, VLLMClientError
from ..utils.config import Config
from ..utils.logger import get_logger

if TYPE_CHECKING:
    from ..agents.coordinator import CoordinatorAgent
    from ..agents.course_advisor import CourseAdvisorAgent
    from ..agents.learning_planner import LearningPlannerAgent
    from ..tools.mcp_playwright import MCPPlaywrightClient, MCPPlaywrightError
    from ..tools.web_search import WebSearchClient, WebSearchError
    from ..utils.error_handler import ErrorHandler


logger = get_logger(__name__)


# Global agent instances (will be initialized by the application)
_coordinator_agent: Optional["CoordinatorAgent"] = None
_course_advisor_agent: Optional["CourseAdvisorAgent"] = None
_learning_planner_agent: Optional["LearningPlannerAgent"] = None
_vllm_client: Optional[VLLMClient] = None
_mcp_client: Optional["MCPPlaywrightClient"] = None
_web_search_client: Optional["WebSearchClient"] = None


def initialize_agents(config: Config, vllm_client: VLLMClient) -> None:
    """
    Initialize agent instances.
    
    This should be called once at application startup before using any node functions.
    
    Args:
        config: System configuration
        vllm_client: Initialized vLLM client
    """
    global _coordinator_agent, _course_advisor_agent, _learning_planner_agent, _vllm_client, _mcp_client, _web_search_client
    
    # Import here to avoid circular import
    from ..agents.coordinator import CoordinatorAgent
    from ..agents.course_advisor import CourseAdvisorAgent
    from ..agents.learning_planner import LearningPlannerAgent
    from ..tools.mcp_playwright import create_mcp_playwright_client
    from ..tools.web_search import create_web_search_client
    
    _vllm_client = vllm_client
    
    # Initialize tool clients
    _mcp_client = create_mcp_playwright_client(config.mcp)
    _web_search_client = create_web_search_client(config.web_search)
    
    # Initialize agents
    _coordinator_agent = CoordinatorAgent(
        vllm_client=vllm_client,
        config=config.agents.coordinator,
    )
    
    _course_advisor_agent = CourseAdvisorAgent(
        vllm_client=vllm_client,
        mcp_client=_mcp_client,
        web_search_client=_web_search_client,
        config=config.agents.course_advisor,
    )
    
    _learning_planner_agent = LearningPlannerAgent(
        vllm_client=vllm_client,
        web_search_client=_web_search_client,
        config=config.agents.learning_planner,
    )
    
    logger.info("Initialized all agent instances")


def coordinator_node(state: AgentState) -> AgentState:
    """
    Coordinator node function.
    
    This node:
    1. Analyzes user intent using the coordinator agent
    2. Makes routing decisions
    3. Updates state with next_agent and current_task
    4. Optionally adds a response message to the user
    5. Detects and handles topic switches
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state with routing decision
    """
    logger.info(f"Executing coordinator_node for conversation {state['conversation_id']}")
    
    # Import here to avoid circular import
    from ..utils.error_handler import ErrorHandler
    
    # Check if coordinator agent is initialized
    if _coordinator_agent is None:
        logger.error("Coordinator agent not initialized")
        return ErrorHandler.handle_generic_error(
            Exception("Coordinator agent not initialized"),
            state,
            context="coordinator_node",
        )
    
    try:
        # Increment loop count to prevent infinite loops
        state = increment_loop_count(state)
        
        # Check loop count limit
        max_loop_count = 10  # TODO: Get from config
        if state["loop_count"] > max_loop_count:
            logger.warning(
                f"Loop count exceeded limit ({max_loop_count}) for conversation "
                f"{state['conversation_id']}"
            )
            state["next_agent"] = "end"
            state["is_complete"] = True
            state = add_message(
                state,
                role="assistant",
                content="对话已达到最大轮次限制。如需继续，请开始新的对话。",
                agent="system",
            )
            return state
        
        # Detect topic switches
        topic_switch = detect_topic_switch(state)
        
        if topic_switch == "new_topic":
            # Handle new topic
            state = handle_topic_switch(state, "new_topic")
            # Continue with normal routing
        elif topic_switch == "previous_topic":
            # Return to previous topic
            state = return_to_previous_topic(state)
            # The function already sets next_agent to coordinator
            return state
        
        # Analyze intent and make routing decision
        # Note: We need to run this synchronously in the node function
        # In a real implementation, you might need to handle async properly
        import asyncio
        
        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function
        decision = loop.run_until_complete(_coordinator_agent.analyze_and_route(state))
        
        # Update state with routing decision
        from_agent = "coordinator"
        to_agent = decision["next_agent"]
        
        state["next_agent"] = to_agent
        state["current_task"] = decision["current_task"]
        state["requires_human_input"] = decision.get("requires_human_input", False)
        
        # Add response message if provided
        if decision.get("response"):
            state = add_message(
                state,
                role="assistant",
                content=decision["response"],
                agent="coordinator",
            )
        
        # Maintain context on transition
        if to_agent and to_agent != "coordinator":
            state = maintain_context_on_transition(state, from_agent, to_agent)
        
        logger.info(
            f"Coordinator decision: next_agent={state['next_agent']}, "
            f"task={state['current_task']}, "
            f"requires_human_input={state['requires_human_input']}"
        )
        
        return state
    
    except VLLMClientError as e:
        logger.error(f"LLM error in coordinator_node: {e}")
        return ErrorHandler.handle_llm_error(e, state)
    
    except Exception as e:
        logger.error(f"Unexpected error in coordinator_node: {e}")
        return ErrorHandler.handle_routing_error(e, state)


def course_advisor_node(state: AgentState) -> AgentState:
    """
    Course advisor node function.
    
    This node:
    1. Uses MCP Playwright to search GeekTime courses
    2. Uses web search to find supplementary resources
    3. Analyzes user needs and recommends courses
    4. Updates state with course_candidates
    5. Adds recommendation message to conversation
    6. Summarizes the subtask completion
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state with course recommendations
    """
    logger.info(f"Executing course_advisor_node for conversation {state['conversation_id']}")
    
    # Import here to avoid circular import
    from ..utils.error_handler import ErrorHandler
    from ..tools.mcp_playwright import MCPPlaywrightError
    from ..tools.web_search import WebSearchError
    
    # Check if course advisor agent is initialized
    if _course_advisor_agent is None:
        logger.error("Course advisor agent not initialized")
        return ErrorHandler.handle_generic_error(
            Exception("Course advisor agent not initialized"),
            state,
            context="course_advisor_node",
        )
    
    try:
        # Get or create event loop for async operations
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Get course recommendations
        result = loop.run_until_complete(_course_advisor_agent.recommend_courses(state))
        
        # Update state with course candidates
        state["course_candidates"] = result["courses"]
        
        # Add recommendation message
        state = add_message(
            state,
            role="assistant",
            content=result["response"],
            agent="course_advisor",
        )
        
        # Summarize subtask completion
        state = summarize_subtask_completion(
            state,
            subtask_name="course_search",
            subtask_result={
                "num_courses": len(result["courses"]),
                "num_web_resources": len(result.get("web_resources", [])),
            },
        )
        
        # Maintain context on transition back to coordinator
        state = maintain_context_on_transition(state, "course_advisor", "coordinator")
        
        # Route back to coordinator for next decision
        state["next_agent"] = "coordinator"
        
        logger.info(
            f"Course advisor completed: found {len(result['courses'])} courses, "
            f"{len(result.get('web_resources', []))} web resources"
        )
        
        return state
    
    except VLLMClientError as e:
        logger.error(f"LLM error in course_advisor_node: {e}")
        return ErrorHandler.handle_llm_error(e, state)
    
    except (MCPPlaywrightError, WebSearchError) as e:
        logger.error(f"Tool error in course_advisor_node: {e}")
        return ErrorHandler.handle_tool_error(e, "course_search", state)
    
    except Exception as e:
        logger.error(f"Unexpected error in course_advisor_node: {e}")
        return ErrorHandler.handle_generic_error(e, state, context="course_advisor_node")


def learning_planner_node(state: AgentState) -> AgentState:
    """
    Learning planner node function.
    
    This node:
    1. Searches for learning paths and best practices using web search
    2. Analyzes user goals, skill level, and available time
    3. Creates a structured learning plan with milestones
    4. Incorporates recommended courses into the plan
    5. Updates state with learning_plan
    6. Adds plan summary message to conversation
    7. Summarizes the subtask completion
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state with learning plan
    """
    logger.info(f"Executing learning_planner_node for conversation {state['conversation_id']}")
    
    # Import here to avoid circular import
    from ..utils.error_handler import ErrorHandler
    from ..tools.web_search import WebSearchError
    
    # Check if learning planner agent is initialized
    if _learning_planner_agent is None:
        logger.error("Learning planner agent not initialized")
        return ErrorHandler.handle_generic_error(
            Exception("Learning planner agent not initialized"),
            state,
            context="learning_planner_node",
        )
    
    try:
        # Get or create event loop for async operations
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Create learning plan
        result = loop.run_until_complete(_learning_planner_agent.create_learning_plan(state))
        
        # Update state with learning plan
        state["learning_plan"] = result["learning_plan"]
        
        # Add plan summary message
        state = add_message(
            state,
            role="assistant",
            content=result["response"],
            agent="learning_planner",
        )
        
        # Summarize subtask completion
        state = summarize_subtask_completion(
            state,
            subtask_name="learning_plan_creation",
            subtask_result={
                "milestones": result["learning_plan"]["milestones"],
                "estimated_duration": result["learning_plan"]["estimated_duration"],
            },
        )
        
        # Maintain context on transition to human input
        state = maintain_context_on_transition(state, "learning_planner", "human_input")
        
        # Mark that human input is required for plan approval
        state["requires_human_input"] = True
        state["next_agent"] = "human_input"
        
        logger.info(
            f"Learning planner completed: created plan with "
            f"{len(result['learning_plan']['milestones'])} milestones, "
            f"estimated duration: {result['learning_plan']['estimated_duration']}"
        )
        
        return state
    
    except VLLMClientError as e:
        logger.error(f"LLM error in learning_planner_node: {e}")
        return ErrorHandler.handle_llm_error(e, state)
    
    except WebSearchError as e:
        logger.error(f"Web search error in learning_planner_node: {e}")
        return ErrorHandler.handle_tool_error(e, "web_search", state)
    
    except Exception as e:
        logger.error(f"Unexpected error in learning_planner_node: {e}")
        return ErrorHandler.handle_generic_error(e, state, context="learning_planner_node")


def human_input_node(state: AgentState) -> AgentState:
    """
    Human input node function.
    
    This node handles human-in-the-loop interaction by:
    1. Checking if there's pending human feedback in the state
    2. Processing the feedback and updating relevant state fields
    3. Routing back to the coordinator for next steps
    
    The actual user input collection happens at the application layer (UI/API).
    This node processes the feedback that has been placed in state["human_feedback"].
    
    If no feedback is present yet, the node will prompt for input and wait.
    The application layer should:
    1. Detect that requires_human_input is True
    2. Pause execution and collect user input
    3. Place the input in state["human_feedback"]
    4. Resume execution of this node
    
    Args:
        state: Current agent state with human_feedback field
    
    Returns:
        Updated agent state with processed feedback
        
    Validates:
        - Requirements 6.1: Present learning plans for user approval
        - Requirements 6.2: Allow user feedback on course recommendations
        - Requirements 6.3: Support user interruption at any point
    """
    logger.info(f"Executing human_input_node for conversation {state['conversation_id']}")
    
    # Check if we have human feedback to process
    human_feedback = state.get("human_feedback")
    
    if not human_feedback or human_feedback.strip() == "":
        # No feedback yet - this means we're waiting for user input
        # Add a prompt message if not already present
        last_message = state["messages"][-1] if state["messages"] else None
        
        # Determine what we're waiting for based on context
        if state.get("learning_plan") and state["learning_plan"].get("status") == "draft":
            # Waiting for learning plan approval
            prompt = (
                "我已经为您制定了学习计划。请查看上述计划并提供反馈：\n"
                "- 如果您同意该计划，请回复「同意」或「批准」\n"
                "- 如果需要调整，请告诉我您的具体建议\n"
                "- 如果想重新规划，请回复「重新规划」"
            )
        elif state.get("course_candidates") and len(state["course_candidates"]) > 0:
            # Waiting for course recommendation feedback
            prompt = (
                "我已经为您推荐了一些课程。请提供您的反馈：\n"
                "- 如果您对推荐满意，请回复「满意」\n"
                "- 如果需要更多课程，请回复「更多推荐」\n"
                "- 如果想调整推荐方向，请告诉我您的具体需求"
            )
        else:
            # General feedback request
            prompt = "请提供您的反馈或确认，以便我继续为您服务。"
        
        # Only add prompt if the last message isn't already a prompt
        if not last_message or last_message.get("content") != prompt:
            state = add_message(
                state,
                role="assistant",
                content=prompt,
                agent="system",
            )
        
        # Keep requires_human_input as True so the application knows to wait
        # The node will be called again after feedback is provided
        logger.info("Waiting for human feedback")
        return state
    
    # We have feedback - process it
    logger.info(f"Processing human feedback: {human_feedback[:100]}...")
    
    # Add the user's feedback as a message
    state = add_message(
        state,
        role="user",
        content=human_feedback,
        agent=None,
    )
    
    # Process feedback based on context
    feedback_lower = human_feedback.lower().strip()
    
    # Check if this is learning plan approval
    if state.get("learning_plan") and state["learning_plan"].get("status") == "draft":
        if any(keyword in feedback_lower for keyword in ["同意", "批准", "确认", "好的", "可以", "approve", "yes"]):
            # User approved the plan
            state["learning_plan"]["status"] = "approved"
            
            # Summarize the approval
            state = summarize_subtask_completion(
                state,
                subtask_name="plan_approval",
                subtask_result={"status": "approved"},
            )
            
            logger.info("Learning plan approved by user")
            
        elif any(keyword in feedback_lower for keyword in ["重新", "不同", "修改", "调整", "redo", "change"]):
            # User wants to revise the plan
            state["learning_plan"]["status"] = "draft"  # Keep as draft
            state["current_task"] = "revise_learning_plan"
            
            response = "好的，我会根据您的反馈调整学习计划。请告诉我您希望如何调整？"
            state = add_message(
                state,
                role="assistant",
                content=response,
                agent="system",
            )
            
            logger.info("User requested learning plan revision")
            
        else:
            # User provided specific feedback - treat as adjustment request
            state["current_task"] = "adjust_learning_plan_with_feedback"
            
            response = "我理解了您的反馈。让我根据您的建议调整学习计划。"
            state = add_message(
                state,
                role="assistant",
                content=response,
                agent="system",
            )
            
            logger.info("User provided specific feedback on learning plan")
    
    # Check if this is course recommendation feedback
    elif state.get("course_candidates") and len(state["course_candidates"]) > 0:
        # Check for "more" request first (higher priority)
        if any(keyword in feedback_lower for keyword in ["更多", "其他", "别的", "再推荐", "more", "other"]):
            # User wants more recommendations
            state["current_task"] = "find_more_courses"
            
            # Summarize feedback
            state = summarize_subtask_completion(
                state,
                subtask_name="course_recommendation_feedback",
                subtask_result={"feedback_type": "more"},
            )
            
            logger.info("User requested more course recommendations")
            
        elif any(keyword in feedback_lower for keyword in ["满意", "好的", "可以", "不错", "satisfied", "good"]):
            # User is satisfied with recommendations
            # Summarize feedback
            state = summarize_subtask_completion(
                state,
                subtask_name="course_recommendation_feedback",
                subtask_result={"feedback_type": "satisfied"},
            )
            
            logger.info("User satisfied with course recommendations")
            
        else:
            # User provided specific feedback - adjust recommendations
            state["current_task"] = "adjust_course_recommendations"
            
            # Summarize feedback
            state = summarize_subtask_completion(
                state,
                subtask_name="course_recommendation_feedback",
                subtask_result={"feedback_type": "adjust"},
            )
            
            logger.info("User provided specific feedback on course recommendations")
    
    else:
        # General feedback - let coordinator handle it
        response = "感谢您的反馈。让我继续为您服务。"
        state = add_message(
            state,
            role="assistant",
            content=response,
            agent="system",
        )
        
        logger.info("Processed general user feedback")
    
    # Clear the human input request flags
    state["requires_human_input"] = False
    state["human_feedback"] = None
    
    # Maintain context on transition back to coordinator
    state = maintain_context_on_transition(state, "human_input", "coordinator")
    
    # Route back to coordinator for next decision
    state["next_agent"] = "coordinator"
    
    logger.info(
        f"Human input processed, routing to coordinator with task: {state.get('current_task')}"
    )
    
    return state


def entry_node(state: AgentState) -> AgentState:
    """
    Entry node function.
    
    This is the first node executed in the graph. It performs initial setup
    and routes to the coordinator.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state
    """
    logger.info(f"Executing entry_node for conversation {state['conversation_id']}")
    
    # Set next agent to coordinator
    state["next_agent"] = "coordinator"
    
    # Reset loop count at entry
    state["loop_count"] = 0
    
    return state


def end_node(state: AgentState) -> AgentState:
    """
    End node function.
    
    This is the final node in the graph. It marks the conversation as complete.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated agent state
    """
    logger.info(f"Executing end_node for conversation {state['conversation_id']}")
    
    # Mark conversation as complete
    state["is_complete"] = True
    state["next_agent"] = None
    
    # Add farewell message if not already present
    if not state["messages"] or "再见" not in state["messages"][-1]["content"]:
        state = add_message(
            state,
            role="assistant",
            content="感谢您的使用！如有其他问题，欢迎随时回来。",
            agent="system",
        )
    
    return state
