"""Main entry point for the education tutoring system

This module provides the main application entry point with CLI interface
for running the education tutoring system. It supports both interactive
conversation mode and API server mode.
"""

import argparse
import asyncio
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.graph.builder import create_graph_with_persistence
from src.graph.state import AgentState, Message, UserProfile
from src.memory.database import DatabaseManager, init_database
from src.utils.config import get_config
from src.utils.logger import setup_logger, get_logger


class ConversationSession:
    """Manages a single conversation session with the tutoring system"""
    
    def __init__(self, graph, config, user_id: str, conversation_id: Optional[str] = None):
        """
        Initialize a conversation session.
        
        Args:
            graph: Compiled LangGraph instance
            config: System configuration
            user_id: User identifier
            conversation_id: Optional conversation ID (creates new if None)
        """
        self.graph = graph
        self.config = config
        self.user_id = user_id
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.logger = get_logger(__name__)
        
        # Initialize database manager for user profile persistence
        self.db_manager = DatabaseManager(config.system.database_path)
    
    def create_initial_state(self, user_message: str) -> AgentState:
        """
        Create initial state for a new conversation.
        
        Args:
            user_message: First user message
        
        Returns:
            Initial AgentState
        """
        # Try to load existing user profile
        from src.memory.checkpointer import load_user_profile
        user_profile = load_user_profile(self.db_manager, self.user_id)
        
        if not user_profile:
            # Create default user profile
            user_profile: UserProfile = {
                "user_id": self.user_id,
                "background": None,
                "skill_level": None,
                "learning_goals": [],
                "time_availability": None,
                "preferences": {},
            }
        
        # Create initial message
        initial_message: Message = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now(),
            "agent": None,
        }
        
        # Create initial state
        state: AgentState = {
            "messages": [initial_message],
            "conversation_id": self.conversation_id,
            "user_profile": user_profile,
            "current_task": None,
            "next_agent": None,
            "course_candidates": [],
            "learning_plan": None,
            "requires_human_input": False,
            "human_feedback": None,
            "loop_count": 0,
            "is_complete": False,
        }
        
        return state
    
    async def run_conversation(self, user_message: str) -> AgentState:
        """
        Run a conversation turn with the tutoring system.
        
        Args:
            user_message: User's input message
        
        Returns:
            Updated state after processing
        """
        try:
            # Create initial state
            state = self.create_initial_state(user_message)
            
            # Configure graph execution with thread_id for persistence
            config = {
                "configurable": {
                    "thread_id": self.conversation_id,
                }
            }
            
            self.logger.info(f"Starting conversation {self.conversation_id} for user {self.user_id}")
            
            # Execute graph
            result = await self.graph.ainvoke(state, config)
            
            self.logger.info(f"Conversation turn completed")
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error in conversation: {e}", exc_info=True)
            raise
    
    async def continue_conversation(self, user_message: str, current_state: AgentState) -> AgentState:
        """
        Continue an existing conversation with new user input.
        
        Args:
            user_message: User's new message
            current_state: Current conversation state
        
        Returns:
            Updated state after processing
        """
        try:
            # Add new user message to state
            new_message: Message = {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now(),
                "agent": None,
            }
            
            current_state["messages"].append(new_message)
            current_state["requires_human_input"] = False
            current_state["human_feedback"] = user_message
            
            # Configure graph execution
            config = {
                "configurable": {
                    "thread_id": self.conversation_id,
                }
            }
            
            self.logger.info(f"Continuing conversation {self.conversation_id}")
            
            # Execute graph with updated state
            result = await self.graph.ainvoke(current_state, config)
            
            return result
        
        except Exception as e:
            self.logger.error(f"Error continuing conversation: {e}", exc_info=True)
            raise


