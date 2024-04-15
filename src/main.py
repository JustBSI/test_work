from fastapi import FastAPI
from src.files.router import router as router_file
from redis import asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache
from fastapi_cache.backends.redis import RedisBackend

app = FastAPI(
    title="File manager"
)


app.include_router(router_file)


@app.on_event("startup")
async def startup_event():
    redis = aioredis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
