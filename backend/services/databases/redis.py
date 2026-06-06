import logging
import json
from redis.asyncio import Redis
from backend.config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._client = None

    async def connect(self):
        if not self._client:
            try:
                self._client = Redis.from_url(self.redis_url, decode_responses=True)
                await self._client.ping()
                logger.info("Successfully connected to Redis.")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._client = None

    async def get(self, key: str):
        if not self._client:
            await self.connect()
        if not self._client:
            return None
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None

    async def set(self, key: str, value: str, expire_seconds: int = None):
        if not self._client:
            await self.connect()
        if not self._client:
            return False
        try:
            await self._client.set(key, value, ex=expire_seconds)
            return True
        except Exception as e:
            logger.error(f"Redis set failed: {e}")
            return False

    async def get_json(self, key: str):
        val = await self.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return None
        return None

    async def set_json(self, key: str, data: dict, expire_seconds: int = None):
        try:
            val = json.dumps(data)
            return await self.set(key, val, expire_seconds)
        except Exception as e:
            logger.error(f"Redis set_json failed: {e}")
            return False

    async def delete(self, key: str):
        if not self._client:
            await self.connect()
        if not self._client:
            return False
        try:
            await self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete failed: {e}")
            return False

redis_client = RedisClient()