async def run_interactive_mode(config):
    """
    Run the system in interactive CLI mode.
    
    Args:
        config: System configuration
    """
    logger = get_logger(__name__)
    
    # Import monitoring
    from src.utils.monitoring import get_monitor
    monitor = get_monitor()
    
    print("\n" + "="*60)
    print("欢迎使用教育辅导智能体系统")
    print("Education Tutoring System")
    print("="*60)
    print("\n输入 'quit' 或 'exit' 退出系统")
    print("输入 'new' 开始新对话")
    print("输入 'help' 查看帮助信息")
    print("输入 'stats' 查看性能统计\n")
    
    try:
        # Initialize graph with persistence
        logger.info("Initializing system...")
        graph = await create_graph_with_persistence(
            database_path=config.system.database_path,
            max_loop_count=config.system.max_loop_count,
        )
        logger.info("System initialized successfully")
        
        # Get or create user ID
        user_id = input("请输入您的用户ID（或按回车使用默认）: ").strip()
        if not user_id:
            user_id = "default_user"
        
        # Create conversation session
        session = ConversationSession(graph, config, user_id)
        current_state = None
        conversation_start_time = time.time()
        
        print(f"\n已为用户 {user_id} 创建会话 {session.conversation_id}")
        print("请输入您的问题或需求：\n")
        
        while True:
            try:
                # Get user input
                user_input = input("您: ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit']:
                    # Record conversation metrics
                    conversation_duration = time.time() - conversation_start_time
                    message_count = len(current_state["messages"]) if current_state else 0
                    monitor.record_conversation(
                        conversation_id=session.conversation_id,
                        user_id=user_id,
                        duration=conversation_duration,
                        message_count=message_count,
                        success=True,
                    )
                    
                    # Log performance summary
                    monitor.log_summary()
                    
                    print("\n感谢使用！再见！")
                    break
                
                if user_input.lower() == 'new':
                    # Record previous conversation
                    if current_state:
                        conversation_duration = time.time() - conversation_start_time
                        message_count = len(current_state["messages"])
                        monitor.record_conversation(
                            conversation_id=session.conversation_id,
                            user_id=user_id,
                            duration=conversation_duration,
                            message_count=message_count,
                            success=True,
                        )
                    
                    # Start new conversation
                    session = ConversationSession(graph, config, user_id)
                    current_state = None
                    conversation_start_time = time.time()
                    print(f"\n已创建新会话 {session.conversation_id}")
                    print("请输入您的问题或需求：\n")
                    continue
                
                if user_input.lower() == 'help':
                    print("\n可用命令：")
                    print("  quit/exit - 退出系统")
                    print("  new - 开始新对话")
                    print("  help - 显示此帮助信息")
                    print("  stats - 显示性能统计")
                    print("\n您可以询问：")
                    print("  - 课程推荐（例如：我想学习Python数据分析）")
                    print("  - 学习计划（例如：帮我制定一个学习计划）")
                    print("  - 课程详情（例如：这门课程适合我吗？）\n")
                    continue
                
                if user_input.lower() == 'stats':
                    print("\n" + "="*60)
                    print("性能统计 / Performance Statistics")
                    print("="*60)
                    summary = monitor.get_summary()
                    for category, stats in summary.items():
                        print(f"\n{category.upper()}:")
                        for key, value in stats.items():
                            if isinstance(value, float):
                                print(f"  {key}: {value:.2f}")
                            else:
                                print(f"  {key}: {value}")
                    print("="*60 + "\n")
                    continue
                
                # Process user input
                if current_state is None:
                    # First message in conversation
                    current_state = await session.run_conversation(user_input)
                else:
                    # Continue existing conversation
                    current_state = await session.continue_conversation(user_input, current_state)
                
                # Display assistant responses
                print()
                for message in current_state["messages"]:
                    if message["role"] == "assistant" and message.get("agent"):
                        agent_name = message["agent"]
                        content = message["content"]
                        print(f"{agent_name}: {content}\n")
                
                # Check if conversation is complete
                if current_state.get("is_complete"):
                    print("对话已完成。输入 'new' 开始新对话，或继续提问。\n")
            
            except KeyboardInterrupt:
                print("\n\n检测到中断。输入 'quit' 退出或继续对话。\n")
                continue
            
            except Exception as e:
                logger.error(f"Error processing input: {e}", exc_info=True)
                print(f"\n抱歉，处理您的请求时出现错误：{e}")
                print("请重试或输入 'new' 开始新对话。\n")
    
    except Exception as e:
        logger.error(f"Fatal error in interactive mode: {e}", exc_info=True)
        print(f"\n系统错误：{e}")
        sys.exit(1)


async def run_single_query(config, query: str, user_id: str = "cli_user"):
    """
    Run a single query and exit (non-interactive mode).
    
    Args:
        config: System configuration
        query: User query
        user_id: User identifier
    """
    logger = get_logger(__name__)
    
    # Import monitoring
    from src.utils.monitoring import get_monitor
    monitor = get_monitor()
    
    try:
        # Initialize graph
        logger.info("Initializing system...")
        start_time = time.time()
        
        graph = await create_graph_with_persistence(
            database_path=config.system.database_path,
            max_loop_count=config.system.max_loop_count,
        )
        
        # Create session and run query
        session = ConversationSession(graph, config, user_id)
        result = await session.run_conversation(query)
        
        # Record conversation metrics
        duration = time.time() - start_time
        message_count = len(result["messages"])
        monitor.record_conversation(
            conversation_id=session.conversation_id,
            user_id=user_id,
            duration=duration,
            message_count=message_count,
            success=True,
        )
        
        # Print results
        print("\n" + "="*60)
        print("查询结果 / Query Result")
        print("="*60 + "\n")
        
        for message in result["messages"]:
            if message["role"] == "assistant":
                agent = message.get("agent", "System")
                print(f"[{agent}]")
                print(message["content"])
                print()
        
        # Log performance summary
        monitor.log_summary()
        
        return result
    
    except Exception as e:
        logger.error(f"Error in single query mode: {e}", exc_info=True)
        print(f"\n错误：{e}")
        sys.exit(1)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="教育辅导智能体系统 / Education Tutoring System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径 (默认: config/system_config.yaml)",
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["interactive", "query"],
        default="interactive",
        help="运行模式：interactive (交互式) 或 query (单次查询)",
    )
    
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="单次查询模式下的查询内容",
    )
    
    parser.add_argument(
        "--user-id",
        type=str,
        default="cli_user",
        help="用户ID (默认: cli_user)",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=None,
        help="日志级别 (覆盖配置文件设置)",
    )
    
    return parser.parse_args()


