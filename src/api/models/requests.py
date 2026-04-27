"""Esquemas de entrada para la API de fraude."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionInput(BaseModel):
    """Representa una transacción individual lista para inferencia.

    Propósito:
        Define el contrato de entrada que la API acepta para evaluar riesgo de fraude.
    """

    model_config = ConfigDict(extra="forbid")

    step: int = Field(..., ge=1, description="Paso temporal de la transacción.")
    type: str = Field(..., min_length=1, description="Tipo de transacción.")
    amount: float = Field(..., ge=0, description="Monto de la transacción.")
    oldbalanceOrg: float = Field(..., ge=0, description="Saldo origen antes de la transacción.")
    oldbalanceDest: float = Field(..., ge=0, description="Saldo destino antes de la transacción.")
    ratio_monto_saldo: float = Field(..., ge=0, description="Ratio entre monto y saldo origen.")
    flag_transfer: int = Field(..., description="Indicador binario de transferencia.")
    flag_monto_alto: int = Field(..., description="Indicador binario de monto alto.")
    regla_monto_alto_transfer: int = Field(..., description="Regla binaria de monto alto en transferencia.")
    regla_ratio_alto: int = Field(..., description="Regla binaria de ratio alto.")

    @field_validator("type")
    @classmethod
    def normalizar_tipo(cls, value: str) -> str:
        """Normaliza el tipo de transacción según el formato esperado.

        Parámetros:
            value (str): Tipo recibido en el payload.

        Retorna:
            str: Tipo de transacción en mayúsculas y sin espacios extra.
        """
        cleaned_value = value.strip().upper()
        if not cleaned_value:
            raise ValueError("El tipo de transacción no puede estar vacío.")
        return cleaned_value

    @field_validator(
        "flag_transfer",
        "flag_monto_alto",
        "regla_monto_alto_transfer",
        "regla_ratio_alto",
    )
    @classmethod
    def validar_binario(cls, value: int) -> int:
        """Asegura que los flags operativos sean binarios.

        Parámetros:
            value (int): Valor recibido para una señal operativa binaria.

        Retorna:
            int: Valor validado, limitado a 0 o 1.
        """
        if value not in (0, 1):
            raise ValueError("Debe ser 0 o 1.")
        return value


class BatchPredictionRequest(BaseModel):
    """Representa un lote de transacciones para evaluación masiva."""

    model_config = ConfigDict(extra="forbid")

    transactions: list[TransactionInput] = Field(
        ...,
        min_length=1,
        description="Lista de transacciones a evaluar en lote.",
    )
