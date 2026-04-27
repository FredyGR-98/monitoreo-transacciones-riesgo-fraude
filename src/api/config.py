"""Configuración central para la API de inferencia de fraude.

Propósito:
    Centraliza rutas de artefactos, metadatos visibles de OpenAPI y constantes
    que deben compartirse entre endpoints, servicios y documentación.
"""

from pathlib import Path


RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_ARTIFACTS = RUTA_PROYECTO / "artifacts"
RUTA_MODELO = RUTA_ARTIFACTS / "fraude_api_pipeline.joblib"
RUTA_FEATURES = RUTA_ARTIFACTS / "fraude_api_features.json"
RUTA_METADATA = RUTA_ARTIFACTS / "fraude_api_metadata.json"
RUTA_POWERBI_DATA = RUTA_PROYECTO / "dashboard" / "powerbi_data" / "monitoreo_fraude.csv"

API_TITLE = "API de Monitoreo de Transacciones y Riesgo de Fraude"
API_VERSION = "1.2.0"
API_DESCRIPTION = """
API de inferencia para monitoreo de fraude transaccional.

La aplicación carga un pipeline serializado desde `artifacts/`, valida el payload
de entrada con Pydantic, ordena las variables según el JSON exportado durante el
entrenamiento y devuelve una probabilidad de fraude junto con la decisión final.
""".strip()

API_TAGS_METADATA = [
    {
        "name": "Monitoreo",
        "description": "Endpoints para validar salud del servicio y entregar datos operativos.",
    },
    {
        "name": "Modelo",
        "description": "Metadatos del pipeline desplegado y de sus artefactos cargados.",
    },
    {
        "name": "Predicción",
        "description": "Endpoints para inferencia individual y por lotes.",
    },
]
