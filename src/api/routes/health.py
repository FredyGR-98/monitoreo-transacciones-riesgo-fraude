"""Endpoints de monitoreo y salud de la API."""

from fastapi import APIRouter, Depends

from src.api.models import HealthResponse, RootResponse
from src.api.services import PredictionService, get_prediction_service


router = APIRouter(tags=["Monitoreo"])


@router.get(
    "/",
    response_model=RootResponse,
    summary="Resumen de la API",
)
def root() -> RootResponse:
    """Entrega una vista resumida de la API y sus rutas principales.

    Retorna:
        RootResponse: Mensaje de bienvenida y resumen de endpoints disponibles.
    """
    return RootResponse(
        message="Bienvenido a la API de Monitoreo de Transacciones y Riesgo de Fraude.",
        docs_url="/docs",
        redoc_url="/redoc",
        endpoints={
            "/health": "Estado operativo de la API y del pipeline",
            "/model/info": "Metadatos del modelo y artefactos cargados",
            "/monitoring/powerbi": "Dataset plano de monitoreo para Power BI",
            "/predict": "Predicción individual para una transacción",
            "/predict/batch": "Predicción por lotes para múltiples transacciones",
        },
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verificar estado de la API",
)
def health(
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> HealthResponse:
    """Confirma que la API y el pipeline están disponibles.

    Parámetros:
        prediction_service (PredictionService): Servicio listo para servir inferencia.

    Retorna:
        HealthResponse: Estado, umbral y cantidad de variables esperadas.
    """
    return HealthResponse(**prediction_service.health_status())
