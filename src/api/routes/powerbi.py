"""Endpoint plano para consumo de monitoreo desde Power BI."""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.api.config import RUTA_POWERBI_DATA
from src.api.models import PowerBITransactionResponse


router = APIRouter(tags=["Monitoreo"])


@router.get(
    "/monitoring/powerbi",
    response_model=list[PowerBITransactionResponse],
    summary="Obtener dataset de monitoreo para Power BI",
)
def get_powerbi_monitoring_data() -> list[PowerBITransactionResponse]:
    """Entrega el dataset plano para consumo directo desde Power BI.

    Retorna:
        list[PowerBITransactionResponse]: Registros listos para analítica externa.
    """
    if not RUTA_POWERBI_DATA.exists():
        raise HTTPException(
            status_code=404,
            detail=(
                "El dataset para Power BI aún no existe. Ejecuta primero una corrida "
                "de monitoreo desde la app para generar el archivo base."
            ),
        )

    dataframe = pd.read_csv(RUTA_POWERBI_DATA)
    if dataframe.empty:
        return []

    records: list[dict[str, Any]] = (
        dataframe.where(pd.notna(dataframe), None).to_dict(orient="records")
    )
    return [PowerBITransactionResponse(**record) for record in records]
