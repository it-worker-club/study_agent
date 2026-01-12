"""Example demonstrating memory persistence functionality.

This example shows how to:
1. Initialize the database
2. Create a graph with persistence enabled
3. Save and load conversation state
4. Persist user profiles and learning plans
"""

import asyncio
from datetime import datetime

from src.graph.builder import create_graph_with_persistence
from src.graph.helpers import (
    create_initial_state,
    add_message,
    persist_state_to_database,
    load_state_from_database,
    update_user_profile_in_state,
    save_learning_plan_from_state,
)
from src.graph.state import LearningPlan
from src.memory.database import init_database, get_database_manager
from src.memory.checkpointer import (
    save_user_profile,
    load_user_profile,
    save_learning_plan,
    load_learning_plan,
    list_user_learning_plans,
)


async def example_basic_persistence():
    """基本持久化示例"""
    print("=== Basic Persistence Example ===\n")
    
    # 1. 初始化数据库
    database_path = "./data/example_tutoring.db"
    db_manager = init_database(database_path)
    print(f"✓ Database initialized at {database_path}\n")
    
    # 2. 创建初始状态
    state = create_initial_state(
        conversation_id="conv_001",
        user_id="user_123",
    )
    
    # 3. 添加一些消息
    state = add_message(state, "user", "我想学习 Python 数据分析")
    state = add_message(
        state,
        "assistant",
        "好的，我可以帮您推荐相关课程和制定学习计划。",
        agent="coordinator",
    )
    
    # 4. 更新用户画像
    state["user_profile"]["background"] = "软件工程师"
    state["user_profile"]["skill_level"] = "intermediate"
    state["user_profile"]["learning_goals"] = ["掌握 pandas", "学习数据可视化"]
    
    # 5. 持久化状态
    success = persist_state_to_database(state, database_path)
    print(f"✓ State persisted: {success}\n")
    
    # 6. 加载状态
    loaded_state = load_state_from_database("conv_001", database_path)
    if loaded_state:
        print(f"✓ State loaded successfully")
        print(f"  - Conversation ID: {loaded_state['conversation_id']}")
        print(f"  - User ID: {loaded_state['user_profile']['user_id']}")
        print(f"  - Messages: {len(loaded_state['messages'])}")
        print(f"  - Skill level: {loaded_state['user_profile']['skill_level']}")
        print(f"  - Learning goals: {loaded_state['user_profile']['learning_goals']}\n")


async def example_user_profile_persistence():
    """用户画像持久化示例"""
    print("=== User Profile Persistence Example ===\n")
    
    database_path = "./data/example_tutoring.db"
    db_manager = get_database_manager(database_path)
    
    # 1. 创建用户画像
    user_profile = {
        "user_id": "user_456",
        "background": "数据分析师",
        "skill_level": "beginner",
        "learning_goals": ["学习机器学习", "掌握深度学习"],
        "time_availability": "每天 2 小时",
        "preferences": {
            "learning_style": "实践为主",
            "preferred_language": "中文",
        },
    }
    
    # 2. 保存用户画像
    success = save_user_profile(db_manager, user_profile)
    print(f"✓ User profile saved: {success}\n")
    
    # 3. 加载用户画像
    loaded_profile = load_user_profile(db_manager, "user_456")
    if loaded_profile:
        print(f"✓ User profile loaded:")
        print(f"  - User ID: {loaded_profile['user_id']}")
        print(f"  - Background: {loaded_profile['background']}")
        print(f"  - Skill level: {loaded_profile['skill_level']}")
        print(f"  - Learning goals: {loaded_profile['learning_goals']}")
        print(f"  - Time availability: {loaded_profile['time_availability']}")
        print(f"  - Preferences: {loaded_profile['preferences']}\n")


