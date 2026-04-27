"""Cliente HTTP liviano para interactuar con la API de fraude."""

from __future__ import annotations

from typing import Any

import requests


class ApiClientError(Exception):
    """Representa errores controlados al comunicarse con la API."""


class ApiClient:
    """Cliente simple para consultar endpoints del backend FastAPI."""

    def __init__(self, base_url: str) -> None:
        """Inicializa el cliente con la URL base del servicio.

        Parámetros:
            base_url (str): URL base de la API, por ejemplo `http://127.0.0.1:8000`.
        """
        self.base_url = base_url.rstrip("/")

    def health(self) -> dict[str, Any]:
        """Consulta el estado operativo de la API.

        Retorna:
            dict[str, Any]: Respuesta del endpoint `/health`.
        """
        return self._request("GET", "/health")

    def model_info(self) -> dict[str, Any]:
        """Recupera metadatos públicos del modelo cargado.

        Retorna:
            dict[str, Any]: Información del endpoint `/model/info`.
        """
        return self._request("GET", "/model/info")

    def predict(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Ejecuta una predicción individual.

        Parámetros:
            payload (dict[str, Any]): Datos de la transacción a evaluar.

        Retorna:
            dict[str, Any]: Predicción individual generada por la API.
        """
        return self._request("POST", "/predict", json=payload)

    def predict_batch(self, transactions: list[dict[str, Any]]) -> dict[str, Any]:
        """Ejecuta scoring por lotes.

        Parámetros:
            transactions (list[dict[str, Any]]): Lote de transacciones a evaluar.

        Retorna:
            dict[str, Any]: Respuesta completa del endpoint `/predict/batch`.
        """
        return self._request("POST", "/predict/batch", json={"transactions": transactions})

    def _request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Centraliza timeouts y manejo de errores HTTP.

        Parámetros:
            method (str): Método HTTP a ejecutar.
            endpoint (str): Ruta relativa del endpoint.
            json (dict[str, Any] | None): Payload JSON opcional.

        Retorna:
            dict[str, Any]: Respuesta de la API convertida a JSON.
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(method, url, json=json, timeout=10)
        except requests.RequestException as error:
            raise ApiClientError(
                "No fue posible conectar con la API. Verifica que FastAPI esté levantada."
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise ApiClientError("La API respondió con un contenido no JSON.") from error

        if response.ok:
            return data

        detail = data.get("detail") or data.get("error") or "Error desconocido"
        raise ApiClientError(str(detail))
