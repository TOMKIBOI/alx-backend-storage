#!/usr/bin/env python3
"""Writing strings to Redis"""
import redis
import uuid
from typing import Union, Optional, Callable
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """Decorator that counts how many times a function is called"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self._redis.incr(method.__qualname__)
        return method(self, *args, **kwargs)
    return wrapper

# Storing lists


def call_history(method: Callable) -> Callable:
    """Decorator that stores the history"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"

        # convert args to string
        self._redis.rpush(input_key, str(args))

        # call the original method and get the output
        output = method(self, *args, **kwargs)

        # convert output to string and store in redis
        self._redis.rpush(output_key, str(output))

        return output
    return wrapper


class Cache:
    """Cache class"""

    def __init__(self) -> None:
        """Constructor"""
        self._redis = redis.Redis()
        self._redis.flushdb()

    # Storing data in Redis
    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """Store data in Redis"""
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    # Reading from Redis and recovering original type
    def get(self, key: str, fn: Optional[Callable] =
            None) -> Union[str, bytes, int, float]:
        """Get data from Redis"""
        value = self._redis.get(key)
        if fn:
            return fn(value)
        return value

    # Retrieving lists using replay functionality
    def replay(self, method: Callable) -> str:
        """Replay data"""
        method_name = method.__qualname__
        inputs = self._redis.lrange(f"{method_name}:inputs", 0, -1)
        outputs = self._redis.lrange(f"{method_name}:outputs", 0, -1)

        for i, o in zip(inputs, outputs):
            print(f"{method_name}({i.decode('utf-8')}) -> {o.decode('utf-8')}")

    def get_str(self, key: str) -> Optional[str]:
        """Get data from Redis as string"""
        return self.get(key, lambda x: x.decode('utf-8'))

    def get_int(self, key: str) -> Optional[int]:
        """Get data from Redis as int"""
        return self.get(key, lambda x: int(x))

    def get_call_history(self, method_name: str) -> str:
        """Get call history"""
        return self._redis.lrange(f"{method_name}:inputs", 0, -1),
        self._redis.lrange(f"{method_name}:outputs", 0, -1)
