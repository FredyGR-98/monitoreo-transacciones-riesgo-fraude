"""Endpoints de inferencia individual y por lotes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.models import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionResponse,
    TransactionInput,
)
from src.api.services import PredictionService, get_prediction_service


logger = logging.getLogger(__name__)

router = APIRouter(tags=["Predicción"])


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Predecir una transacción",
)
def predict(
    transaction: TransactionInput,
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    """Calcula la probabilidad de fraude para una transacción individual.

    Parámetros:
        transaction (TransactionInput): Datos validados de la transacción.
        prediction_service (PredictionService): Servicio con pipeline y umbral cargados.

    Retorna:
        PredictionResponse: Resultado de clasificación y probabilidad estimada.
    """
    try:
        result = prediction_service.predict(transaction)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # pragma: no cover - fallback defensivo
        logger.exception("Fallo inesperado durante la predicción individual")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al generar la predicción.",
        ) from error

    return PredictionResponse(**result)


@router.post(
    "/predict/batch",
    response_model=BatchPredictionResponse,
    summary="Predecir múltiples transacciones",
)
def predict_batch(
    payload: BatchPredictionRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> BatchPredictionResponse:
    """Calcula inferencia para un lote de transacciones.

    Parámetros:
        payload (BatchPredictionRequest): Lote validado de transacciones.
        prediction_service (PredictionService): Servicio reutilizado de inferencia.

    Retorna:
        BatchPredictionResponse: Cantidad procesada y lista de resultados.
    """
    try:
        results = prediction_service.predict_batch(payload.transactions)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:  # pragma: no cover - fallback defensivo
        logger.exception("Fallo inesperado durante la predicción por lotes")
        raise HTTPException(
            status_code=500,
            detail="Ocurrió un error interno al generar la predicción por lotes.",
        ) from error

    return BatchPredictionResponse(total=len(results), resultados=results)
