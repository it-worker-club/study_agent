"""Checkpointer implementation for LangGraph state persistence.

This module provides AsyncSQLiteSaver integration for LangGraph,
along with user profile and learning plan persistence functions.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.graph.state import UserProfile, LearningPlan, CourseInfo
from src.memory.database import DatabaseManager

logger = logging.getLogger(__name__)


async def get_checkpointer(database_path: str) -> AsyncSqliteSaver:
    """获取 LangGraph AsyncSQLiteSaver 实例
    
    Args:
        database_path: 数据库文件路径
    
    Returns:
        配置好的 AsyncSqliteSaver 实例
    """
    try:
        # 使用 LangGraph 的 AsyncSqliteSaver
        # from_conn_string 返回一个 async context manager
        # 我们需要使用 async with 来获取实际的 checkpointer
        checkpointer = AsyncSqliteSaver.from_conn_string(database_path)
        
        logger.info(f"Initialized AsyncSqliteSaver with database: {database_path}")
        return checkpointer
    except Exception as e:
        logger.error(f"Failed to initialize checkpointer: {e}")
        raise


def save_user_profile(
    db_manager: DatabaseManager,
    user_profile: UserProfile,
) -> bool:
    """保存用户画像到数据库
    
    Args:
        db_manager: 数据库管理器
        user_profile: 用户画像数据
    
    Returns:
        是否保存成功
    """
    try:
        # 将列表和字典序列化为 JSON
        learning_goals_json = json.dumps(user_profile.get("learning_goals", []), ensure_ascii=False)
        preferences_json = json.dumps(user_profile.get("preferences", {}), ensure_ascii=False)
        
        # 使用 INSERT OR REPLACE 实现 upsert
        query = """
        INSERT OR REPLACE INTO user_profiles 
        (user_id, background, skill_level, learning_goals, time_availability, preferences, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            user_profile["user_id"],
            user_profile.get("background"),
            user_profile.get("skill_level"),
            learning_goals_json,
            user_profile.get("time_availability"),
            preferences_json,
            datetime.now(),
        )
        
        db_manager.execute_update(query, params)
        logger.info(f"Saved user profile for user {user_profile['user_id']}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to save user profile: {e}")
        return False


def load_user_profile(
    db_manager: DatabaseManager,
    user_id: str,
) -> Optional[UserProfile]:
    """从数据库加载用户画像
    
    Args:
        db_manager: 数据库管理器
        user_id: 用户 ID
    
    Returns:
        用户画像数据，如果不存在则返回 None
    """
    try:
        query = """
        SELECT user_id, background, skill_level, learning_goals, 
               time_availability, preferences
        FROM user_profiles
        WHERE user_id = ?
        """
        
        row = db_manager.execute_query(query, (user_id,), fetch_one=True)
        
        if not row:
            logger.info(f"No user profile found for user {user_id}")
            return None
        
        # 反序列化 JSON 字段
        learning_goals = json.loads(row["learning_goals"]) if row["learning_goals"] else []
        preferences = json.loads(row["preferences"]) if row["preferences"] else {}
        
        user_profile: UserProfile = {
            "user_id": row["user_id"],
            "background": row["background"],
            "skill_level": row["skill_level"],
            "learning_goals": learning_goals,
            "time_availability": row["time_availability"],
            "preferences": preferences,
        }
        
        logger.info(f"Loaded user profile for user {user_id}")
        return user_profile
    
    except Exception as e:
        logger.error(f"Failed to load user profile: {e}")
        return None


