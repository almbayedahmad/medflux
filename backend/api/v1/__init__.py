from fastapi import APIRouter
from .routes import router as routes

api_v1 = APIRouter()
api_v1.include_router(routes)

__all__ = ["api_v1"]
