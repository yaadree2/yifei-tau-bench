import json
import os
import redis
from typing import Optional
from pydantic import BaseModel
from cashier.model.model_util import CustomJSONEncoder

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


def push_assistant_to_redis(
    r: redis.Redis,
    task_id: int,
    uuid: str,
    assistant_turns,
):    
    redis_key = f"{MESSAGES_KEY_PREFIX}{uuid}:{task_id}"
    serialized_turns = [json.dumps(turn, cls=CustomJSONEncoder) for turn in assistant_turns]
    r.rpush(redis_key, *serialized_turns)

def push_user_to_redis(
    r: redis.Redis,
    task_id: int,
    uuid: str,
    msg: str,
):    
    redis_key = f"{MESSAGES_KEY_PREFIX}{uuid}:{task_id}"
    r.rpush(redis_key, json.dumps({"role": "user", "content": msg}))

def push_to_redis_final_reward(
    r: redis.Redis,
    uuid: str,
    reward: int,
):
    redis_key = f"{SUMMARY_KEY_PREFIX}{uuid}"
    r.set(redis_key, RedisSummary(reward=reward).model_dump_json())