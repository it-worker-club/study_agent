# Performance Monitoring Implementation

## Overview

The performance monitoring system provides comprehensive tracking and logging of system performance metrics, including:

- LLM API call latency and token usage
- Tool execution time
- Graph node execution time
- Conversation session statistics

This document describes the implementation and usage of the monitoring system.

## Architecture

### Components

1. **PerformanceMonitor**: Central class that collects and stores metrics
2. **Context Managers**: Convenient wrappers for monitoring code blocks
3. **Decorators**: Function decorators for automatic monitoring
4. **Structured Logging**: Enhanced logging with contextual information

### Metrics Collected

#### LLM Call Metrics
- Agent name
- Duration (seconds)
- Token count
- Success/failure status
- Error messages (if failed)

#### Tool Execution Metrics
- Tool name
- Duration (seconds)
- Success/failure status
- Error messages (if failed)

#### Node Execution Metrics
- Node name
- Duration (seconds)
- Success/failure status
- Error messages (if failed)

#### Conversation Metrics
- Conversation ID
- User ID
- Total duration
- Message count
- Success status

## Usage

### Basic Monitoring with Context Managers

```python
from src.utils.monitoring import (
    monitor_llm_call,
    monitor_tool_execution,
    monitor_node_execution,
)

# Monitor an LLM call
with monitor_llm_call("coordinator") as call_info:
    response = llm_client.call(prompt)
    call_info["tokens"] = response.usage.total_tokens

# Monitor a tool execution
with monitor_tool_execution("search_geektime_courses"):
    results = search_tool.execute(query)

# Monitor a node execution
with monitor_node_execution("course_advisor"):
    result_state = course_advisor_node(state)
```

### Monitoring with Decorators

```python
from src.utils.monitoring import monitor_function

@monitor_function(metric_type="node")
def coordinator_node(state):
    # Node implementation
    return updated_state

@monitor_function(metric_type="tool")
async def search_courses(query):
    # Tool implementation
    return results
```

### Recording Conversation Metrics

```python
from src.utils.monitoring import get_monitor

monitor = get_monitor()

# Record a conversation session
monitor.record_conversation(
    conversation_id="conv_123",
    user_id="user_456",
    duration=45.5,
    message_count=12,
    success=True,
)
```

### Getting Metrics Summary

```python
from src.utils.monitoring import get_monitor

monitor = get_monitor()

# Get summary as dictionary
summary = monitor.get_summary()

# Log summary to logger
monitor.log_summary()
```

## Structured Logging

The system supports structured JSON logging for better log aggregation and analysis.

### Enabling Structured Logging

```python
from src.utils.logger import setup_logger

logger = setup_logger(
    name="education_tutoring_system",
    level="INFO",
    structured=True,  # Enable JSON logging
    log_file="logs/system.json",
)
```

### Adding Context to Logs

```python
from src.utils.logger import add_context_to_logger, log_with_context

# Add persistent context to logger
add_context_to_logger(logger, {
    "user_id": "user123",
    "conversation_id": "conv456",
})

# Log with additional context
log_with_context(
    logger,
    "info",
    "Processing request",
    {"action": "course_search", "query": "Python"},
)
```

## Integration with Main Application

The monitoring system is integrated into the main application (`src/main.py`):

1. **Interactive Mode**: Tracks all conversations and displays statistics on demand
2. **Single Query Mode**: Records metrics for the query and displays summary
3. **Performance Statistics Command**: Users can type `stats` to view current metrics

### Example Output

```
性能统计 / Performance Statistics
============================================================

LLM_CALLS:
  total: 15
  successful: 14
  failed: 1
  avg_duration: 1.23
  total_tokens: 2450

TOOL_EXECUTIONS:
  total: 8
  successful: 8
  failed: 0
  avg_duration: 0.45

NODE_EXECUTIONS:
  total: 25
  successful: 25
  failed: 0
  avg_duration: 0.15

CONVERSATIONS:
  total: 2
  successful: 2
  avg_duration: 45.50
  avg_messages: 10.50
============================================================
```

## Configuration

Monitoring behavior can be configured through the system configuration file:

```yaml
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/tutoring_system.log"
  max_file_size: 10  # MB
  backup_count: 5
  structured: false  # Set to true for JSON logging
```

## Best Practices

1. **Use Context Managers**: Prefer context managers over manual timing for automatic error handling
2. **Add Token Counts**: Always record token counts for LLM calls when available
3. **Monitor Critical Paths**: Focus monitoring on performance-critical operations
4. **Review Metrics Regularly**: Use the summary feature to identify bottlenecks
5. **Enable Structured Logging**: Use JSON logging in production for better analysis

## Performance Impact

The monitoring system is designed to have minimal performance impact:

- Metrics collection: < 1ms overhead per operation
- Memory usage: Metrics stored in memory (consider periodic cleanup for long-running systems)
- Logging: Asynchronous file I/O to minimize blocking

## Future Enhancements

Potential improvements for the monitoring system:

1. **Metrics Export**: Export metrics to external monitoring systems (Prometheus, Grafana)
2. **Real-time Dashboards**: Web-based dashboard for live metrics visualization
3. **Alerting**: Automatic alerts for performance degradation or errors
4. **Metrics Persistence**: Store metrics in database for historical analysis
5. **Distributed Tracing**: Integration with OpenTelemetry for distributed systems

## Troubleshooting

### High LLM Latency

If LLM calls are slow:
1. Check vLLM server performance
2. Review token counts (large responses increase latency)
3. Consider adjusting temperature and max_tokens parameters

### Tool Execution Failures

If tools are failing frequently:
1. Check network connectivity
2. Review error messages in metrics
3. Verify tool configuration and credentials

### Memory Usage

If memory usage is high:
1. Periodically clear old metrics: `monitor.metrics.clear()`
2. Reduce metrics retention period
3. Consider exporting metrics to external storage

## Related Documentation

- [Logging Configuration](../src/utils/logger.py)
- [Main Application](../src/main.py)
- [Monitoring Examples](../examples/monitoring_example.py)

---

**文档版本**: 1.0  
**最后更新**: 2026-01-12  
**作者**: Tango  
**维护者**: Tango
