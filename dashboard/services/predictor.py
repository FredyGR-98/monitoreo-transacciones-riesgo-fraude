"""Ayudantes para construir payloads amigables hacia la API de fraude."""

from __future__ import annotations

from typing import Any


TRANSACTION_TYPES = ["TRANSFER", "CASH_OUT", "CASH_IN", "PAYMENT", "DEBIT"]
RATIO_HIGH_THRESHOLD = 0.90


def build_transaction_payload(
    *,
    step: int,
    transaction_type: str,
    amount: float,
    oldbalance_org: float,
    oldbalance_dest: float,
    high_amount_threshold: float,
) -> dict[str, Any]:
    """Construye el payload final que espera la API usando reglas derivadas."""
    normalized_type = transaction_type.strip().upper()
    ratio = amount / oldbalance_org if oldbalance_org > 0 else 0.0
    flag_transfer = int(normalized_type == "TRANSFER")
    flag_monto_alto = int(flag_transfer == 1 and amount >= high_amount_threshold)
    regla_monto_alto_transfer = flag_monto_alto
    regla_ratio_alto = int(oldbalance_org > 0 and ratio >= RATIO_HIGH_THRESHOLD)

    return {
        "step": int(step),
        "type": normalized_type,
        "amount": float(amount),
        "oldbalanceOrg": float(oldbalance_org),
        "oldbalanceDest": float(oldbalance_dest),
        "ratio_monto_saldo": round(float(ratio), 4),
        "flag_transfer": flag_transfer,
        "flag_monto_alto": flag_monto_alto,
        "regla_monto_alto_transfer": regla_monto_alto_transfer,
        "regla_ratio_alto": regla_ratio_alto,
    }


def get_prediction_label(fraud_prediction: int) -> str:
    """Devuelve una etiqueta legible para la prediccion."""
    return "Fraude probable" if fraud_prediction == 1 else "Operacion normal"


def get_prediction_tone(fraud_prediction: int) -> str:
    """Define el tono visual del resultado."""
    return "critico" if fraud_prediction == 1 else "estable"
