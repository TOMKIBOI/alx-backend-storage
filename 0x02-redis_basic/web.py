#!/usr/bin/env python3
""" Implementing an expiring web cache and tracker"""
import redis
import requests
from typing import Callable
from functools import wraps

red = redis.Redis()
red.flushdb()


def count(method: Callable) -> Callable:
    """Decorator that increments the count for a key"""
    @wraps(method)
    def wrapper(*args, **kwargs):
        """Wrapper function"""
        red.incr(method.__qualname__)
        return method(*args, **kwargs)
    return wrapper


def get_page(url: str) -> str:
    """Get the HTML content of a page"""
    cache_key = f"count:{url}"
    cached_content = red.get(url)
    if cached_content:
        return cached_content.decode()

    response = requests.get(url)
    content = response.text

    red.setex(cache_key, 10, content)

    return content


@count
def get_page(url: str) -> str:
    """Get the HTML content of a page"""
    cache_key = f"count:{url}"
    cached_content = red.get(url)
    if cached_content:
        return cached_content.decode()

    response = requests.get(url)
    content = response.text

    red.setex(cache_key, 10, content)

    return content


red.set("get_page", 0)
