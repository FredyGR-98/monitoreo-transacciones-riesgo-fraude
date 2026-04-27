"""Routers de la API de fraude."""

from src.api.routes.health import router as health_router
from src.api.routes.model import router as model_router
from src.api.routes.powerbi import router as powerbi_router
from src.api.routes.predictions import router as predictions_router

__all__ = ["health_router", "model_router", "powerbi_router", "predictions_router"]
