from typing import Any, Optional

_MEMORY_CACHE = {}

def get_from_cache(key: str) -> Optional[Any]:
    return _MEMORY_CACHE.get(key)

def set_to_cache(key: str, value: Any):
    _MEMORY_CACHE[key] = value
