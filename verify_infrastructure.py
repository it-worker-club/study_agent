#!/usr/bin/env python3
"""
Infrastructure Verification Script
Verifies all base components are working correctly.
"""

import sys
from pathlib import Path

def verify_imports():
    """Verify all core modules can be imported."""
    print("=" * 60)
    print("VERIFYING MODULE IMPORTS")
    print("=" * 60)
    
    modules = [
        ("Configuration", "src.utils.config", "get_config"),
        ("State Management", "src.graph.state", "AgentState"),
        ("State Helpers", "src.graph.helpers", "create_initial_state"),
        ("vLLM Client", "src.llm.vllm_client", "VLLMClient"),
        ("Error Handler", "src.utils.error_handler", "ErrorHandler"),
        ("Tool Manager", "src.tools.tool_manager", "ToolManager"),
        ("MCP Playwright", "src.tools.mcp_playwright", "MCPPlaywrightClient"),
        ("Web Search", "src.tools.web_search", "WebSearchClient"),
    ]
    
    all_passed = True
    for name, module, item in modules:
        try:
            exec(f"from {module} import {item}")
            print(f"✓ {name:25} - OK")
        except Exception as e:
            print(f"✗ {name:25} - FAILED: {e}")
            all_passed = False
    
    print()
    return all_passed

def verify_configuration():
    """Verify configuration loading."""
    print("=" * 60)
    print("VERIFYING CONFIGURATION")
    print("=" * 60)
    
    try:
        from src.utils.config import get_config
        
        config_path = Path("config/system_config.yaml")
        if not config_path.exists():
            print(f"✗ Configuration file not found: {config_path}")
            return False
        
        config = get_config(str(config_path))
        
        # Verify key configuration sections
        checks = [
            ("vLLM API Base", hasattr(config.vllm, 'api_base')),
            ("vLLM Model Name", hasattr(config.vllm, 'model_name')),
            ("MCP Config", hasattr(config, 'mcp')),
            ("System Config", hasattr(config, 'system')),
            ("Database Path", hasattr(config.system, 'database_path')),
            ("Max Loop Count", hasattr(config.system, 'max_loop_count')),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {name:25} - {'OK' if passed else 'FAILED'}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n  vLLM Endpoint: {config.vllm.api_base}")
            print(f"  Model: {config.vllm.model_name}")
            print(f"  Database: {config.system.database_path}")
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        print()
        return False

def verify_state_management():
    """Verify state management."""
    print("=" * 60)
    print("VERIFYING STATE MANAGEMENT")
    print("=" * 60)
    
    try:
        from src.graph.helpers import create_initial_state, validate_state
        
        # Create a test state
        state = create_initial_state("test-conversation-123")
        
        checks = [
            ("State Creation", state is not None),
            ("Conversation ID", state.get("conversation_id") == "test-conversation-123"),
            ("Messages List", isinstance(state.get("messages"), list)),
            ("User Profile", "user_profile" in state),
            ("Loop Count", "loop_count" in state),
            ("State Validation", validate_state(state)),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {name:25} - {'OK' if passed else 'FAILED'}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print(f"\n  State has {len(state)} fields")
            print(f"  Initial loop count: {state['loop_count']}")
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"✗ State management failed: {e}")
        print()
        return False

def verify_vllm_client():
    """Verify vLLM client."""
    print("=" * 60)
    print("VERIFYING vLLM CLIENT")
    print("=" * 60)
    
    try:
        from src.llm.vllm_client import create_vllm_client
        from src.utils.config import get_config
        
        config = get_config("config/system_config.yaml")
        client = create_vllm_client(config.vllm)
        
        checks = [
            ("Client Creation", client is not None),
            ("Has Generate Method", hasattr(client, 'generate')),
            ("Has Check Health Method", hasattr(client, 'check_health')),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {name:25} - {'OK' if passed else 'FAILED'}")
            if not passed:
                all_passed = False
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"✗ vLLM client initialization failed: {e}")
        print()
        return False

def verify_tools():
    """Verify tool integration."""
    print("=" * 60)
    print("VERIFYING TOOL INTEGRATION")
    print("=" * 60)
    
    try:
        from src.tools.tool_manager import create_tool_manager
        from src.utils.config import get_config
        
        config = get_config("config/system_config.yaml")
        manager = create_tool_manager(config)
        
        status = manager.get_tool_status()
        
        checks = [
            ("Tool Manager Creation", manager is not None),
            ("MCP Playwright Available", status.get("mcp_playwright", False)),
            ("Web Search Available", status.get("web_search", False)),
            ("Search Courses Method", hasattr(manager, 'search_courses')),
            ("Search Web Method", hasattr(manager, 'search_web')),
        ]
        
        all_passed = True
        for name, passed in checks:
            status_symbol = "✓" if passed else "✗"
            print(f"{status_symbol} {name:30} - {'OK' if passed else 'FAILED'}")
            if not passed:
                all_passed = False
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"✗ Tool integration failed: {e}")
        print()
        return False

def verify_error_handler():
    """Verify error handler."""
    print("=" * 60)
    print("VERIFYING ERROR HANDLER")
    print("=" * 60)
    
    try:
        from src.utils.error_handler import ErrorHandler
        
        handler = ErrorHandler()
        
        checks = [
            ("Handler Creation", handler is not None),
            ("Handle LLM Error", hasattr(handler, 'handle_llm_error')),
            ("Handle Tool Error", hasattr(handler, 'handle_tool_error')),
            ("Handle State Error", hasattr(handler, 'handle_state_error')),
            ("Handle Routing Error", hasattr(handler, 'handle_routing_error')),
            ("Is Recoverable", hasattr(handler, 'is_recoverable_error')),
        ]
        
        all_passed = True
        for name, passed in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {name:25} - {'OK' if passed else 'FAILED'}")
            if not passed:
                all_passed = False
        
        print()
        return all_passed
        
    except Exception as e:
        print(f"✗ Error handler verification failed: {e}")
        print()
        return False

def main():
    """Run all verification checks."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "INFRASTRUCTURE VERIFICATION" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    results.append(("Module Imports", verify_imports()))
    results.append(("Configuration", verify_configuration()))
    results.append(("State Management", verify_state_management()))
    results.append(("vLLM Client", verify_vllm_client()))
    results.append(("Tool Integration", verify_tools()))
    results.append(("Error Handler", verify_error_handler()))
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name:25} - {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ ALL INFRASTRUCTURE COMPONENTS VERIFIED SUCCESSFULLY!\n")
        return 0
    else:
        print("\n✗ SOME INFRASTRUCTURE COMPONENTS FAILED VERIFICATION\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
