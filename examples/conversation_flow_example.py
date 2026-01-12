"""Example demonstrating conversation flow control.

This example shows how to:
1. Maintain context during agent transitions
2. Handle topic switching and branching
3. Summarize subtask completions
4. Check conversation health
"""

from datetime import datetime

from src.graph.state import AgentState
from src.graph.helpers import create_initial_state, add_message
from src.graph.conversation_flow import (
    maintain_context_on_transition,
    extract_conversation_context,
    build_context_summary_for_agent,
    ensure_context_consistency,
    detect_topic_switch,
    handle_topic_switch,
    return_to_previous_topic,
    summarize_subtask_completion,
    create_conversation_summary,
    check_conversation_health,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_state_info(state: AgentState):
    """Print key state information."""
    print(f"Conversation ID: {state['conversation_id']}")
    print(f"Messages: {len(state['messages'])}")
    print(f"Loop Count: {state['loop_count']}")
    print(f"Current Task: {state.get('current_task')}")
    print(f"Next Agent: {state.get('next_agent')}")
    print(f"Courses: {len(state['course_candidates'])}")
    print(f"Has Plan: {state['learning_plan'] is not None}")


def example_context_maintenance():
    """Example: Context maintenance during agent transitions."""
    print_section("Example 1: Context Maintenance")
    
    # Create initial state
    state = create_initial_state()
    
    # Add user information
    state["user_profile"]["background"] = "Software Engineer"
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["learning_goals"] = ["Learn Python", "Build APIs"]
    
    # Add some messages
    state = add_message(state, "user", "我想学习Python和API开发", None)
    state = add_message(state, "assistant", "好的，让我为您推荐相关课程", "coordinator")
    
    # Add some course candidates
    state["course_candidates"] = [
        {
            "title": "Python 核心技术与实战",
            "url": "https://time.geekbang.org/column/intro/100026901",
            "description": "深入学习Python核心技术",
            "difficulty": "intermediate",
            "duration": "20小时",
            "rating": 4.8,
            "source": "geektime",
        },
        {
            "title": "Python Web开发实战",
            "url": "https://time.geekbang.org/column/intro/100027001",
            "description": "使用Flask和Django构建Web应用",
            "difficulty": "intermediate",
            "duration": "15小时",
            "rating": 4.6,
            "source": "geektime",
        },
    ]
    
    print("Initial state:")
    print_state_info(state)
    
    # Transition from coordinator to course_advisor
    print("\n--- Transitioning: coordinator -> course_advisor ---")
    state = maintain_context_on_transition(state, "coordinator", "course_advisor")
    
    print("\nAfter transition:")
    print_state_info(state)
    
    # Verify context is maintained
    print("\n✓ Context maintained:")
    print(f"  - User goals: {state['user_profile']['learning_goals']}")
    print(f"  - Skill level: {state['user_profile']['skill_level']}")
    print(f"  - Courses: {len(state['course_candidates'])} preserved")
    print(f"  - Messages: {len(state['messages'])} (transition message added)")


def example_context_extraction():
    """Example: Extracting and summarizing conversation context."""
    print_section("Example 2: Context Extraction and Summarization")
    
    # Create state with rich context
    state = create_initial_state()
    state["user_profile"]["learning_goals"] = ["Learn Python", "Build REST APIs"]
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["background"] = "5 years Java experience"
    
    state = add_message(state, "user", "我想学习Python", None)
    state = add_message(state, "assistant", "好的，让我为您推荐课程", "coordinator")
    
    state["course_candidates"] = [
        {
            "title": "Python Course",
            "url": "https://example.com/python",
            "description": "Learn Python",
            "difficulty": "intermediate",
            "source": "geektime",
        }
    ]
    
    # Extract context
    context = extract_conversation_context(state)
    
    print("Extracted context:")
    print(f"  Phase: {context['phase']}")
    print(f"  User goals: {context['user_goals']}")
    print(f"  Has courses: {context['has_courses']}")
    print(f"  Number of courses: {context['num_courses']}")
    print(f"  Current task: {context['current_task']}")
    
    # Build context summary for agent
    summary = build_context_summary_for_agent(state, "course_advisor")
    
    print("\nContext summary for course_advisor:")
    print(summary)
    
    # Check consistency
    is_consistent, issue = ensure_context_consistency(state)
    print(f"\n✓ Context consistency: {is_consistent}")
    if not is_consistent:
        print(f"  Issue: {issue}")


def example_topic_switching():
    """Example: Handling topic switches and branching."""
    print_section("Example 3: Topic Switching and Branching")
    
    # Create state with ongoing conversation
    state = create_initial_state()
    state["user_profile"]["learning_goals"] = ["Learn Python"]
    state["current_task"] = "course_search"
    
    state = add_message(state, "user", "我想学习Python", None)
    state = add_message(state, "assistant", "好的，让我为您推荐Python课程", "coordinator")
    
    state["course_candidates"] = [
        {
            "title": "Python Course",
            "url": "https://example.com/python",
            "description": "Learn Python",
            "difficulty": "beginner",
            "source": "geektime",
        }
    ]
    
    print("Current conversation:")
    print_state_info(state)
    
    # User switches topic
    print("\n--- User switches topic ---")
    state = add_message(state, "user", "换个话题，我想问问Java的课程", None)
    
    # Detect topic switch
    topic_switch = detect_topic_switch(state)
    print(f"Topic switch detected: {topic_switch}")
    
    if topic_switch == "new_topic":
        # Handle topic switch
        state = handle_topic_switch(state, "new_topic")
        
        print("\nAfter handling topic switch:")
        print_state_info(state)
        print(f"✓ Previous context saved in conversation stack")
        print(f"✓ Routed to coordinator for new topic")
    
    # Later, user wants to return to previous topic
    print("\n--- User returns to previous topic ---")
    state = add_message(state, "user", "回到之前的Python课程讨论", None)
    
    topic_switch = detect_topic_switch(state)
    print(f"Topic switch detected: {topic_switch}")
    
    if topic_switch == "previous_topic":
        # Return to previous topic
        state = return_to_previous_topic(state)
        
        print("\nAfter returning to previous topic:")
        print_state_info(state)
        print(f"✓ Previous context restored")
        print(f"✓ Task: {state.get('current_task')}")


def example_subtask_summarization():
    """Example: Summarizing subtask completions."""
    print_section("Example 4: Subtask Summarization")
    
    state = create_initial_state()
    
    # Summarize course search completion
    print("--- Course search completed ---")
    state = summarize_subtask_completion(
        state,
        subtask_name="course_search",
        subtask_result={
            "num_courses": 5,
            "num_web_resources": 3,
        },
    )
    
    print(f"Summary added: {state['messages'][-1]['content']}")
    
    # Summarize learning plan creation
    print("\n--- Learning plan created ---")
    state = summarize_subtask_completion(
        state,
        subtask_name="learning_plan_creation",
        subtask_result={
            "milestones": [
                {"name": "Python Basics"},
                {"name": "Web Development"},
                {"name": "API Development"},
            ],
            "estimated_duration": "3 months",
        },
    )
    
    print(f"Summary added: {state['messages'][-1]['content']}")
    
    # Summarize plan approval
    print("\n--- Plan approved ---")
    state = summarize_subtask_completion(
        state,
        subtask_name="plan_approval",
        subtask_result={"status": "approved"},
    )
    
    print(f"Summary added: {state['messages'][-1]['content']}")


def example_conversation_health():
    """Example: Checking conversation health."""
    print_section("Example 5: Conversation Health Check")
    
    # Healthy conversation
    print("--- Healthy conversation ---")
    state = create_initial_state()
    state = add_message(state, "user", "Hello", None)
    state["loop_count"] = 3
    state["user_profile"]["learning_goals"] = ["Learn Python"]
    state["course_candidates"] = [
        {
            "title": "Python Course",
            "url": "https://example.com/python",
            "description": "Learn Python",
            "difficulty": "beginner",
            "source": "geektime",
        }
    ]
    
    health = check_conversation_health(state)
    print(f"Health: {health['health']}")
    print(f"Issues: {health['issues']}")
    print(f"Warnings: {health['warnings']}")
    
    # Conversation with warnings
    print("\n--- Conversation with high loop count ---")
    state["loop_count"] = 9
    
    health = check_conversation_health(state)
    print(f"Health: {health['health']}")
    print(f"Issues: {health['issues']}")
    print(f"Warnings: {health['warnings']}")
    
    # Unhealthy conversation
    print("\n--- Unhealthy conversation (loop limit exceeded) ---")
    state["loop_count"] = 12
    
    health = check_conversation_health(state)
    print(f"Health: {health['health']}")
    print(f"Issues: {health['issues']}")
    print(f"Warnings: {health['warnings']}")


def example_full_conversation_flow():
    """Example: Complete conversation flow with all features."""
    print_section("Example 6: Complete Conversation Flow")
    
    # Initialize conversation
    state = create_initial_state()
    print("1. Conversation started")
    print_state_info(state)
    
    # User provides initial input
    state = add_message(state, "user", "我想学习Python和Web开发", None)
    state["user_profile"]["learning_goals"] = ["Learn Python", "Web Development"]
    state["user_profile"]["skill_level"] = "beginner"
    
    # Coordinator routes to course advisor
    state["next_agent"] = "course_advisor"
    state["current_task"] = "course_search"
    state = maintain_context_on_transition(state, "coordinator", "course_advisor")
    
    print("\n2. Routed to course advisor")
    print_state_info(state)
    
    # Course advisor finds courses
    state["course_candidates"] = [
        {
            "title": "Python 核心技术",
            "url": "https://example.com/python",
            "description": "Learn Python",
            "difficulty": "beginner",
            "source": "geektime",
        },
        {
            "title": "Web 开发实战",
            "url": "https://example.com/web",
            "description": "Build web apps",
            "difficulty": "intermediate",
            "source": "geektime",
        },
    ]
    
    state = summarize_subtask_completion(
        state,
        subtask_name="course_search",
        subtask_result={"num_courses": 2},
    )
    
    print("\n3. Courses found and summarized")
    print(f"   Last message: {state['messages'][-1]['content']}")
    
    # Route to learning planner
    state["next_agent"] = "learning_planner"
    state["current_task"] = "create_learning_plan"
    state = maintain_context_on_transition(state, "course_advisor", "learning_planner")
    
    print("\n4. Routed to learning planner")
    
    # Learning planner creates plan
    state["learning_plan"] = {
        "goal": "Learn Python and Web Development",
        "milestones": [
            {"name": "Python Basics", "duration": "1 month"},
            {"name": "Web Fundamentals", "duration": "1 month"},
            {"name": "Full Stack Project", "duration": "1 month"},
        ],
        "recommended_courses": state["course_candidates"],
        "estimated_duration": "3 months",
        "created_at": datetime.now(),
        "status": "draft",
    }
    
    state = summarize_subtask_completion(
        state,
        subtask_name="learning_plan_creation",
        subtask_result={
            "milestones": state["learning_plan"]["milestones"],
            "estimated_duration": "3 months",
        },
    )
    
    print("\n5. Learning plan created and summarized")
    print(f"   Last message: {state['messages'][-1]['content']}")
    
    # Create conversation summary
    summary = create_conversation_summary(state)
    print("\n6. Conversation summary:")
    print(summary)
    
    # Check health
    health = check_conversation_health(state)
    print(f"\n7. Conversation health: {health['health']}")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("  Conversation Flow Control Examples")
    print("=" * 60)
    
    example_context_maintenance()
    example_context_extraction()
    example_topic_switching()
    example_subtask_summarization()
    example_conversation_health()
    example_full_conversation_flow()
    
    print("\n" + "=" * 60)
    print("  All examples completed successfully!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
