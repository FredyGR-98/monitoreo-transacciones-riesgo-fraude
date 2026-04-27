"""Validaciones auxiliares para mantener consistencia entre esquema y artefactos."""

from __future__ import annotations

from typing import Any

import pandas as pd

from src.api.models.requests import TransactionInput


class PayloadValidator:
    """Valida payloads de inferencia usando el JSON de features como fuente de verdad."""

    def __init__(self, expected_features: list[str]) -> None:
        """Inicializa el validador con el orden de variables esperado.

        Parámetros:
            expected_features (list[str]): Variables finales requeridas por el pipeline.
        """
        self.expected_features = expected_features

    def validate_schema_alignment(self) -> None:
        """Verifica que el esquema HTTP coincida con el pipeline desplegado.

        Retorna:
            None: Lanza una excepción si el orden de variables no coincide.
        """
        schema_fields = list(TransactionInput.model_fields)
        if schema_fields != self.expected_features:
            raise ValueError(
                "El schema TransactionInput no coincide con el orden definido en fraude_api_features.json."
            )

    def order_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Reordena y valida un payload individual según las features esperadas.

        Parámetros:
            payload (dict[str, Any]): Datos de entrada de una transacción.

        Retorna:
            dict[str, Any]: Payload ordenado según el pipeline.
        """
        missing_features = [
            feature for feature in self.expected_features if feature not in payload
        ]
        if missing_features:
            raise ValueError(f"Faltan features requeridas: {missing_features}")

        unexpected_features = [
            feature for feature in payload if feature not in self.expected_features
        ]
        if unexpected_features:
            raise ValueError(f"Se recibieron features no soportadas: {unexpected_features}")

        return {feature: payload[feature] for feature in self.expected_features}

    def build_dataframe(self, payloads: list[dict[str, Any]]) -> pd.DataFrame:
        """Construye un DataFrame alineado con el pipeline serializado.

        Parámetros:
            payloads (list[dict[str, Any]]): Lote de transacciones ya validadas.

        Retorna:
            pd.DataFrame: Tabla lista para el pipeline de inferencia.
        """
        ordered_payloads = [self.order_payload(payload) for payload in payloads]
        return pd.DataFrame(ordered_payloads, columns=self.expected_features)
