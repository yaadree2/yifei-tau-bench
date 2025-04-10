import os
import redis

def connect_to_redis(decode_responses):
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        r = redis.Redis(host=redis_host, port=redis_port, decode_responses=decode_responses, socket_connect_timeout=1)
        r.ping()
    except redis.exceptions.ConnectionError as e:
        print(f"Could not connect to Redis to clear data: {e}. Old data might persist in visualizer.")

    return r