async def async_main():
    """Async main function"""
    args = parse_arguments()
    
    try:
        # Load configuration
        config = get_config(args.config)
        
        # Override log level if specified
        if args.log_level:
            config.logging.level = args.log_level
        
        # Setup logging
        logger = setup_logger(
            name="education_tutoring_system",
            level=config.logging.level,
            log_format=config.logging.format,
            log_file=config.logging.file,
            max_file_size=config.logging.max_file_size,
            backup_count=config.logging.backup_count,
        )
        
        logger.info("="*60)
        logger.info("Education Tutoring System Starting")
        logger.info("="*60)
        logger.info(f"Configuration: {args.config or 'config/system_config.yaml'}")
        logger.info(f"Database: {config.system.database_path}")
        logger.info(f"vLLM endpoint: {config.vllm.api_base}")
        logger.info(f"Mode: {args.mode}")
        
        # Initialize database
        init_database(config.system.database_path)
        logger.info("Database initialized")
        
        # Run in selected mode
        if args.mode == "interactive":
            await run_interactive_mode(config)
        elif args.mode == "query":
            if not args.query:
                print("错误：query 模式需要 --query 参数")
                sys.exit(1)
            await run_single_query(config, args.query, args.user_id)
        
        logger.info("System shutdown complete")
    
    except FileNotFoundError as e:
        print(f"配置错误: {e}", file=sys.stderr)
        print("请确保配置文件存在: config/system_config.yaml", file=sys.stderr)
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n系统已中断")
        sys.exit(0)
    
    except Exception as e:
        print(f"系统错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point"""
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
