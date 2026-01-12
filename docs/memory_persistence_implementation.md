# Memory Persistence Implementation

## Overview

This document describes the memory persistence implementation for the education tutoring system. The implementation provides database storage for conversation history, user profiles, and learning plans, along with LangGraph checkpoint integration for state recovery.

## Architecture

### Components

1. **Database Layer** (`src/memory/database.py`)
   - SQLite database initialization and schema management
   - CRUD operations for conversations, messages, user profiles, and learning plans
   - Database connection management

2. **Checkpointer Layer** (`src/memory/checkpointer.py`)
   - LangGraph AsyncSQLiteSaver integration
   - User profile persistence functions
   - Learning plan persistence functions

3. **Helper Functions** (`src/graph/helpers.py`)
   - State persistence and loading utilities
   - User profile update functions
   - Learning plan save functions

4. **Graph Integration** (`src/graph/builder.py`)
   - Graph creation with persistence enabled
   - Automatic database initialization

## Database Schema

### Tables

#### 1. conversations
Stores conversation session metadata.

```sql
CREATE TABLE conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'archived'))
);
```

#### 2. messages
Stores individual messages in conversations.

```sql
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);
```

#### 3. user_profiles
Stores user profile information.

```sql
CREATE TABLE user_profiles (
    user_id TEXT PRIMARY KEY,
    background TEXT,
    skill_level TEXT CHECK(skill_level IN ('beginner', 'intermediate', 'advanced', NULL)),
    learning_goals TEXT,  -- JSON array
    time_availability TEXT,
    preferences TEXT,  -- JSON object
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4. learning_plans
Stores learning plans created for users.

```sql
CREATE TABLE learning_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    plan_content TEXT NOT NULL,  -- JSON object
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'approved', 'in_progress', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);
```

### Indexes

Performance indexes are created on frequently queried columns:
- `idx_messages_conversation`: Messages by conversation
- `idx_messages_timestamp`: Messages by timestamp
- `idx_conversations_user`: Conversations by user
- `idx_learning_plans_user`: Learning plans by user
- `idx_learning_plans_conversation`: Learning plans by conversation

## Usage

### 1. Initialize Database

```python
from src.memory.database import init_database

# Initialize database with schema
database_path = "./data/tutoring_system.db"
db_manager = init_database(database_path)
```

### 2. Create Graph with Persistence

```python
from src.graph.builder import create_graph_with_persistence

# Create graph with automatic database initialization
graph = await create_graph_with_persistence(
    database_path="./data/tutoring_system.db",
    max_loop_count=10,
)

# Run graph with thread_id for conversation tracking
config = {
    "configurable": {
        "thread_id": "user_123_session_001",
    }
}

result = await graph.ainvoke(initial_state, config=config)
```

### 3. Save and Load User Profiles

```python
from src.memory.database import get_database_manager
from src.memory.checkpointer import save_user_profile, load_user_profile

db_manager = get_database_manager(database_path)

# Save user profile
user_profile = {
    "user_id": "user_123",
    "background": "软件工程师",
    "skill_level": "intermediate",
    "learning_goals": ["学习 Python", "掌握数据分析"],
    "time_availability": "每天 2 小时",
    "preferences": {"learning_style": "实践为主"},
}

save_user_profile(db_manager, user_profile)

# Load user profile
loaded_profile = load_user_profile(db_manager, "user_123")
```

### 4. Save and Load Learning Plans

```python
from src.memory.checkpointer import (
    save_learning_plan,
    load_learning_plan,
    list_user_learning_plans,
)

# Save learning plan
learning_plan = {
    "goal": "成为 Python 专家",
    "milestones": [...],
    "recommended_courses": [...],
    "estimated_duration": "8 周",
    "created_at": datetime.now(),
    "status": "draft",
}

plan_id = save_learning_plan(
    db_manager,
    conversation_id="conv_001",
    user_id="user_123",
    learning_plan=learning_plan,
)

# Load learning plan
loaded_plan = load_learning_plan(db_manager, plan_id=plan_id)

# List all plans for a user
plans = list_user_learning_plans(db_manager, "user_123", limit=10)
```

### 5. Persist and Load State

```python
from src.graph.helpers import (
    persist_state_to_database,
    load_state_from_database,
)

# Persist entire state
success = persist_state_to_database(state, database_path)

# Load state from database
loaded_state = load_state_from_database("conv_001", database_path)
```

### 6. Update User Profile in State

```python
from src.graph.helpers import update_user_profile_in_state

# Update user profile and persist
state = update_user_profile_in_state(
    state,
    database_path,
    skill_level="advanced",
    learning_goals=["深度学习", "自然语言处理"],
)
```

## LangGraph Checkpointer Integration

The system uses LangGraph's `AsyncSQLiteSaver` for automatic state checkpointing:

```python
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

# Create checkpointer
checkpointer = AsyncSqliteSaver.from_conn_string(database_path)
await checkpointer.setup()

