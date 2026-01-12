"""Example demonstrating human input node usage.

This example shows how the human input node handles user feedback
for learning plan approval and course recommendation feedback.
"""

from datetime import datetime

from src.graph.state import AgentState, LearningPlan, CourseInfo
from src.graph.nodes import human_input_node
from src.graph.helpers import create_initial_state, add_message


def print_state_summary(state: AgentState, title: str):
    """Print a summary of the current state."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Conversation ID: {state['conversation_id']}")
    print(f"Requires Human Input: {state['requires_human_input']}")
    print(f"Next Agent: {state['next_agent']}")
    print(f"Current Task: {state.get('current_task')}")
    
    if state.get("learning_plan"):
        print(f"Learning Plan Status: {state['learning_plan']['status']}")
    
    print(f"\nMessages ({len(state['messages'])}):")
    for i, msg in enumerate(state["messages"][-3:], 1):  # Show last 3 messages
        print(f"  {i}. [{msg['role']}] {msg['content'][:80]}...")


def example_learning_plan_approval():
    """Example: Approving a learning plan."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Learning Plan Approval")
    print("="*60)
    
    # Create initial state
    state = create_initial_state()
    
    # Add a draft learning plan (as if created by learning planner)
    learning_plan: LearningPlan = {
        "goal": "学习 Python 数据分析",
        "milestones": [
            {
                "name": "Python 基础语法",
                "duration": "2周",
                "content": "学习变量、函数、类等基础概念",
            },
            {
                "name": "数据处理库",
                "duration": "3周",
                "content": "学习 NumPy 和 Pandas",
            },
            {
                "name": "数据可视化",
                "duration": "2周",
                "content": "学习 Matplotlib 和 Seaborn",
            },
        ],
        "recommended_courses": [],
        "estimated_duration": "7周",
        "created_at": datetime.now(),
        "status": "draft",
    }
    
    state["learning_plan"] = learning_plan
    state["requires_human_input"] = True
    state["human_feedback"] = None
    
    # Add a message from learning planner
    state = add_message(
        state,
        role="assistant",
        content="我为您制定了一个 7 周的学习计划，包含 3 个主要里程碑...",
        agent="learning_planner",
    )
    
    print_state_summary(state, "Initial State (Waiting for Approval)")
    
    # First call - node prompts for input
    state = human_input_node(state)
    print_state_summary(state, "After First Call (Prompt Generated)")
    
    # Simulate user approval
    state["human_feedback"] = "同意这个计划，看起来很合理"
    
    # Second call - node processes approval
    state = human_input_node(state)
    print_state_summary(state, "After Approval (Plan Approved)")
    
    print(f"\n✓ Learning plan status: {state['learning_plan']['status']}")
    print(f"✓ Ready to route to: {state['next_agent']}")


def example_learning_plan_revision():
    """Example: Requesting learning plan revision."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Learning Plan Revision Request")
    print("="*60)
    
    # Create initial state with draft plan
    state = create_initial_state()
    
    learning_plan: LearningPlan = {
        "goal": "学习 Web 开发",
        "milestones": [
            {"name": "HTML/CSS", "duration": "2周"},
            {"name": "JavaScript", "duration": "3周"},
        ],
        "recommended_courses": [],
        "estimated_duration": "5周",
        "created_at": datetime.now(),
        "status": "draft",
    }
    
    state["learning_plan"] = learning_plan
    state["requires_human_input"] = True
    
    print_state_summary(state, "Initial State")
    
    # User requests revision
    state["human_feedback"] = "我想重新规划，希望加入后端开发内容"
    
    # Process revision request
    state = human_input_node(state)
    print_state_summary(state, "After Revision Request")
    
    print(f"\n✓ Current task: {state['current_task']}")
    print(f"✓ Plan status: {state['learning_plan']['status']}")


def example_course_feedback():
    """Example: Providing feedback on course recommendations."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Course Recommendation Feedback")
    print("="*60)
    
    # Create initial state with course recommendations
    state = create_initial_state()
    
    courses = [
        CourseInfo(
            title="Python 核心技术与实战",
            url="https://time.geekbang.org/course/intro/100001",
            description="系统学习 Python 核心知识",
            difficulty="intermediate",
            duration="20小时",
            rating=4.8,
            source="geektime",
        ),
        CourseInfo(
            title="数据分析实战 45 讲",
            url="https://time.geekbang.org/course/intro/100002",
            description="实战数据分析技能",
            difficulty="intermediate",
            duration="15小时",
            rating=4.6,
            source="geektime",
        ),
    ]
    
    state["course_candidates"] = courses
    state["requires_human_input"] = True
    
    # Add course advisor message
    state = add_message(
        state,
        role="assistant",
        content="我为您推荐了 2 门课程...",
        agent="course_advisor",
    )
    
    print_state_summary(state, "Initial State (Courses Recommended)")
    
    # First call - prompt for feedback
    state = human_input_node(state)
    print_state_summary(state, "After Prompt")
    
    # User requests more courses
    state["human_feedback"] = "这些课程不错，能再推荐一些更高级的课程吗？"
    
    # Process feedback
    state = human_input_node(state)
    print_state_summary(state, "After Feedback")
    
    print(f"\n✓ Current task: {state['current_task']}")
    print(f"✓ Next agent: {state['next_agent']}")


def example_satisfaction_feedback():
    """Example: User satisfied with recommendations."""
    print("\n" + "="*60)
    print("EXAMPLE 4: User Satisfaction")
    print("="*60)
    
    # Create state with courses
    state = create_initial_state()
    
    course = CourseInfo(
        title="Python 入门课程",
        url="https://example.com/course",
        description="适合初学者",
        difficulty="beginner",
        duration="10小时",
        rating=4.5,
        source="geektime",
    )
    
    state["course_candidates"] = [course]
    state["requires_human_input"] = True
    state["human_feedback"] = "这些课程很好，我很满意"
    
    print_state_summary(state, "Initial State")
    
    # Process satisfaction
    state = human_input_node(state)
    print_state_summary(state, "After Processing")
    
    print(f"\n✓ User satisfied with recommendations")
    print(f"✓ Ready to continue conversation")


def example_interruption():
    """Example: User interruption at any point."""
    print("\n" + "="*60)
    print("EXAMPLE 5: User Interruption")
    print("="*60)
    
    # Create state mid-conversation
    state = create_initial_state()
    
    # Add some conversation history
    state = add_message(state, "user", "我想学习 Python", None)
    state = add_message(state, "assistant", "好的，让我为您推荐课程", "coordinator")
    
    # User interrupts with new request
    state["requires_human_input"] = True
    state["human_feedback"] = "等等，我想先了解一下学习路径"
    
    print_state_summary(state, "Initial State (User Interrupts)")
    
    # Process interruption
    state = human_input_node(state)
    print_state_summary(state, "After Interruption")
    
    print(f"\n✓ User interruption handled")
    print(f"✓ Coordinator will handle new request")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("HUMAN INPUT NODE EXAMPLES")
    print("="*60)
    
    example_learning_plan_approval()
    example_learning_plan_revision()
    example_course_feedback()
    example_satisfaction_feedback()
    example_interruption()
    
    print("\n" + "="*60)
    print("ALL EXAMPLES COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
