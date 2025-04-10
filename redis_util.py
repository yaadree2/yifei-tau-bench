import json
import os
import redis
from typing import Optional
from pydantic import BaseModel

class RedisSummary(BaseModel):
    reward: int

MESSAGES_KEY_PREFIX = "tau_bench:messages:"

SUMMARY_KEY_PREFIX = "tau_bench:summary:"

def connect_to_redis(decode_responses):
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    r = redis.Redis(
        host=redis_host,
        port=redis_port,
        decode_responses=decode_responses,
        socket_connect_timeout=1,
    )
    r.ping()

    return r


def push_to_redis(
    r: redis.Redis,
    task_id: int,
    uuid: str,
    role: str,
    content: Optional[str] = None,
    tool_calls: Optional[list] = None,
    tool_results: Optional[dict] = None,
    tool_name: Optional[str] = None,
):
    message = {"role": role}
    if content:
        message["content"] = content
    if tool_calls:
        # Ensure tool calls are serializable (e.g., convert pydantic models)
        message["tool_calls"] = [
            tc if isinstance(tc, dict) else tc.model_dump() for tc in tool_calls
        ]
    if tool_results:
        message["tool_results"] = (
            tool_results  # Assuming results are already serializable
        )
        if tool_name:
            message["tool_name"] = tool_name

    redis_key = f"{MESSAGES_KEY_PREFIX}{uuid}:{task_id}"
    r.rpush(redis_key, json.dumps(message))


def push_to_redis_final_reward(
    r: redis.Redis,
    uuid: str,
    reward: int,
):
    redis_key = f"{SUMMARY_KEY_PREFIX}{uuid}"
    r.set(redis_key, RedisSummary(reward=reward).model_dump_json())