"""Compatibilidad hacia atras para importaciones antiguas de servicio."""

from src.api.services.prediction import PredictionService as FraudPredictor
from src.api.services.prediction import get_prediction_service as get_predictor

__all__ = ["FraudPredictor", "get_predictor"]