def save_learning_plan(
    db_manager: DatabaseManager,
    conversation_id: str,
    user_id: str,
    learning_plan: LearningPlan,
) -> Optional[int]:
    """保存学习计划到数据库
    
    Args:
        db_manager: 数据库管理器
        conversation_id: 对话 ID
        user_id: 用户 ID
        learning_plan: 学习计划数据
    
    Returns:
        学习计划 ID，如果保存失败则返回 None
    """
    try:
        # 将学习计划序列化为 JSON
        plan_content = {
            "goal": learning_plan["goal"],
            "milestones": learning_plan["milestones"],
            "recommended_courses": learning_plan["recommended_courses"],
            "estimated_duration": learning_plan["estimated_duration"],
            "created_at": learning_plan["created_at"].isoformat() if isinstance(learning_plan["created_at"], datetime) else learning_plan["created_at"],
        }
        plan_content_json = json.dumps(plan_content, ensure_ascii=False)
        
        query = """
        INSERT INTO learning_plans 
        (conversation_id, user_id, goal, plan_content, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now()
        params = (
            conversation_id,
            user_id,
            learning_plan["goal"],
            plan_content_json,
            learning_plan.get("status", "draft"),
            now,
            now,
        )
        
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            plan_id = cursor.lastrowid
        
        logger.info(f"Saved learning plan {plan_id} for user {user_id}")
        return plan_id
    
    except Exception as e:
        logger.error(f"Failed to save learning plan: {e}")
        return None


def load_learning_plan(
    db_manager: DatabaseManager,
    plan_id: Optional[int] = None,
    conversation_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Optional[LearningPlan]:
    """从数据库加载学习计划
    
    可以通过 plan_id、conversation_id 或 user_id 查询。
    如果提供多个参数，优先级为：plan_id > conversation_id > user_id
    
    Args:
        db_manager: 数据库管理器
        plan_id: 学习计划 ID
        conversation_id: 对话 ID（加载该对话的最新计划）
        user_id: 用户 ID（加载该用户的最新计划）
    
    Returns:
        学习计划数据，如果不存在则返回 None
    """
    try:
        if plan_id:
            query = """
            SELECT plan_id, goal, plan_content, status, created_at
            FROM learning_plans
            WHERE plan_id = ?
            """
            params = (plan_id,)
        elif conversation_id:
            query = """
            SELECT plan_id, goal, plan_content, status, created_at
            FROM learning_plans
            WHERE conversation_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """
            params = (conversation_id,)
        elif user_id:
            query = """
            SELECT plan_id, goal, plan_content, status, created_at
            FROM learning_plans
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """
            params = (user_id,)
        else:
            logger.warning("No query parameter provided for load_learning_plan")
            return None
        
        row = db_manager.execute_query(query, params, fetch_one=True)
        
        if not row:
            logger.info("No learning plan found")
            return None
        
        # 反序列化 JSON 内容
        plan_content = json.loads(row["plan_content"])
        
        learning_plan: LearningPlan = {
            "goal": plan_content["goal"],
            "milestones": plan_content["milestones"],
            "recommended_courses": plan_content["recommended_courses"],
            "estimated_duration": plan_content["estimated_duration"],
            "created_at": datetime.fromisoformat(plan_content["created_at"]) if isinstance(plan_content["created_at"], str) else plan_content["created_at"],
            "status": row["status"],
        }
        
        logger.info(f"Loaded learning plan {row['plan_id']}")
        return learning_plan
    
    except Exception as e:
        logger.error(f"Failed to load learning plan: {e}")
        return None


def update_learning_plan_status(
    db_manager: DatabaseManager,
    plan_id: int,
    status: str,
) -> bool:
    """更新学习计划状态
    
    Args:
        db_manager: 数据库管理器
        plan_id: 学习计划 ID
        status: 新状态 (draft/approved/in_progress/completed)
    
    Returns:
        是否更新成功
    """
    try:
        query = """
        UPDATE learning_plans
        SET status = ?, updated_at = ?
        WHERE plan_id = ?
        """
        
        db_manager.execute_update(query, (status, datetime.now(), plan_id))
        logger.info(f"Updated learning plan {plan_id} status to {status}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to update learning plan status: {e}")
        return False


def list_user_learning_plans(
    db_manager: DatabaseManager,
    user_id: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """列出用户的所有学习计划
    
    Args:
        db_manager: 数据库管理器
        user_id: 用户 ID
        limit: 返回的最大计划数
    
    Returns:
        学习计划列表（简要信息）
    """
    try:
        query = """
        SELECT plan_id, goal, status, created_at, updated_at
        FROM learning_plans
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """
        
        rows = db_manager.execute_query(query, (user_id, limit))
        
        plans = []
        for row in rows:
            plans.append({
                "plan_id": row["plan_id"],
                "goal": row["goal"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        
        return plans
    
    except Exception as e:
        logger.error(f"Failed to list learning plans: {e}")
        return []
