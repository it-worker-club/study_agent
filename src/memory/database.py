"""Database management for the education tutoring system.

This module provides SQLite database initialization and management
for storing conversations, messages, user profiles, and learning plans.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Database schema SQL statements
SCHEMA_SQL = """
-- 对话会话表
CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed', 'archived'))
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
);

-- 用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id TEXT PRIMARY KEY,
    background TEXT,
    skill_level TEXT CHECK(skill_level IN ('beginner', 'intermediate', 'advanced', NULL)),
    learning_goals TEXT,
    time_availability TEXT,
    preferences TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 学习计划表
CREATE TABLE IF NOT EXISTS learning_plans (
    plan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    plan_content TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'approved', 'in_progress', 'completed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_plans_user ON learning_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_plans_conversation ON learning_plans(conversation_id);
"""


class DatabaseManager:
    """数据库管理器
    
    提供数据库连接管理和基本操作功能。
    """
    
    def __init__(self, database_path: str):
        """初始化数据库管理器
        
        Args:
            database_path: 数据库文件路径
        """
        self.database_path = database_path
        self._ensure_database_directory()
    
    def _ensure_database_directory(self):
        """确保数据库目录存在"""
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接
        
        Returns:
            SQLite 数据库连接对象
        """
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # 使用字典式访问
        return conn
    
    def execute_script(self, script: str):
        """执行 SQL 脚本
        
        Args:
            script: SQL 脚本内容
        """
        with self.get_connection() as conn:
            conn.executescript(script)
            conn.commit()
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch_one: bool = False,
    ) -> Optional[List[sqlite3.Row]]:
        """执行查询
        
        Args:
            query: SQL 查询语句
            params: 查询参数
            fetch_one: 是否只获取一条记录
        
        Returns:
            查询结果列表或单条记录
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                return cursor.fetchone()
            return cursor.fetchall()
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """执行更新操作
        
        Args:
            query: SQL 更新语句
            params: 更新参数
        
        Returns:
            受影响的行数
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount


def init_database(database_path: str) -> DatabaseManager:
    """初始化数据库
    
    创建数据库文件和所有必需的表结构。
    
    Args:
        database_path: 数据库文件路径
    
    Returns:
        数据库管理器实例
    """
    logger.info(f"Initializing database at {database_path}")
    
    db_manager = DatabaseManager(database_path)
    
    try:
        # 执行 schema 创建脚本
        db_manager.execute_script(SCHEMA_SQL)
        logger.info("Database schema created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    return db_manager


def get_database_manager(database_path: str) -> DatabaseManager:
    """获取数据库管理器实例
    
    Args:
        database_path: 数据库文件路径
    
    Returns:
        数据库管理器实例
    """
    return DatabaseManager(database_path)


# Conversation management functions
def create_conversation(
    db_manager: DatabaseManager,
    conversation_id: str,
    user_id: str,
) -> bool:
    """创建新对话会话
    
    Args:
        db_manager: 数据库管理器
        conversation_id: 对话 ID
        user_id: 用户 ID
    
    Returns:
        是否创建成功
    """
    try:
        query = """
        INSERT OR IGNORE INTO conversations (conversation_id, user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """
        now = datetime.now()
        db_manager.execute_update(query, (conversation_id, user_id, now, now))
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        return False


def save_message(
    db_manager: DatabaseManager,
    conversation_id: str,
    role: str,
    content: str,
    agent: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> bool:
    """保存消息到数据库
    
    Args:
        db_manager: 数据库管理器
        conversation_id: 对话 ID
        role: 消息角色
        content: 消息内容
        agent: 智能体名称
        timestamp: 消息时间戳
    
    Returns:
        是否保存成功
    """
    try:
        query = """
        INSERT INTO messages (conversation_id, role, content, agent, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        db_manager.execute_update(query, (conversation_id, role, content, agent, timestamp))
        return True
    except Exception as e:
        logger.error(f"Failed to save message: {e}")
        return False


def load_messages(
    db_manager: DatabaseManager,
    conversation_id: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """加载对话消息
    
    Args:
        db_manager: 数据库管理器
        conversation_id: 对话 ID
        limit: 限制返回的消息数量
    
    Returns:
        消息列表
    """
    try:
        query = """
        SELECT role, content, agent, timestamp
        FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        rows = db_manager.execute_query(query, (conversation_id,))
        
        messages = []
        for row in rows:
            messages.append({
                "role": row["role"],
                "content": row["content"],
                "agent": row["agent"],
                "timestamp": datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else row["timestamp"],
            })
        
        return messages
    except Exception as e:
        logger.error(f"Failed to load messages: {e}")
        return []


def update_conversation_status(
    db_manager: DatabaseManager,
    conversation_id: str,
    status: str,
) -> bool:
    """更新对话状态
    
    Args:
        db_manager: 数据库管理器
        conversation_id: 对话 ID
        status: 新状态
    
    Returns:
        是否更新成功
    """
    try:
        query = """
        UPDATE conversations
        SET status = ?, updated_at = ?
        WHERE conversation_id = ?
        """
        db_manager.execute_update(query, (status, datetime.now(), conversation_id))
        return True
    except Exception as e:
        logger.error(f"Failed to update conversation status: {e}")
        return False