# Use with graph
graph = create_graph(checkpointer=checkpointer)
```

### Benefits

1. **Automatic State Persistence**: LangGraph automatically saves state at each node
2. **State Recovery**: Resume conversations from any checkpoint
3. **Time Travel**: Access historical states for debugging
4. **Thread Safety**: Separate conversation threads with unique thread_ids

### Configuration

```python
# Run with specific thread_id
config = {
    "configurable": {
        "thread_id": "conversation_123",
    }
}

# Resume from checkpoint
result = await graph.ainvoke(state, config=config)

# Get state history
history = await checkpointer.aget_tuple(config)
```

## Data Flow

### Saving Data

```
User Input → Graph Execution → State Updates → Checkpointer
                                              ↓
                                    Database (conversations, messages)
                                              ↓
                                    Manual Persistence (profiles, plans)
```

### Loading Data

```
Thread ID → Checkpointer → Latest State
                              ↓
                    Load Additional Data (profiles, plans)
                              ↓
                    Complete State Object
```

## Error Handling

All persistence functions include error handling:

```python
try:
    success = save_user_profile(db_manager, user_profile)
    if not success:
        logger.error("Failed to save user profile")
except Exception as e:
    logger.error(f"Error saving user profile: {e}")
```

### Common Errors

1. **Database Connection Errors**: Check database path and permissions
2. **Schema Errors**: Ensure database is initialized with `init_database()`
3. **Foreign Key Violations**: Ensure referenced records exist
4. **JSON Serialization Errors**: Validate data types before saving

## Performance Considerations

### Indexes

All frequently queried columns have indexes for optimal performance:
- Message queries by conversation_id
- User profile lookups by user_id
- Learning plan queries by user_id and conversation_id

### Batch Operations

For bulk operations, use transactions:

```python
with db_manager.get_connection() as conn:
    cursor = conn.cursor()
    for message in messages:
        cursor.execute(query, params)
    conn.commit()
```

### Connection Pooling

The `DatabaseManager` creates connections on-demand. For high-concurrency scenarios, consider implementing connection pooling.

## Testing

### Unit Tests

Test individual persistence functions:

```python
def test_save_user_profile():
    db_manager = init_database(":memory:")
    user_profile = {...}
    success = save_user_profile(db_manager, user_profile)
    assert success
    
    loaded = load_user_profile(db_manager, user_profile["user_id"])
    assert loaded == user_profile
```

### Integration Tests

Test full persistence flow:

```python
async def test_graph_persistence():
    graph = await create_graph_with_persistence(":memory:")
    state = create_initial_state()
    
    config = {"configurable": {"thread_id": "test_001"}}
    result = await graph.ainvoke(state, config=config)
    
    # Verify state was persisted
    loaded = load_state_from_database("test_001", ":memory:")
    assert loaded is not None
```

## Migration and Maintenance

### Schema Updates

To update the schema:

1. Create migration script
2. Backup existing database
3. Apply schema changes
4. Verify data integrity

### Backup Strategy

Regular backups recommended:

```bash
# Backup SQLite database
cp data/tutoring_system.db data/backups/tutoring_system_$(date +%Y%m%d).db
```

### Data Cleanup

Implement cleanup for old conversations:

```sql
-- Archive old conversations
UPDATE conversations 
SET status = 'archived' 
WHERE updated_at < datetime('now', '-30 days');

-- Delete very old archived conversations
DELETE FROM conversations 
WHERE status = 'archived' 
AND updated_at < datetime('now', '-90 days');
```

## Requirements Validation

This implementation validates the following requirements:

- **Requirement 4.1**: Persist conversation history across multiple sessions ✓
- **Requirement 4.2**: Store user preferences and learning goals ✓
- **Requirement 4.3**: Load previous conversation context when user returns ✓
- **Requirement 4.4**: Support at least 10 rounds of continuous conversation ✓
- **Requirement 4.5**: Include timestamps for all stored interactions ✓

## Example Usage

See `examples/memory_persistence_example.py` for complete working examples of:
- Basic persistence
- User profile management
- Learning plan storage
- Graph with persistence
- Conversation continuation

## Troubleshooting

### Database Locked Error

If you encounter "database is locked" errors:
1. Ensure only one process accesses the database
2. Use proper connection management (context managers)
3. Consider using WAL mode: `PRAGMA journal_mode=WAL`

### Missing Data

If data is not persisted:
1. Check that `persist_state_to_database()` is called
2. Verify database path is correct
3. Check logs for error messages
4. Ensure database has write permissions

### Checkpoint Not Found

If checkpoints are not found:
1. Verify thread_id is consistent
2. Ensure checkpointer is properly initialized
3. Check that graph was compiled with checkpointer

## Future Enhancements

Potential improvements:
1. Add support for PostgreSQL/MySQL for production deployments
2. Implement data encryption for sensitive information
3. Add full-text search for message history
4. Implement automatic backup and recovery
5. Add metrics and monitoring for database operations

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
