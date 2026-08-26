from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import from_url
from sqlalchemy.ext.asyncio import create_async_engine
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.health import check_dependencies
from app.api import router
from app.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.database = create_async_engine(settings.database_url, pool_pre_ping=True)
    app.state.redis = from_url(settings.redis_url, decode_responses=True)
    yield
    await app.state.redis.aclose()
    await app.state.database.dispose()


app = FastAPI(title="QueueFlow API", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def readiness(request: Request, response: Response) -> dict[str, object]:
    dependencies = await check_dependencies(
        request.app.state.database, request.app.state.redis
    )
    ready = all(dependencies.values())
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ready else "unavailable", "dependencies": dependencies}


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket) -> None:
    await websocket.accept()
    await websocket.send_json({"type": "connected"})
    while True:
        await websocket.receive_text()
