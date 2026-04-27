"""Endpoints de observabilidad y metadatos del modelo desplegado."""

from fastapi import APIRouter, Depends

from src.api.models import ModelInfoResponse
from src.api.services import PredictionService, get_prediction_service


router = APIRouter(tags=["Modelo"])


@router.get(
    "/model/info",
    response_model=ModelInfoResponse,
    summary="Consultar metadatos del modelo",
)
def model_info(
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> ModelInfoResponse:
    """Expone metadatos útiles para inspeccionar el pipeline en producción.

    Parámetros:
        prediction_service (PredictionService): Servicio de inferencia activo.

    Retorna:
        ModelInfoResponse: Nombre, familia, variables y métricas del modelo desplegado.
    """
    return ModelInfoResponse(**prediction_service.model_info())
