import json
from typing import Any
import redis.asyncio as aioredis
from app.core.config import settings

class RedisService:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def close(self):
        if self.redis_client:
            await self.redis_client.close()

    async def publish_event(self, channel: str, message: dict):
        await self.connect()
        await self.redis_client.publish(channel, json.dumps(message))

    async def set_cache(self, key: str, value: Any, expire_seconds: int = 3600):
        await self.connect()
        await self.redis_client.set(key, json.dumps(value), ex=expire_seconds)

    async def get_cache(self, key: str) -> Any | None:
        await self.connect()
        data = await self.redis_client.get(key)
        if data:
            return json.loads(data)
        return None

    async def get_client(self) -> aioredis.Redis:
        await self.connect()
        return self.redis_client

redis_service = RedisService()
