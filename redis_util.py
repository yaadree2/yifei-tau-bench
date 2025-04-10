import json
import os
import redis
from typing import Optional
def connect_to_redis(decode_responses):
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=decode_responses, socket_connect_timeout=1)
        r.ping()
    except redis.exceptions.ConnectionError as e:
        print(f"Could not connect to Redis to clear data: {e}. Old data might persist in visualizer.")

    return r


def push_to_redis(r: redis.Redis, task_id: int, role: str, content: Optional[str] = None, tool_calls: Optional[list] = None, tool_results: Optional[dict] = None, tool_name: Optional[str] = None):
    """Pushes a message dictionary to the Redis list for a given task."""
    if r is None:
        print(f"Skipping Redis push: No connection.")
        return
    try:
        message = {"role": role}
        if content:
            message["content"] = content
        if tool_calls:
            # Ensure tool calls are serializable (e.g., convert pydantic models)
            message["tool_calls"] = [tc if isinstance(tc, dict) else tc.model_dump() for tc in tool_calls]
        if tool_results:
             message["tool_results"] = tool_results # Assuming results are already serializable
             if tool_name:
                 message["tool_name"] = tool_name

        redis_key = f"conversation:{task_id}"
        r.rpush(redis_key, json.dumps(message))
        # Optional: Trim the list to prevent unbounded growth
        # r.ltrim(redis_key, -1000, -1) # Keep only the latest 1000 messages
    except redis.exceptions.ConnectionError as e:
        print(f"Redis connection error during push: {e}")
    except Exception as e:
        # Log other errors (e.g., serialization issues)
        print(f"Error pushing message to Redis for task {task_id}: {e}")