"""Example demonstrating the routing logic in the education tutoring system.

This example shows how the route_next function is used to make routing
decisions based on the current state.
"""

from src.graph import create_initial_state, route_next, add_message


def demonstrate_routing():
    """Demonstrate various routing scenarios."""
    
    print("=" * 60)
    print("Education Tutoring System - Routing Logic Demo")
    print("=" * 60)
    
    # Scenario 1: Normal routing to coordinator
    print("\n1. Normal routing to coordinator:")
    state = create_initial_state()
    state["next_agent"] = "coordinator"
    result = route_next(state)
    print(f"   State: next_agent='coordinator', loop_count={state['loop_count']}")
    print(f"   Route decision: {result}")
    
    # Scenario 2: Routing to course advisor
    print("\n2. Routing to course advisor:")
    state = create_initial_state()
    state["next_agent"] = "course_advisor"
    result = route_next(state)
    print(f"   State: next_agent='course_advisor'")
    print(f"   Route decision: {result}")
    
    # Scenario 3: Routing to learning planner
    print("\n3. Routing to learning planner:")
    state = create_initial_state()
    state["next_agent"] = "learning_planner"
    result = route_next(state)
    print(f"   State: next_agent='learning_planner'")
    print(f"   Route decision: {result}")
    
    # Scenario 4: Human input required
    print("\n4. Human input required:")
    state = create_initial_state()
    state["next_agent"] = "coordinator"
    state["requires_human_input"] = True
    result = route_next(state)
    print(f"   State: requires_human_input=True")
    print(f"   Route decision: {result} (overrides next_agent)")
    
    # Scenario 5: Task completed
    print("\n5. Task completed:")
    state = create_initial_state()
    state["next_agent"] = "coordinator"
    state["is_complete"] = True
    result = route_next(state)
    print(f"   State: is_complete=True")
    print(f"   Route decision: {result} (overrides next_agent)")
    
    # Scenario 6: Loop count exceeded
    print("\n6. Loop count exceeded (prevents infinite loops):")
    state = create_initial_state()
    state["next_agent"] = "coordinator"
    state["loop_count"] = 11
    result = route_next(state)
    print(f"   State: loop_count=11 (max=10)")
    print(f"   Route decision: {result} (safety mechanism)")
    
    # Scenario 7: Invalid next_agent
    print("\n7. Invalid next_agent (safety fallback):")
    state = create_initial_state()
    state["next_agent"] = "invalid_agent"
    result = route_next(state)
    print(f"   State: next_agent='invalid_agent'")
    print(f"   Route decision: {result} (safe default)")
    
    # Scenario 8: Priority demonstration
    print("\n8. Priority demonstration (loop_count > is_complete > human_input > next_agent):")
    state = create_initial_state()
    state["loop_count"] = 11
    state["is_complete"] = True
    state["requires_human_input"] = True
    state["next_agent"] = "coordinator"
    result = route_next(state)
    print(f"   State: All conditions set")
    print(f"   Route decision: {result} (loop_count has highest priority)")
    
    # Scenario 9: Typical conversation flow
    print("\n9. Typical conversation flow simulation:")
    state = create_initial_state()
    
    # User asks a question
    state = add_message(state, "user", "我想学习 Python 数据分析", None)
    state["next_agent"] = "coordinator"
    print(f"   Step 1: User input -> route to {route_next(state)}")
    
    # Coordinator routes to course advisor
    state["loop_count"] = 1
    state["next_agent"] = "course_advisor"
    print(f"   Step 2: Coordinator decision -> route to {route_next(state)}")
    
    # Course advisor completes, routes back to coordinator
    state["loop_count"] = 2
    state["next_agent"] = "coordinator"
    print(f"   Step 3: Course advisor done -> route to {route_next(state)}")
    
    # Coordinator routes to learning planner
    state["loop_count"] = 3
    state["next_agent"] = "learning_planner"
    print(f"   Step 4: Coordinator decision -> route to {route_next(state)}")
    
    # Learning planner creates plan, requires human approval
    state["loop_count"] = 4
    state["requires_human_input"] = True
    state["next_agent"] = "coordinator"
    print(f"   Step 5: Plan created -> route to {route_next(state)}")
    
    # After human approval, complete
    state["loop_count"] = 5
    state["requires_human_input"] = False
    state["is_complete"] = True
    state["next_agent"] = "end"
    print(f"   Step 6: User approved -> route to {route_next(state)}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_routing()
