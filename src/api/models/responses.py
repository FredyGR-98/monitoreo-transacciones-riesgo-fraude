"""Esquemas de salida para la API de fraude."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    """Respuesta pública para una predicción individual."""

    fraude: int = Field(..., description="Predicción binaria final del modelo.")
    probabilidad: float = Field(..., description="Probabilidad estimada de fraude.")
    threshold_aplicado: float = Field(..., description="Threshold usado para la decisión final.")
    modelo: str = Field(..., description="Nombre del modelo cargado en la API.")


class BatchPredictionResponse(BaseModel):
    """Respuesta pública para inferencia por lotes."""

    total: int = Field(..., description="Cantidad total de transacciones procesadas.")
    resultados: list[PredictionResponse] = Field(
        ...,
        description="Predicciones generadas para cada transacción del lote.",
    )


class HealthResponse(BaseModel):
    """Respuesta del endpoint de salud del servicio."""

    status: str = Field(..., description="Estado general del servicio.")
    modelo: str = Field(..., description="Nombre del modelo cargado.")
    threshold: float = Field(..., description="Threshold actual del servicio.")
    features_esperadas: int = Field(..., description="Cantidad de variables requeridas.")


class RootResponse(BaseModel):
    """Respuesta del endpoint raíz de la API."""

    message: str = Field(..., description="Mensaje de bienvenida de la API.")
    docs_url: str = Field(..., description="Ruta de acceso a Swagger UI.")
    redoc_url: str = Field(..., description="Ruta de acceso a ReDoc.")
    endpoints: dict[str, str] = Field(
        ...,
        description="Resumen de endpoints principales disponibles.",
    )


class ModelInfoResponse(BaseModel):
    """Resumen del modelo y de los artefactos cargados por la API."""

    modelo: str = Field(..., description="Nombre lógico del modelo.")
    familia_modelo: str | None = Field(None, description="Familia algorítmica del modelo.")
    escenario: str | None = Field(None, description="Escenario operativo representado por el pipeline.")
    target: str | None = Field(None, description="Variable objetivo del modelo.")
    threshold: float = Field(..., description="Threshold aplicado en inferencia.")
    features: list[str] = Field(..., description="Lista ordenada de variables esperadas por el pipeline.")
    metricas_holdout: dict[str, Any] = Field(
        default_factory=dict,
        description="Métricas relevantes del holdout temporal registradas en metadata.",
    )
    notas: list[str] = Field(
        default_factory=list,
        description="Notas operativas y consideraciones del modelo.",
    )


class PowerBITransactionResponse(BaseModel):
    """Fila plana de monitoreo pensada para consumo directo desde Power BI."""

    transaction_id: str = Field(..., description="Identificador único de la transacción.")
    timestamp: str = Field(..., description="Fecha y hora del evento o de la corrida.")
    type: str = Field(..., description="Tipo de transacción.")
    amount: int | None = Field(None, description="Monto entero redondeado para analítica.")
    channel: str = Field(..., description="Canal de origen de la transacción.")
    customer_segment: str = Field(..., description="Segmento del cliente.")
    probabilidad_fraude: float = Field(..., description="Probabilidad final para monitoreo.")
    nivel_riesgo: str = Field(..., description="Nivel de riesgo categorizado.")
    alerta: str = Field(..., description="Bandera textual de alerta operativa.")
    time_window: str = Field(..., description="Franja horaria derivada para el dashboard.")
