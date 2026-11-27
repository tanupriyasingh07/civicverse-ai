import json
from typing import Any, Optional
import redis
from app.core.config import settings


class CacheService:
    def __init__(self) -> None:
        self._memory_fallback: dict[str, str] = {}
        try:
            self._client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            self._client.ping()
            self._use_redis = True
        except Exception:
            self._client = None
            self._use_redis = False

    def set_json(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        serialized = json.dumps(value)
        if self._use_redis and self._client:
            try:
                self._client.setex(key, ttl_seconds, serialized)
                return
            except Exception:
                pass
        self._memory_fallback[key] = serialized

    def get_json(self, key: str) -> Optional[Any]:
        raw: Optional[str] = None
        if self._use_redis and self._client:
            try:
                raw = self._client.get(key)
            except Exception:
                raw = None
        if raw is None:
            raw = self._memory_fallback.get(key)
        return json.loads(raw) if raw else None


cache_service = CacheService()
