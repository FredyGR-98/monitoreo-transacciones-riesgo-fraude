"""Lógica de inferencia para la API de fraude."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from src.api.models.requests import TransactionInput
from src.api.services.artifacts import ArtifactBundle, get_artifact_bundle
from src.api.services.validation import PayloadValidator


logger = logging.getLogger(__name__)


class PredictionService:
    """Servicio de alto nivel para scoring individual y por lotes."""

    def __init__(self, artifact_bundle: ArtifactBundle) -> None:
        """Inicializa el servicio con artefactos ya cargados.

        Parámetros:
            artifact_bundle (ArtifactBundle): Pipeline, features y metadatos del modelo.
        """
        self.pipeline = artifact_bundle.pipeline
        self.features = artifact_bundle.features
        self.metadata = artifact_bundle.metadata
        self.threshold = artifact_bundle.threshold
        self.model_name = artifact_bundle.model_name
        self.validator = PayloadValidator(self.features)
        self.validator.validate_schema_alignment()

    def health_status(self) -> dict[str, Any]:
        """Entrega un resumen mínimo del estado operativo del servicio.

        Retorna:
            dict[str, Any]: Estado, modelo activo, umbral y número de features.
        """
        return {
            "status": "ok",
            "modelo": self.model_name,
            "threshold": self.threshold,
            "features_esperadas": len(self.features),
        }

    def model_info(self) -> dict[str, Any]:
        """Entrega metadatos útiles para documentación y observabilidad.

        Retorna:
            dict[str, Any]: Información pública del modelo desplegado.
        """
        return {
            "modelo": self.model_name,
            "familia_modelo": self.metadata.get("model_family"),
            "escenario": self.metadata.get("scenario"),
            "target": self.metadata.get("target"),
            "threshold": self.threshold,
            "features": self.features,
            "metricas_holdout": self.metadata.get("metricas_temporal_holdout", {}),
            "notas": self.metadata.get("notas", []),
        }

    def predict(self, transaction: TransactionInput | dict[str, Any]) -> dict[str, Any]:
        """Calcula una predicción para una transacción individual.

        Parámetros:
            transaction (TransactionInput | dict[str, Any]): Transacción a evaluar.

        Retorna:
            dict[str, Any]: Probabilidad de fraude y decisión final.
        """
        payload = (
            transaction.model_dump()
            if isinstance(transaction, TransactionInput)
            else transaction
        )
        results = self.predict_batch([payload])
        return results[0]

    def predict_batch(
        self,
        transactions: list[TransactionInput | dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Ejecuta scoring por lotes reutilizando el pipeline cargado.

        Parámetros:
            transactions (list[TransactionInput | dict[str, Any]]): Lote a evaluar.

        Retorna:
            list[dict[str, Any]]: Lista de resultados de inferencia.
        """
        payloads = [
            transaction.model_dump()
            if isinstance(transaction, TransactionInput)
            else transaction
            for transaction in transactions
        ]

        dataframe = self.validator.build_dataframe(payloads)
        probabilities = self.pipeline.predict_proba(dataframe)[:, 1]
        results = [self._build_prediction(float(probability)) for probability in probabilities]

        logger.info(
            "Predicción por lotes generada | total=%s | threshold=%.2f | modelo=%s",
            len(results),
            self.threshold,
            self.model_name,
        )

        return results

    def _build_prediction(self, probability: float) -> dict[str, Any]:
        """Convierte una probabilidad en la respuesta pública de la API.

        Parámetros:
            probability (float): Probabilidad de fraude calculada por el modelo.

        Retorna:
            dict[str, Any]: Respuesta final consumida por API y dashboard.
        """
        return {
            "fraude": int(probability >= self.threshold),
            "probabilidad": round(probability, 4),
            "threshold_aplicado": self.threshold,
            "modelo": self.model_name,
        }


@lru_cache(maxsize=1)
def get_prediction_service() -> PredictionService:
    """Entrega una instancia cacheada del servicio de inferencia.

    Retorna:
        PredictionService: Servicio reutilizable por todos los endpoints.
    """
    return PredictionService(get_artifact_bundle())
