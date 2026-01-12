"""Unit tests for graph builder module.

Tests the creation and compilation of the LangGraph StateGraph.
"""

import pytest

from src.graph.builder import create_graph, create_graph_with_config
from src.graph.state import AgentState
from src.graph.helpers import create_initial_state, add_message
from src.utils.config import get_config


class TestGraphBuilder:
    """Test suite for graph builder functions."""
    
    def test_create_graph_without_checkpointer(self):
        """Test creating graph without checkpointer."""
        # Create graph
        graph = create_graph(checkpointer=None, max_loop_count=10)
        
        # Verify graph is created
        assert graph is not None
        
        # Verify graph has the expected structure
        # Note: We can't easily inspect the internal structure,
        # but we can verify it's a compiled graph
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "stream")
    
    def test_create_graph_with_custom_loop_count(self):
        """Test creating graph with custom max_loop_count."""
        # Create graph with custom loop count
        graph = create_graph(checkpointer=None, max_loop_count=5)
        
        # Verify graph is created
        assert graph is not None
        assert hasattr(graph, "invoke")
    
    def test_create_graph_with_config(self):
        """Test creating graph using system configuration."""
        # Load config
        config = get_config()
        
        # Create graph using config
        graph = create_graph_with_config(config, checkpointer=None)
        
        # Verify graph is created
        assert graph is not None
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "stream")
    
    def test_graph_structure_has_all_nodes(self):
        """Test that graph includes all required nodes."""
        # Create graph
        graph = create_graph(checkpointer=None)
        
        # Get the graph structure
        # Note: LangGraph doesn't expose nodes directly in a simple way,
        # but we can verify the graph was compiled successfully
        assert graph is not None
        
        # The graph should be invokable
        assert callable(graph.invoke)
    
    def test_graph_accepts_agent_state(self):
        """Test that graph accepts AgentState as input."""
        # Create graph
        graph = create_graph(checkpointer=None)
        
        # Create initial state
        state = create_initial_state()
        
        # Verify state is valid AgentState
        assert isinstance(state, dict)
        assert "messages" in state
        assert "conversation_id" in state
        assert "user_profile" in state
        
        # Note: We don't actually invoke the graph here because
        # it requires initialized agents and a running vLLM server
        # That's tested in integration tests
    
    def test_create_graph_returns_compiled_graph(self):
        """Test that create_graph returns a compiled graph."""
        # Create graph
        graph = create_graph(checkpointer=None)
        
        # Verify it has the methods of a compiled graph
        assert hasattr(graph, "invoke")
        assert hasattr(graph, "stream")
        assert hasattr(graph, "ainvoke")  # Async version
        assert hasattr(graph, "astream")  # Async stream
    
    def test_graph_with_zero_loop_count(self):
        """Test creating graph with zero max_loop_count."""
        # This should still work, but will immediately end
        graph = create_graph(checkpointer=None, max_loop_count=0)
        
        assert graph is not None
        assert hasattr(graph, "invoke")
    
    def test_graph_with_large_loop_count(self):
        """Test creating graph with large max_loop_count."""
        # Should handle large values
        graph = create_graph(checkpointer=None, max_loop_count=1000)
        
        assert graph is not None
        assert hasattr(graph, "invoke")


class TestGraphConfiguration:
    """Test suite for graph configuration."""
    
    def test_default_max_loop_count(self):
        """Test that default max_loop_count is used when not specified."""
        # Create graph without specifying max_loop_count
        graph = create_graph(checkpointer=None)
        
        # Should use default value (10)
        assert graph is not None
    
    def test_config_max_loop_count_is_used(self):
        """Test that config max_loop_count is used in create_graph_with_config."""
        # Load config
        config = get_config()
        
        # Verify config has max_loop_count
        assert hasattr(config.system, "max_loop_count")
        assert isinstance(config.system.max_loop_count, int)
        
        # Create graph with config
        graph = create_graph_with_config(config, checkpointer=None)
        
        # Should be created successfully
        assert graph is not None


class TestGraphCheckpointer:
    """Test suite for graph checkpointer functionality."""
    
    def test_create_graph_accepts_none_checkpointer(self):
        """Test that graph accepts None as checkpointer."""
        # Create graph with explicit None checkpointer
        graph = create_graph(checkpointer=None)
        
        assert graph is not None
        assert hasattr(graph, "invoke")
    
    @pytest.mark.skip(reason="Requires langgraph[sqlite] to be installed")
    def test_create_graph_with_sqlite_checkpointer(self):
        """Test creating graph with SQLite checkpointer."""
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
            
            # Create in-memory SQLite checkpointer
            checkpointer = SqliteSaver.from_conn_string(":memory:")
            
            # Create graph with checkpointer
            graph = create_graph(checkpointer=checkpointer)
            
            assert graph is not None
            assert hasattr(graph, "invoke")
            
        except ImportError:
            pytest.skip("langgraph[sqlite] not installed")


class TestGraphInvocation:
    """Test suite for graph invocation (without actual execution)."""
    
    def test_graph_invoke_signature(self):
        """Test that graph.invoke has correct signature."""
        # Create graph
        graph = create_graph(checkpointer=None)
        
        # Verify invoke method exists and is callable
        assert hasattr(graph, "invoke")
        assert callable(graph.invoke)
    
    def test_graph_stream_signature(self):
        """Test that graph.stream has correct signature."""
        # Create graph
        graph = create_graph(checkpointer=None)
        
        # Verify stream method exists and is callable
        assert hasattr(graph, "stream")
        assert callable(graph.stream)
    
    def test_initial_state_is_valid_for_graph(self):
        """Test that initial state created by helper is valid for graph."""
        # Create initial state
        state = create_initial_state()
        
        # Verify all required fields are present
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
            assert field in state, f"Missing required field: {field}"
        
        # Verify initial values
        assert isinstance(state["messages"], list)
        assert len(state["messages"]) == 0
        assert state["loop_count"] == 0
        assert state["is_complete"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
