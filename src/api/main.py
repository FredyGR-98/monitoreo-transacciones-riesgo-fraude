"""Punto de entrada principal para la API FastAPI de fraude."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.config import API_DESCRIPTION, API_TAGS_METADATA, API_TITLE, API_VERSION
from src.api.routes import health_router, model_router, powerbi_router, predictions_router
from src.api.services import get_prediction_service


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Gestiona la inicialización de artefactos al arrancar la API.

    Parámetros:
        _ (FastAPI): Instancia de la aplicación recibida por FastAPI.

    Retorna:
        AsyncGenerator: Contexto de vida útil de la aplicación.
    """
    prediction_service = get_prediction_service()
    logger.info("API inicializada con el modelo %s", prediction_service.model_name)
    yield


def create_app() -> FastAPI:
    """Construye la aplicación FastAPI y registra sus routers.

    Retorna:
        FastAPI: Aplicación lista para exponer endpoints de salud, modelo e inferencia.
    """
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        lifespan=lifespan,
        openapi_tags=API_TAGS_METADATA,
    )

    app.include_router(health_router)
    app.include_router(model_router)
    app.include_router(powerbi_router)
    app.include_router(predictions_router)

    return app


app = create_app()
