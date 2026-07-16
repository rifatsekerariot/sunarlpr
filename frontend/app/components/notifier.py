import os
import asyncio
import json
import redis.asyncio as aioredis
from nicegui import ui
import structlog
from app.api_client import api_client

logger = structlog.get_logger()

# Shared set of active UI WebSockets/Sessions to broadcast notifications to
active_listeners = set()

async def redis_listener():
    """Background task to listen to Redis Pub/Sub and broadcast plate detection events to NiceGUI clients."""
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
    while True:
        try:
            logger.info("Connecting to Redis Pub/Sub for UI events...")
            r = await aioredis.from_url(redis_url, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe("lpr_events")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    logger.info("Received event from Redis", data=data)
                    # Dispatch to all active NiceGUI client queues/callbacks
                    for callback in list(active_listeners):
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error("Failed to call UI update listener", error=str(e))
                            active_listeners.remove(callback)
            await asyncio.sleep(1)
        except Exception as e:
            logger.error("Redis Pub/Sub listener disconnected, retrying in 5 seconds", error=str(e))
            await asyncio.sleep(5)
