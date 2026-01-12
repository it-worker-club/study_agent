"""LangGraph graph builder for the education tutoring system.

This module constructs the StateGraph that orchestrates the multi-agent
conversation flow. The graph uses a Supervisor pattern where the coordinator
agent routes tasks to specialized agents (course advisor and learning planner).

The graph structure:
    entry -> coordinator -> [course_advisor | learning_planner | human_input | end]
    
All specialized agents route back to the coordinator for next decision.
"""

import asyncio
from typing import Optional

from langgraph.graph import END, StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver

from ..graph.helpers import route_next
from ..graph.nodes import (
    coordinator_node,
    course_advisor_node,
    entry_node,
    human_input_node,
    learning_planner_node,
    end_node,
)
from ..graph.state import AgentState
from ..utils.logger import get_logger


logger = get_logger(__name__)


def create_graph(
    checkpointer: Optional[BaseCheckpointSaver] = None,
    max_loop_count: int = 10,
) -> StateGraph:
    """
    Create and compile the LangGraph StateGraph for the education tutoring system.
    
    This function builds a graph with the following structure:
    
    1. Entry node: Initializes the conversation
    2. Coordinator node: Analyzes intent and makes routing decisions
    3. Course Advisor node: Searches and recommends courses
    4. Learning Planner node: Creates personalized learning plans
    5. Human Input node: Handles user feedback and approvals
    6. End node: Finalizes the conversation
    
    The graph uses conditional routing based on the coordinator's decisions
    and state conditions (loop count, human input requirements, completion status).
    
    Args:
        checkpointer: Optional checkpoint saver for conversation persistence.
                     If provided, enables conversation history and state recovery.
        max_loop_count: Maximum number of routing loops before forcing termination.
                       Default is 10 to prevent infinite loops.
    
    Returns:
        Compiled StateGraph ready for execution
        
    Validates:
        - Requirements 2.1: Use LangGraph StateGraph to manage application state
        - Requirements 5.2: Support conditional routing based on conversation state
        - Requirements 9.5: Detect and handle conversation loops
        
    Example:
        >>> from langgraph.checkpoint.sqlite import SqliteSaver
        >>> checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
        >>> graph = create_graph(checkpointer=checkpointer)
        >>> result = graph.invoke(initial_state, config={"configurable": {"thread_id": "123"}})
    """
    logger.info("Creating LangGraph StateGraph...")
    
    # Create the StateGraph with AgentState as the state schema
    # This ensures type safety and proper state management
    workflow = StateGraph(AgentState)
    
    # Add all nodes to the graph
    # Each node is a function that takes AgentState and returns updated AgentState
    logger.debug("Adding nodes to graph...")
    
    # Entry node - first node executed, initializes conversation
    workflow.add_node("entry", entry_node)
    
    # Coordinator node - analyzes intent and makes routing decisions
    workflow.add_node("coordinator", coordinator_node)
    
    # Course Advisor node - searches and recommends courses
    workflow.add_node("course_advisor", course_advisor_node)
    
    # Learning Planner node - creates personalized learning plans
    workflow.add_node("learning_planner", learning_planner_node)
    
    # Human Input node - handles user feedback and approvals
    workflow.add_node("human_input", human_input_node)
    
    # End node - finalizes conversation
    workflow.add_node("end", end_node)
    
    logger.debug("All nodes added successfully")
    
    # Define edges between nodes
    logger.debug("Defining edges...")
    
    # Set entry point - the first node to execute
    workflow.set_entry_point("entry")
    
    # Entry always routes to coordinator
    workflow.add_edge("entry", "coordinator")
    
    # Coordinator uses conditional routing based on state
    # The route_next function examines state and returns the next node name
    workflow.add_conditional_edges(
        "coordinator",
        lambda state: route_next(state, max_loop_count=max_loop_count),
        {
            "coordinator": "coordinator",  # Loop back for clarification
            "course_advisor": "course_advisor",
            "learning_planner": "learning_planner",
            "human_input": "human_input",
            "end": "end",
        },
    )
    
    # Course Advisor always routes back to coordinator for next decision
    workflow.add_edge("course_advisor", "coordinator")
    
    # Learning Planner always routes back to coordinator for next decision
    workflow.add_edge("learning_planner", "coordinator")
    
    # Human Input always routes back to coordinator after processing feedback
    workflow.add_edge("human_input", "coordinator")
    
    # End node terminates the graph
    workflow.add_edge("end", END)
    
    logger.debug("All edges defined successfully")
    
    # Compile the graph
    logger.info("Compiling graph...")
    
    if checkpointer:
        logger.info("Compiling with checkpointer for conversation persistence")
        compiled_graph = workflow.compile(checkpointer=checkpointer)
    else:
        logger.info("Compiling without checkpointer (no persistence)")
        compiled_graph = workflow.compile()
    
    logger.info("Graph compiled successfully")
    
    return compiled_graph


def create_graph_with_config(
    config,
    checkpointer: Optional[BaseCheckpointSaver] = None,
) -> StateGraph:
    """
    Create graph using system configuration.
    
    This is a convenience function that extracts relevant settings from
    the system configuration and passes them to create_graph().
    
    Args:
        config: System configuration object
        checkpointer: Optional checkpoint saver for conversation persistence
    
    Returns:
        Compiled StateGraph ready for execution
    """
    max_loop_count = getattr(config.system, "max_loop_count", 10)
    
    return create_graph(
        checkpointer=checkpointer,
        max_loop_count=max_loop_count,
    )


async def create_graph_with_persistence(
    database_path: str,
    max_loop_count: int = 10,
) -> StateGraph:
    """
    Create graph with database persistence enabled.
    
    This function initializes the database, creates a checkpointer,
    and builds a graph with full conversation persistence.
    
    Args:
        database_path: Path to SQLite database file
        max_loop_count: Maximum number of routing loops
    
    Returns:
        Compiled StateGraph with persistence enabled
        
    Example:
        >>> graph = await create_graph_with_persistence("./data/tutoring.db")
        >>> result = await graph.ainvoke(
        ...     initial_state,
        ...     config={"configurable": {"thread_id": "user_123"}}
        ... )
    """
    from ..memory.checkpointer import get_checkpointer
    from ..memory.database import init_database
    
    logger.info(f"Creating graph with persistence at {database_path}")
    
    # Initialize database schema
    init_database(database_path)
    
    # Create checkpointer
    checkpointer = await get_checkpointer(database_path)
    
    # Create and return graph with checkpointer
    return create_graph(
        checkpointer=checkpointer,
        max_loop_count=max_loop_count,
    )

