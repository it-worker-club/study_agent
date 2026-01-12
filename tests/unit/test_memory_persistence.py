"""Unit tests for memory persistence functionality."""

import pytest
from datetime import datetime
from pathlib import Path

from src.memory.database import (
    init_database,
    get_database_manager,
    create_conversation,
    save_message,
    load_messages,
    update_conversation_status,
)
from src.memory.checkpointer import (
    save_user_profile,
    load_user_profile,
    save_learning_plan,
    load_learning_plan,
    list_user_learning_plans,
    update_learning_plan_status,
)
from src.graph.helpers import (
    create_initial_state,
    persist_state_to_database,
    load_state_from_database,
)


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return str(tmp_path / "test_tutoring.db")


@pytest.fixture
def db_manager(test_db_path):
    """Initialize database and return manager."""
    return init_database(test_db_path)


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""
    
    def test_init_database_creates_file(self, test_db_path):
        """Test that init_database creates the database file."""
        db_manager = init_database(test_db_path)
        assert Path(test_db_path).exists()
        assert db_manager is not None
    
    def test_init_database_creates_tables(self, db_manager):
        """Test that all required tables are created."""
        # Query sqlite_master to check tables exist
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        rows = db_manager.execute_query(query)
        
        table_names = [row["name"] for row in rows]
        
        assert "conversations" in table_names
        assert "messages" in table_names
        assert "user_profiles" in table_names
        assert "learning_plans" in table_names


class TestConversationManagement:
    """Test conversation CRUD operations."""
    
    def test_create_conversation(self, db_manager):
        """Test creating a new conversation."""
        success = create_conversation(db_manager, "conv_test_001", "user_001")
        assert success
        
        # Verify conversation exists
        query = "SELECT * FROM conversations WHERE conversation_id = ?"
        row = db_manager.execute_query(query, ("conv_test_001",), fetch_one=True)
        assert row is not None
        assert row["user_id"] == "user_001"
        assert row["status"] == "active"
    
    def test_save_and_load_messages(self, db_manager):
        """Test saving and loading messages."""
        # Create conversation first
        create_conversation(db_manager, "conv_test_002", "user_002")
        
        # Save messages
        save_message(db_manager, "conv_test_002", "user", "Hello")
        save_message(db_manager, "conv_test_002", "assistant", "Hi there!", agent="coordinator")
        
        # Load messages
        messages = load_messages(db_manager, "conv_test_002")
        
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["agent"] == "coordinator"
    
    def test_update_conversation_status(self, db_manager):
        """Test updating conversation status."""
        create_conversation(db_manager, "conv_test_003", "user_003")
        
        success = update_conversation_status(db_manager, "conv_test_003", "completed")
        assert success
        
        # Verify status updated
        query = "SELECT status FROM conversations WHERE conversation_id = ?"
        row = db_manager.execute_query(query, ("conv_test_003",), fetch_one=True)
        assert row["status"] == "completed"


class TestUserProfilePersistence:
    """Test user profile persistence."""
    
    def test_save_and_load_user_profile(self, db_manager):
        """Test saving and loading user profile."""
        user_profile = {
            "user_id": "user_profile_001",
            "background": "Software Engineer",
            "skill_level": "intermediate",
            "learning_goals": ["Learn Python", "Master Data Science"],
            "time_availability": "2 hours/day",
            "preferences": {"style": "hands-on"},
        }
        
        # Save profile
        success = save_user_profile(db_manager, user_profile)
        assert success
        
        # Load profile
        loaded = load_user_profile(db_manager, "user_profile_001")
        assert loaded is not None
        assert loaded["user_id"] == "user_profile_001"
        assert loaded["background"] == "Software Engineer"
        assert loaded["skill_level"] == "intermediate"
        assert loaded["learning_goals"] == ["Learn Python", "Master Data Science"]
        assert loaded["preferences"] == {"style": "hands-on"}
    
    def test_update_user_profile(self, db_manager):
        """Test updating an existing user profile."""
        user_profile = {
            "user_id": "user_profile_002",
            "background": "Student",
            "skill_level": "beginner",
            "learning_goals": ["Learn basics"],
            "time_availability": None,
            "preferences": {},
        }
        
        # Save initial profile
        save_user_profile(db_manager, user_profile)
        
        # Update profile
        user_profile["skill_level"] = "intermediate"
        user_profile["learning_goals"] = ["Advanced topics"]
        save_user_profile(db_manager, user_profile)
        
        # Load and verify
        loaded = load_user_profile(db_manager, "user_profile_002")
        assert loaded["skill_level"] == "intermediate"
        assert loaded["learning_goals"] == ["Advanced topics"]


