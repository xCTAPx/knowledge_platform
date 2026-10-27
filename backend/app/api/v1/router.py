from fastapi import APIRouter

from app.api.v1.endpoints import auth, conversations, feed, files, health, notes

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(notes.router, tags=["notes"])
api_router.include_router(files.router, tags=["files"])
api_router.include_router(feed.router, tags=["feed"])
api_router.include_router(conversations.router, tags=["conversations"])
