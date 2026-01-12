"""Unit tests for routing logic.

Tests the route_next function to ensure correct routing decisions
based on state conditions.
"""

import pytest

from src.graph.helpers import create_initial_state, route_next


class TestRouteNext:
    """Test suite for route_next function."""
    
    def test_route_to_end_when_loop_count_exceeded(self):
        """Test that routing goes to 'end' when loop count exceeds limit."""
        state = create_initial_state()
        state["loop_count"] = 11  # Exceeds default max of 10
        state["next_agent"] = "coordinator"
        
        result = route_next(state)
        
        assert result == "end"
    
    def test_route_to_end_when_is_complete(self):
        """Test that routing goes to 'end' when task is complete."""
        state = create_initial_state()
        state["is_complete"] = True
        state["next_agent"] = "coordinator"
        
        result = route_next(state)
        
        assert result == "end"
    
    def test_route_to_human_input_when_required(self):
        """Test that routing goes to 'human_input' when human input is required."""
        state = create_initial_state()
        state["requires_human_input"] = True
        state["next_agent"] = "coordinator"
        
        result = route_next(state)
        
        assert result == "human_input"
    
    def test_route_to_coordinator(self):
        """Test routing to coordinator agent."""
        state = create_initial_state()
        state["next_agent"] = "coordinator"
        
        result = route_next(state)
        
        assert result == "coordinator"
    
    def test_route_to_course_advisor(self):
        """Test routing to course advisor agent."""
        state = create_initial_state()
        state["next_agent"] = "course_advisor"
        
        result = route_next(state)
        
        assert result == "course_advisor"
    
    def test_route_to_learning_planner(self):
        """Test routing to learning planner agent."""
        state = create_initial_state()
        state["next_agent"] = "learning_planner"
        
        result = route_next(state)
        
        assert result == "learning_planner"
    
    def test_route_to_end_explicitly(self):
        """Test routing to end node explicitly."""
        state = create_initial_state()
        state["next_agent"] = "end"
        
        result = route_next(state)
        
        assert result == "end"
    
    def test_route_to_end_when_next_agent_is_none(self):
        """Test that routing defaults to 'end' when next_agent is None."""
        state = create_initial_state()
        state["next_agent"] = None
        
        result = route_next(state)
        
        assert result == "end"
    
    def test_route_to_end_when_next_agent_is_invalid(self):
        """Test that routing defaults to 'end' when next_agent is invalid."""
        state = create_initial_state()
        state["next_agent"] = "invalid_agent"
        
        result = route_next(state)
        
        assert result == "end"
    
    def test_custom_max_loop_count(self):
        """Test routing with custom max loop count."""
        state = create_initial_state()
        state["loop_count"] = 6
        state["next_agent"] = "coordinator"
        
        # Should not route to end with default max (10)
        result = route_next(state, max_loop_count=10)
        assert result == "coordinator"
        
        # Should route to end with custom max (5)
        result = route_next(state, max_loop_count=5)
        assert result == "end"
    
    def test_priority_order_loop_count_over_next_agent(self):
        """Test that loop count check has priority over next_agent."""
        state = create_initial_state()
        state["loop_count"] = 15
        state["next_agent"] = "coordinator"
        state["is_complete"] = False
        state["requires_human_input"] = False
        
        result = route_next(state)
        
        assert result == "end"
    
    def test_priority_order_is_complete_over_next_agent(self):
        """Test that is_complete check has priority over next_agent."""
        state = create_initial_state()
        state["loop_count"] = 5
        state["is_complete"] = True
        state["next_agent"] = "coordinator"
        state["requires_human_input"] = False
        
        result = route_next(state)
        
        assert result == "end"
    
    def test_priority_order_human_input_over_next_agent(self):
        """Test that requires_human_input has priority over next_agent."""
        state = create_initial_state()
        state["loop_count"] = 5
        state["is_complete"] = False
        state["requires_human_input"] = True
        state["next_agent"] = "coordinator"
        
        result = route_next(state)
        
        assert result == "human_input"
    
    def test_all_valid_agents_can_be_routed(self):
        """Test that all valid agent names can be routed to."""
        valid_agents = [
            "coordinator",
            "course_advisor",
            "learning_planner",
            "human_input",
            "end",
        ]
        
        for agent in valid_agents:
            state = create_initial_state()
            state["next_agent"] = agent
            
            result = route_next(state)
            
            assert result == agent, f"Failed to route to {agent}"