class TestLearningPlanPersistence:
    """Test learning plan persistence."""
    
    def test_save_and_load_learning_plan(self, db_manager):
        """Test saving and loading learning plan."""
        # Create conversation and user profile first
        create_conversation(db_manager, "conv_plan_001", "user_plan_001")
        save_user_profile(db_manager, {
            "user_id": "user_plan_001",
            "background": None,
            "skill_level": None,
            "learning_goals": [],
            "time_availability": None,
            "preferences": {},
        })
        
        learning_plan = {
            "goal": "Master Python",
            "milestones": [
                {"phase": "Basics", "duration": "2 weeks"},
                {"phase": "Advanced", "duration": "4 weeks"},
            ],
            "recommended_courses": [
                {
                    "title": "Python Course",
                    "url": "https://example.com",
                    "description": "Learn Python",
                    "difficulty": "intermediate",
                    "duration": "6 weeks",
                    "rating": 4.5,
                    "source": "geektime",
                }
            ],
            "estimated_duration": "6 weeks",
            "created_at": datetime.now(),
            "status": "draft",
        }
        
        # Save plan
        plan_id = save_learning_plan(
            db_manager,
            "conv_plan_001",
            "user_plan_001",
            learning_plan,
        )
        assert plan_id is not None
        
        # Load plan
        loaded = load_learning_plan(db_manager, plan_id=plan_id)
        assert loaded is not None
        assert loaded["goal"] == "Master Python"
        assert len(loaded["milestones"]) == 2
        assert len(loaded["recommended_courses"]) == 1
        assert loaded["status"] == "draft"
    
    def test_list_user_learning_plans(self, db_manager):
        """Test listing all learning plans for a user."""
        # Create conversation and user profile
        create_conversation(db_manager, "conv_plan_002", "user_plan_002")
        save_user_profile(db_manager, {
            "user_id": "user_plan_002",
            "background": None,
            "skill_level": None,
            "learning_goals": [],
            "time_availability": None,
            "preferences": {},
        })
        
        # Save multiple plans
        for i in range(3):
            learning_plan = {
                "goal": f"Goal {i}",
                "milestones": [],
                "recommended_courses": [],
                "estimated_duration": "1 week",
                "created_at": datetime.now(),
                "status": "draft",
            }
            save_learning_plan(db_manager, "conv_plan_002", "user_plan_002", learning_plan)
        
        # List plans
        plans = list_user_learning_plans(db_manager, "user_plan_002")
        assert len(plans) == 3
    
    def test_update_learning_plan_status(self, db_manager):
        """Test updating learning plan status."""
        # Create conversation and user profile
        create_conversation(db_manager, "conv_plan_003", "user_plan_003")
        save_user_profile(db_manager, {
            "user_id": "user_plan_003",
            "background": None,
            "skill_level": None,
            "learning_goals": [],
            "time_availability": None,
            "preferences": {},
        })
        
        learning_plan = {
            "goal": "Test Goal",
            "milestones": [],
            "recommended_courses": [],
            "estimated_duration": "1 week",
            "created_at": datetime.now(),
            "status": "draft",
        }
        
        plan_id = save_learning_plan(db_manager, "conv_plan_003", "user_plan_003", learning_plan)
        
        # Update status
        success = update_learning_plan_status(db_manager, plan_id, "approved")
        assert success
        
        # Verify
        loaded = load_learning_plan(db_manager, plan_id=plan_id)
        assert loaded["status"] == "approved"


class TestStatePersistence:
    """Test full state persistence and loading."""
    
    def test_persist_and_load_state(self, test_db_path):
        """Test persisting and loading complete state."""
        # Initialize database
        init_database(test_db_path)
        
        # Create initial state
        state = create_initial_state("conv_state_001", "user_state_001")
        state["user_profile"]["background"] = "Engineer"
        state["user_profile"]["skill_level"] = "intermediate"
        state["messages"].append({
            "role": "user",
            "content": "Hello",
            "timestamp": datetime.now(),
            "agent": None,
        })
        
        # Persist state
        success = persist_state_to_database(state, test_db_path)
        assert success
        
        # Load state
        loaded_state = load_state_from_database("conv_state_001", test_db_path)
        assert loaded_state is not None
        assert loaded_state["conversation_id"] == "conv_state_001"
        assert loaded_state["user_profile"]["user_id"] == "user_state_001"
        assert loaded_state["user_profile"]["background"] == "Engineer"
        assert len(loaded_state["messages"]) == 1
    
    def test_load_nonexistent_state(self, test_db_path):
        """Test loading a state that doesn't exist."""
        init_database(test_db_path)
        
        loaded_state = load_state_from_database("nonexistent", test_db_path)
        assert loaded_state is None
