"""Carga y validación de artefactos del modelo de fraude."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import joblib

from src.api.config import RUTA_FEATURES, RUTA_METADATA, RUTA_MODELO


@dataclass(frozen=True)
class ArtifactBundle:
    """Agrupa los artefactos necesarios para servir inferencia.

    Atributos:
        pipeline (Any): Pipeline serializado listo para inferencia.
        features (list[str]): Lista ordenada de variables esperadas.
        metadata (dict[str, Any]): Metadatos exportados durante entrenamiento.
        threshold (float): Umbral operativo de decisión.
        model_name (str): Nombre público del modelo desplegado.
    """

    pipeline: Any
    features: list[str]
    metadata: dict[str, Any]
    threshold: float
    model_name: str


def _load_pipeline() -> Any:
    """Carga el pipeline serializado desde disco.

    Retorna:
        Any: Pipeline listo para generar probabilidades.
    """
    if not RUTA_MODELO.exists():
        raise FileNotFoundError(f"No se encontró el pipeline en {RUTA_MODELO}.")
    return joblib.load(RUTA_MODELO)


def _load_features() -> list[str]:
    """Carga y valida la lista de variables esperadas.

    Retorna:
        list[str]: Variables finales en el orden requerido por el pipeline.
    """
    if not RUTA_FEATURES.exists():
        raise FileNotFoundError(f"No se encontró la lista de features en {RUTA_FEATURES}.")

    with RUTA_FEATURES.open("r", encoding="utf-8") as file:
        features = json.load(file)

    if not isinstance(features, list) or not all(isinstance(item, str) for item in features):
        raise ValueError("El archivo de features debe contener una lista de nombres de columnas.")

    return features


def _load_metadata() -> dict[str, Any]:
    """Carga y valida la metadata pública del modelo.

    Retorna:
        dict[str, Any]: Metadatos serializados para observabilidad y configuración.
    """
    if not RUTA_METADATA.exists():
        raise FileNotFoundError(f"No se encontró la metadata en {RUTA_METADATA}.")

    with RUTA_METADATA.open("r", encoding="utf-8") as file:
        metadata = json.load(file)

    if not isinstance(metadata, dict):
        raise ValueError("La metadata del modelo debe ser un objeto JSON.")

    return metadata


def _validate_bundle(features: list[str], metadata: dict[str, Any]) -> None:
    """Asegura consistencia entre variables exportadas y metadata.

    Parámetros:
        features (list[str]): Variables finales esperadas por la API.
        metadata (dict[str, Any]): Metadatos del modelo cargado.
    """
    features_metadata = metadata.get("features_finales")
    if features_metadata and features_metadata != features:
        raise ValueError(
            "Las features del metadata no coinciden con fraude_api_features.json."
        )


@lru_cache(maxsize=1)
def get_artifact_bundle() -> ArtifactBundle:
    """Carga una única vez el pipeline y sus artefactos asociados.

    Retorna:
        ArtifactBundle: Conjunto reutilizable por todos los endpoints.
    """
    features = _load_features()
    metadata = _load_metadata()
    _validate_bundle(features, metadata)

    return ArtifactBundle(
        pipeline=_load_pipeline(),
        features=features,
        metadata=metadata,
        threshold=float(metadata.get("threshold_selected", 0.5)),
        model_name=str(metadata.get("model_name", "modelo_no_identificado")),
    )