async def example_learning_plan_persistence():
    """学习计划持久化示例"""
    print("=== Learning Plan Persistence Example ===\n")
    
    database_path = "./data/example_tutoring.db"
    db_manager = get_database_manager(database_path)
    
    # 1. 创建学习计划
    learning_plan: LearningPlan = {
        "goal": "成为 Python 数据分析专家",
        "milestones": [
            {
                "phase": "基础阶段",
                "duration": "2 周",
                "topics": ["Python 基础", "NumPy", "Pandas"],
            },
            {
                "phase": "进阶阶段",
                "duration": "3 周",
                "topics": ["数据可视化", "统计分析", "数据清洗"],
            },
            {
                "phase": "实战阶段",
                "duration": "3 周",
                "topics": ["项目实战", "案例分析"],
            },
        ],
        "recommended_courses": [
            {
                "title": "Python 数据分析实战",
                "url": "https://example.com/course1",
                "description": "从零开始学习 Python 数据分析",
                "difficulty": "intermediate",
                "duration": "8 周",
                "rating": 4.8,
                "source": "geektime",
            },
        ],
        "estimated_duration": "8 周",
        "created_at": datetime.now(),
        "status": "draft",
    }
    
    # 2. 保存学习计划
    plan_id = save_learning_plan(
        db_manager,
        "conv_002",
        "user_456",
        learning_plan,
    )
    print(f"✓ Learning plan saved with ID: {plan_id}\n")
    
    # 3. 加载学习计划
    loaded_plan = load_learning_plan(db_manager, plan_id=plan_id)
    if loaded_plan:
        print(f"✓ Learning plan loaded:")
        print(f"  - Goal: {loaded_plan['goal']}")
        print(f"  - Milestones: {len(loaded_plan['milestones'])}")
        print(f"  - Recommended courses: {len(loaded_plan['recommended_courses'])}")
        print(f"  - Estimated duration: {loaded_plan['estimated_duration']}")
        print(f"  - Status: {loaded_plan['status']}\n")
    
    # 4. 列出用户的所有学习计划
    plans = list_user_learning_plans(db_manager, "user_456")
    print(f"✓ User has {len(plans)} learning plan(s):")
    for plan in plans:
        print(f"  - Plan {plan['plan_id']}: {plan['goal']} ({plan['status']})")
    print()


async def example_graph_with_persistence():
    """使用持久化的图示例"""
    print("=== Graph with Persistence Example ===\n")
    
    database_path = "./data/example_tutoring.db"
    
    # 1. 创建带持久化的图
    graph = await create_graph_with_persistence(database_path)
    print("✓ Graph created with persistence enabled\n")
    
    # 2. 创建初始状态
    initial_state = create_initial_state(
        conversation_id="conv_003",
        user_id="user_789",
    )
    
    # 添加用户消息
    initial_state = add_message(
        initial_state,
        "user",
        "我想学习机器学习，有什么推荐的课程吗？",
    )
    
    print("✓ Initial state created with user message")
    print(f"  - Conversation ID: {initial_state['conversation_id']}")
    print(f"  - User ID: {initial_state['user_profile']['user_id']}")
    print(f"  - Messages: {len(initial_state['messages'])}\n")
    
    # 3. 使用 thread_id 配置运行图
    # 注意：这里只是演示配置，实际运行需要完整的 vLLM 服务
    config = {
        "configurable": {
            "thread_id": initial_state["conversation_id"],
        }
    }
    
    print("✓ Graph is ready to run with config:")
    print(f"  - Thread ID: {config['configurable']['thread_id']}")
    print("\nNote: To actually run the graph, you need:")
    print("  1. A running vLLM service")
    print("  2. Proper configuration in config/system_config.yaml")
    print("  3. Call: result = await graph.ainvoke(initial_state, config=config)\n")


async def example_conversation_continuation():
    """对话继续示例"""
    print("=== Conversation Continuation Example ===\n")
    
    database_path = "./data/example_tutoring.db"
    
    # 1. 加载之前的对话
    conversation_id = "conv_001"
    state = load_state_from_database(conversation_id, database_path)
    
    if state:
        print(f"✓ Loaded previous conversation: {conversation_id}")
        print(f"  - Previous messages: {len(state['messages'])}")
        
        # 2. 添加新消息
        state = add_message(
            state,
            "user",
            "我还想了解一下学习路径规划",
        )
        
        print(f"  - Added new message")
        print(f"  - Total messages now: {len(state['messages'])}\n")
        
        # 3. 保存更新后的状态
        success = persist_state_to_database(state, database_path)
        print(f"✓ Updated state persisted: {success}\n")
    else:
        print(f"✗ Conversation {conversation_id} not found\n")


async def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("Memory Persistence Examples")
    print("=" * 60 + "\n")
    
    try:
        await example_basic_persistence()
        await example_user_profile_persistence()
        await example_learning_plan_persistence()
        await example_graph_with_persistence()
        await example_conversation_continuation()
        
        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
