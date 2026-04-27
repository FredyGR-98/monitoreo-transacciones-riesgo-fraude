"""Servicios para construir y evaluar lotes de monitoreo antifraude."""

from __future__ import annotations

import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from dashboard.services.predictor import build_transaction_payload
except ModuleNotFoundError:  # pragma: no cover - fallback para streamlit desde dashboard/
    from services.predictor import build_transaction_payload


ACTION_OPTIONS = [
    "Pendiente",
    "Revisar",
    "Marcar como fraude",
    "Bloquear",
]

SUPPORTED_FILE_COLUMNS = {
    "step": ["step", "time_step", "periodo"],
    "timestamp": ["timestamp", "fecha_hora", "datetime", "event_time"],
    "type": ["type", "transaction_type", "tipo"],
    "amount": ["amount", "monto"],
    "oldbalanceOrg": ["oldbalanceOrg", "oldbalance_org", "saldo_origen"],
    "newbalanceOrig": ["newbalanceOrig", "newbalance_orig", "nuevo_saldo_origen"],
    "oldbalanceDest": ["oldbalanceDest", "oldbalance_dest", "saldo_destino"],
    "newbalanceDest": ["newbalanceDest", "newbalance_dest", "nuevo_saldo_destino"],
    "transaction_id": ["transaction_id", "id", "txn_id", "transactionId"],
    "channel": ["channel", "canal", "modalidad"],
    "customer_segment": ["customer_segment", "segmento", "customer_type"],
}

REQUIRED_FILE_FIELDS = [
    "transaction_id",
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
]

BASE_DIR = Path(__file__).resolve().parents[2]
MONITORING_OUTPUT_PATH = BASE_DIR / "dashboard" / "powerbi_data" / "monitoreo_fraude.csv"
# Modo recomendado para Power BI Desktop en este entorno: siempre reemplazar el CSV.
MONITORING_CSV_MODE = "overwrite"
POWER_BI_OUTPUT_COLUMNS = [
    "transaction_id",
    "timestamp",
    "type",
    "amount",
    "channel",
    "customer_segment",
    "probabilidad_fraude",
    "nivel_riesgo",
    "alerta",
    "time_window",
]
MONITORING_DEDUPLICATION_KEYS = ["transaction_id", "timestamp"]


def generate_transaction_batch(
    *,
    batch_size: int,
    suspicious_rate: float,
    high_amount_threshold: float,
) -> list[dict[str, Any]]:
    """Genera un lote de transacciones simuladas usando el motor comun."""
    transactions: list[dict[str, Any]] = []
    base_timestamp = pd.Timestamp.now().floor("min").normalize()

    for index in range(batch_size):
        suspicious = random.random() < suspicious_rate
        scenario = _build_transaction_scenario(
            suspicious=suspicious,
            high_amount_threshold=high_amount_threshold,
        )
        simulated_timestamp = _build_simulated_timestamp(
            step=scenario["step"],
            batch_index=index,
            base_timestamp=base_timestamp,
        )
        transaction = _build_monitoring_transaction(
            transaction_id=f"TXN-{10001 + index}",
            step=scenario["step"],
            transaction_type=scenario["type"],
            amount=scenario["amount"],
            oldbalance_org=scenario["oldbalanceOrg"],
            oldbalance_dest=scenario["oldbalanceDest"],
            high_amount_threshold=high_amount_threshold,
            source_label="Simulado",
            timestamp=simulated_timestamp,
            channel=scenario["channel"],
            customer_segment=scenario["customer_segment"],
            scenario=scenario["scenario"],
            balance_status=scenario["balance_status"],
            case_title=scenario["case_title"],
            case_reason=scenario["case_reason"],
            review_hint=scenario["review_hint"],
            recommended_action=scenario["recommended_action"],
            severity_boost=float(scenario.get("severity_boost", 0.0)),
            original_input={
                "step": scenario["step"],
                "timestamp": simulated_timestamp,
                "type": scenario["type"],
                "amount": round(scenario["amount"], 2),
                "oldbalanceOrg": round(scenario["oldbalanceOrg"], 2),
                "oldbalanceDest": round(scenario["oldbalanceDest"], 2),
                "channel": scenario["channel"],
                "customer_segment": scenario["customer_segment"],
            },
        )
        transactions.append(transaction)

    return transactions


def build_transactions_from_records(
    records: list[dict[str, Any]],
    *,
    high_amount_threshold: float,
) -> list[dict[str, Any]]:
    """Construye transacciones desde datos cargados en archivo."""
    transactions: list[dict[str, Any]] = []

    for index, record in enumerate(records, start=1):
        timestamp_value = _extract_optional_value(record, "timestamp")
        step_value = _extract_optional_value(record, "step")
        step = derive_step_value(
            step=step_value,
            timestamp=timestamp_value,
            fallback_index=index,
        )
        transaction_type = str(_extract_value(record, "type")).strip().upper()
        amount = _coerce_float(_extract_value(record, "amount"))
        oldbalance_org = _coerce_float(_extract_value(record, "oldbalanceOrg"))
        newbalance_orig = _coerce_float(_extract_value(record, "newbalanceOrig"))
        oldbalance_dest = _coerce_float(_extract_value(record, "oldbalanceDest"))
        newbalance_dest = _coerce_float(_extract_value(record, "newbalanceDest"))
        transaction_id = str(_extract_value(record, "transaction_id"))
        channel = str(_extract_value(record, "channel", default="Archivo cargado"))
        customer_segment = str(_extract_value(record, "customer_segment", default="Archivo"))
        time_window = derive_time_window(
            step=step if step_value is not None else None,
            timestamp=timestamp_value,
        )

        file_case = _derive_file_case(
            step=step,
            time_window=time_window,
            transaction_type=transaction_type,
            amount=amount,
            oldbalance_org=oldbalance_org,
            newbalance_orig=newbalance_orig,
            oldbalance_dest=oldbalance_dest,
            newbalance_dest=newbalance_dest,
            high_amount_threshold=high_amount_threshold,
            channel=channel,
            customer_segment=customer_segment,
        )

        transactions.append(
            _build_monitoring_transaction(
                transaction_id=transaction_id,
                step=step,
                transaction_type=transaction_type,
                amount=amount,
                oldbalance_org=oldbalance_org,
                oldbalance_dest=oldbalance_dest,
                high_amount_threshold=high_amount_threshold,
                source_label="Archivo",
                timestamp=timestamp_value,
                time_window=time_window,
                channel=channel,
                customer_segment=customer_segment,
                scenario=file_case["scenario"],
                balance_status=file_case["balance_status"],
                case_title=file_case["case_title"],
                case_reason=file_case["case_reason"],
                review_hint=file_case["review_hint"],
                recommended_action=file_case["recommended_action"],
                severity_boost=float(file_case["severity_boost"]),
                original_input=record,
            )
        )

    return transactions


def score_transactions_with_api(
    transactions: list[dict[str, Any]],
    api_client,
) -> list[dict[str, Any]]:
    """Evalua transacciones una por una usando el endpoint /predict."""
    scored_transactions: list[dict[str, Any]] = []

    for transaction in transactions:
        result = api_client.predict(transaction["payload"])
        probability = float(result["probabilidad"])
        threshold = float(result["threshold_aplicado"])
        monitoring_probability = max(probability, float(transaction.get("seed_score", 0.0)))
        risk_level = get_risk_level(monitoring_probability)
        alert = monitoring_probability >= 0.14

        scored_transactions.append(
            {
                **transaction,
                "fraude": int(result["fraude"]),
                "probabilidad": probability,
                "probabilidad_monitoreo": monitoring_probability,
                "threshold_aplicado": threshold,
                "risk_level": risk_level,
                "risk_indicator": get_risk_indicator(risk_level),
                "alert": alert,
            }
        )

    return sorted(
        scored_transactions,
        key=lambda item: float(item["probabilidad_monitoreo"]),
        reverse=True,
    )


def get_risk_level(probability: float) -> str:
    """Clasifica la probabilidad en niveles de riesgo para la UI."""
    if probability >= 0.30:
        return "alto"
    if probability >= 0.14:
        return "medio"
    return "bajo"


def get_risk_indicator(risk_level: str) -> str:
    """Devuelve un indicador visual simple para tablas."""
    mapping = {
        "alto": "🔴 Alto",
        "medio": "🟡 Medio",
        "bajo": "🟢 Bajo",
    }
    return mapping.get(risk_level, "🟢 Bajo")


def validate_uploaded_columns(columns: list[str]) -> None:
    """Valida que el archivo tenga las columnas obligatorias esperadas."""
    missing_fields = []
    normalized_columns = {str(column).strip() for column in columns}

    for field in REQUIRED_FILE_FIELDS:
        aliases = SUPPORTED_FILE_COLUMNS.get(field, [field])
        if not any(alias in normalized_columns for alias in aliases):
            missing_fields.append(field)

    if missing_fields:
        required = ", ".join(REQUIRED_FILE_FIELDS)
        missing = ", ".join(missing_fields)
        raise ValueError(
            "Faltan columnas obligatorias en el archivo. "
            f"Requeridas: {required}. "
            f"Faltantes detectadas: {missing}."
        )


def summarize_monitoring(transactions: list[dict[str, Any]]) -> dict[str, int]:
    """Resume el estado del monitoreo actual."""
    total = len(transactions)
    alerts = sum(1 for item in transactions if item.get("alert"))
    blocked = sum(1 for item in transactions if item.get("analyst_action") == "Bloquear")
    marked = sum(
        1 for item in transactions if item.get("analyst_action") == "Marcar como fraude"
    )
    high_risk = sum(1 for item in transactions if item.get("risk_level") == "alto")
    medium_risk = sum(1 for item in transactions if item.get("risk_level") == "medio")

    return {
        "total": total,
        "alerts": alerts,
        "blocked": blocked,
        "marked": marked,
        "high_risk": high_risk,
        "medium_risk": medium_risk,
    }


def _build_monitoring_transaction(
    *,
    transaction_id: str,
    step: int,
    transaction_type: str,
    amount: float,
    oldbalance_org: float,
    oldbalance_dest: float,
    high_amount_threshold: float,
    source_label: str,
    timestamp: Any = None,
    time_window: str | None = None,
    channel: str,
    customer_segment: str,
    scenario: str,
    balance_status: str,
    case_title: str,
    case_reason: str,
    review_hint: str,
    recommended_action: str,
    severity_boost: float,
    original_input: dict[str, Any],
) -> dict[str, Any]:
    """Construye una transaccion estandar para el motor de monitoreo."""
    payload = build_transaction_payload(
        step=step,
        transaction_type=transaction_type,
        amount=amount,
        oldbalance_org=oldbalance_org,
        oldbalance_dest=oldbalance_dest,
        high_amount_threshold=high_amount_threshold,
    )
    resolved_time_window = time_window or derive_time_window(step=step, timestamp=timestamp)
    modality_label = f"{channel} | {resolved_time_window}"
    modality_context = (
        f"{channel} en franja {resolved_time_window.lower()} para cliente "
        f"{customer_segment.lower()} con balance {balance_status.lower()}."
    )
    seed_score = _estimate_alert_seed(
        payload,
        {
            "channel": channel,
            "customer_segment": customer_segment,
            "balance_status": balance_status,
            "scenario": scenario,
            "severity_boost": severity_boost,
        },
    )

    return {
        "transaction_id": transaction_id,
        "step": int(step),
        "type": transaction_type,
        "amount": round(float(amount), 2),
        "oldbalanceOrg": round(float(oldbalance_org), 2),
        "oldbalanceDest": round(float(oldbalance_dest), 2),
        "payload": payload,
        "scenario": scenario,
        "case_title": case_title,
        "case_reason": case_reason,
        "channel": channel,
        "timestamp": timestamp,
        "time_window": resolved_time_window,
        "modality_label": modality_label,
        "modality_context": modality_context,
        "balance_status": balance_status,
        "customer_segment": customer_segment,
        "review_hint": review_hint,
        "recommended_action": recommended_action,
        "seed_score": seed_score,
        "input_source": source_label,
        "original_input": original_input,
        "analyst_action": "Pendiente",
    }


def _build_transaction_scenario(
    *,
    suspicious: bool,
    high_amount_threshold: float,
) -> dict[str, Any]:
    """Construye un caso transaccional entendible para el analista."""
    if suspicious:
        scenario_builder = random.choice(
            [
                _scenario_high_amount_transfer,
                _scenario_balance_drain,
                _scenario_cashout_spike,
                _scenario_partner_api_transfer,
                _scenario_night_drain,
                _scenario_new_account_cashout,
                _scenario_round_amount_transfer,
            ]
        )
        scenario = scenario_builder(high_amount_threshold)
        scenario["scenario"] = "Sospechosa"
        scenario["balance_status"] = (
            "Inconsistente"
            if scenario["oldbalanceOrg"] <= scenario["amount"] * 1.05
            else "Tensionado"
        )
    else:
        scenario_builder = random.choice(
            [
                _scenario_regular_payment,
                _scenario_regular_transfer,
                _scenario_regular_cash_out,
            ]
        )
        scenario = scenario_builder(high_amount_threshold)
        scenario["scenario"] = "Regular"
        scenario["balance_status"] = "Coherente"

    return scenario


def _derive_file_case(
    *,
    step: int | None,
    time_window: str,
    transaction_type: str,
    amount: float,
    oldbalance_org: float,
    newbalance_orig: float,
    oldbalance_dest: float,
    newbalance_dest: float,
    high_amount_threshold: float,
    channel: str,
    customer_segment: str,
) -> dict[str, Any]:
    """Deriva contexto de negocio para registros cargados desde archivo."""
    ratio = amount / oldbalance_org if oldbalance_org > 0 else 0.0
    is_high_amount = transaction_type == "TRANSFER" and amount >= high_amount_threshold
    low_dest_balance = oldbalance_dest <= amount * 0.10 if amount > 0 else False
    is_night = time_window == "Noche"
    origin_drained = newbalance_orig <= oldbalance_org * 0.10 if oldbalance_org > 0 else False
    destination_jump = newbalance_dest >= oldbalance_dest + amount * 0.90 if amount > 0 else False

    case_title = "Operacion cargada desde archivo"
    case_reason = "Registro importado para scoring uniforme en el panel de monitoreo."
    review_hint = "Sin senal dominante; dejar en observacion."
    recommended_action = "Pendiente"
    severity_boost = 0.02
    scenario = "Regular"

    if customer_segment == "Cuenta nueva" and transaction_type == "CASH_OUT" and ratio >= 0.85:
        case_title = "Cuenta nueva con cash-out elevado"
        case_reason = (
            "El archivo muestra una cuenta nueva que retira gran parte de su saldo "
            "en una sola operacion."
        )
        review_hint = "Validar KYC, geografia y antiguedad de la cuenta antes de liberar."
        recommended_action = "Marcar como fraude"
        severity_boost = 0.18
        scenario = "Sospechosa"
    elif is_night and ratio >= 0.90:
        case_title = "Operacion nocturna tensionada"
        case_reason = (
            "La transaccion ocurre en franja nocturna y consume casi todo el saldo origen."
        )
        review_hint = "Revisar autenticacion, dispositivo y actividad previa del cliente."
        recommended_action = "Bloquear"
        severity_boost = 0.16
        scenario = "Sospechosa"
    elif is_high_amount and ratio >= 0.85:
        case_title = "Transferencia de alto monto"
        case_reason = (
            "El monto supera el umbral alto y compromete gran parte del saldo disponible."
        )
        review_hint = "Confirmar beneficiario, biometria y legitimidad del destino."
        recommended_action = "Revisar"
        severity_boost = 0.14
        scenario = "Sospechosa"
    elif transaction_type in {"TRANSFER", "CASH_OUT"} and (ratio >= 0.95 or origin_drained):
        case_title = "Vaciamiento casi total"
        case_reason = (
            "La operacion drena casi por completo el saldo de origen en un solo evento."
        )
        review_hint = "Priorizar en cola y revisar eventos recientes del cliente."
        recommended_action = "Bloquear"
        severity_boost = 0.17
        scenario = "Sospechosa"
    elif transaction_type == "CASH_OUT" and (low_dest_balance or origin_drained):
        case_title = "Cash-out inusual"
        case_reason = (
            "Se observa una salida de efectivo elevada con senales de bajo saldo de contraparte."
        )
        review_hint = "Contrastar con retiros previos y comportamiento historico."
        recommended_action = "Revisar"
        severity_boost = 0.12
        scenario = "Sospechosa"
    elif transaction_type == "TRANSFER" and destination_jump and ratio >= 0.75:
        case_title = "Transferencia con salto abrupto en destino"
        case_reason = (
            "El saldo destino aumenta de forma brusca y la salida desde origen es material."
        )
        review_hint = "Confirmar legitimidad del beneficiario y relacion previa con el cliente."
        recommended_action = "Revisar"
        severity_boost = 0.11
        scenario = "Sospechosa"
    elif channel == "API partner" and amount >= high_amount_threshold * 0.8:
        case_title = "Transferencia via partner"
        case_reason = (
            "El canal externo aporta friccion adicional y el monto es alto para origen API."
        )
        review_hint = "Auditar la integracion y revisar reputacion del comercio asociado."
        recommended_action = "Revisar"
        severity_boost = 0.13
        scenario = "Sospechosa"
    elif transaction_type == "PAYMENT":
        case_title = "Pago cotidiano"
        case_reason = "Operacion comercial con lectura transaccional estable."
        review_hint = "Monitoreo pasivo, salvo que existan alertas externas."
        severity_boost = 0.0
    elif transaction_type == "CASH_OUT":
        case_title = "Cash-out operativo"
        case_reason = "Retiro con balances compatibles y sin senal dominante adicional."
        review_hint = "Continuar observacion regular."
        severity_boost = 0.01
    else:
        case_title = "Transferencia habitual"
        case_reason = "Transferencia con contexto operativo estable para scoring."
        review_hint = "Mantener seguimiento normal."
        severity_boost = 0.01

    balance_status = _derive_balance_status(amount=amount, oldbalance_org=oldbalance_org)

    return {
        "scenario": scenario,
        "balance_status": balance_status,
        "case_title": case_title,
        "case_reason": case_reason,
        "review_hint": review_hint,
        "recommended_action": recommended_action,
        "severity_boost": severity_boost,
    }


def _extract_value(record: dict[str, Any], field: str, default: Any = None) -> Any:
    """Busca un valor usando aliases de columna."""
    aliases = SUPPORTED_FILE_COLUMNS.get(field, [field])
    for alias in aliases:
        if alias in record and record[alias] not in (None, ""):
            return record[alias]
    if default is not None:
        return default
    raise ValueError(
        "El archivo debe incluir columnas equivalentes a: "
        "transaction_id, type, amount, oldbalanceOrg, newbalanceOrig, "
        "oldbalanceDest y newbalanceDest."
    )


def _extract_optional_value(record: dict[str, Any], field: str) -> Any:
    """Busca un valor opcional usando aliases de columna."""
    aliases = SUPPORTED_FILE_COLUMNS.get(field, [field])
    for alias in aliases:
        if alias in record and record[alias] not in (None, ""):
            return record[alias]
    return None


def _coerce_float(value: Any) -> float:
    """Convierte valores de archivo a float de forma tolerante."""
    if value is None or value == "" or pd.isna(value):
        return 0.0
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").strip()
    return float(value)


def _coerce_int(value: Any, default: int) -> int:
    """Convierte valores a entero con fallback seguro."""
    if value is None or value == "" or pd.isna(value):
        return default
    return int(float(value))


def _derive_balance_status(*, amount: float, oldbalance_org: float) -> str:
    """Resume el estado del saldo origen antes de la transaccion."""
    if oldbalance_org <= amount * 1.05:
        return "Inconsistente"
    if oldbalance_org <= amount * 1.30:
        return "Tensionado"
    return "Coherente"


def _scenario_high_amount_transfer(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(high_amount_threshold * 1.05, high_amount_threshold * 2.3)
    oldbalance = amount * random.uniform(0.92, 1.02)
    return {
        "step": _random_step(),
        "type": "TRANSFER",
        "amount": amount,
        "oldbalanceOrg": oldbalance,
        "oldbalanceDest": random.uniform(0, amount * 0.20),
        "channel": random.choice(["App movil", "Portal web"]),
        "customer_segment": random.choice(["Retail", "Pyme"]),
        "case_title": "Transferencia de alto monto",
        "case_reason": (
            "El monto supera el umbral operativo de transferencias altas y consume casi "
            "todo el saldo disponible."
        ),
        "review_hint": "Validar legitimidad del beneficiario y confirmar autenticacion reforzada.",
        "recommended_action": "Revisar",
        "severity_boost": 0.12,
    }


def _scenario_balance_drain(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(high_amount_threshold * 0.65, high_amount_threshold * 1.25)
    oldbalance = amount * random.uniform(0.98, 1.01)
    return {
        "step": _random_step(),
        "type": random.choice(["TRANSFER", "CASH_OUT"]),
        "amount": amount,
        "oldbalanceOrg": oldbalance,
        "oldbalanceDest": random.uniform(0, amount * 0.10),
        "channel": random.choice(["App movil", "ATM"]),
        "customer_segment": random.choice(["Retail", "Alto valor"]),
        "case_title": "Vaciamiento casi total",
        "case_reason": (
            "La operacion representa al menos el 90% del saldo de origen, una senal "
            "clasica de drenaje o salida agresiva de fondos."
        ),
        "review_hint": "Comparar con historial reciente y revisar si hubo cambios de dispositivo.",
        "recommended_action": "Bloquear",
        "severity_boost": 0.16,
    }


def _scenario_cashout_spike(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(high_amount_threshold * 0.55, high_amount_threshold * 1.40)
    oldbalance = amount * random.uniform(1.00, 1.20)
    return {
        "step": _random_step(),
        "type": "CASH_OUT",
        "amount": amount,
        "oldbalanceOrg": oldbalance,
        "oldbalanceDest": random.uniform(0, amount * 0.35),
        "channel": random.choice(["ATM", "Portal web"]),
        "customer_segment": random.choice(["Retail", "Cuenta nueva"]),
        "case_title": "Cash-out inusual",
        "case_reason": (
            "El retiro es elevado para una salida de efectivo y aparece con balances de "
            "destino bajos, lo que amerita revision operativa."
        ),
        "review_hint": "Verificar cajero, geolocalizacion y precedencia de retiros cercanos.",
        "recommended_action": "Revisar",
        "severity_boost": 0.11,
    }


def _scenario_partner_api_transfer(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(high_amount_threshold * 0.9, high_amount_threshold * 1.8)
    oldbalance = amount * random.uniform(0.88, 1.05)
    return {
        "step": _random_step(),
        "type": "TRANSFER",
        "amount": amount,
        "oldbalanceOrg": oldbalance,
        "oldbalanceDest": random.uniform(0, amount * 0.15),
        "channel": "API partner",
        "customer_segment": random.choice(["Pyme", "Cuenta nueva"]),
        "case_title": "Transferencia via partner",
        "case_reason": (
            "La modalidad de origen es una integracion externa y la transaccion combina "
            "monto alto con saldo de origen tensionado."
        ),
        "review_hint": "Auditar la integracion externa y validar si el comercio asociado es conocido.",
        "recommended_action": "Revisar",
        "severity_boost": 0.14,
    }


def _scenario_night_drain(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(high_amount_threshold * 0.70, high_amount_threshold * 1.45)
    oldbalance = amount * random.uniform(0.94, 1.02)
    return {
        "step": _random_step(preferred_window="Noche"),
        "type": random.choice(["TRANSFER", "CASH_OUT"]),
        "amount": amount,
        "oldbalanceOrg": oldbalance,
        "oldbalanceDest": random.uniform(0, amount * 0.12),
        "channel": random.choice(["Portal web", "App movil"]),
        "customer_segment": random.choice(["Retail", "Cuenta nueva"]),
        "case_title": "Operacion nocturna tensionada",
        "case_reason": (
            "La transaccion ocurre en una franja menos habitual y consume una porcion "
            "muy alta del saldo disponible."
        ),
        "review_hint": "Revisar inicio de sesion, dispositivo y cambios recientes en credenciales.",
        "recommended_action": "Bloquear",
        "severity_boost": 0.15,
    }


def _scenario_new_account_cashout(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(high_amount_threshold * 0.60, high_amount_threshold * 1.10)
    oldbalance = amount * random.uniform(1.02, 1.12)
    return {
        "step": _random_step(),
        "type": "CASH_OUT",
        "amount": amount,
        "oldbalanceOrg": oldbalance,
        "oldbalanceDest": random.uniform(0, amount * 0.08),
        "channel": "ATM",
        "customer_segment": "Cuenta nueva",
        "case_title": "Cuenta nueva con cash-out elevado",
        "case_reason": (
            "Un cliente de poca antiguedad realiza un retiro alto y deja muy poco margen "
            "de saldo posterior."
        ),
        "review_hint": "Confirmar onboarding reciente, KYC y si existe patron de prueba previo.",
        "recommended_action": "Marcar como fraude",
        "severity_boost": 0.18,
    }


def _scenario_round_amount_transfer(high_amount_threshold: float) -> dict[str, Any]:
    multiplier = random.choice([1.0, 1.2, 1.5, 2.0])
    amount = round(high_amount_threshold * multiplier, -4)
    oldbalance = amount * random.uniform(0.96, 1.05)
    return {
        "step": _random_step(),
        "type": "TRANSFER",
        "amount": amount,
        "oldbalanceOrg": oldbalance,
        "oldbalanceDest": random.uniform(0, amount * 0.18),
        "channel": random.choice(["Portal web", "API partner"]),
        "customer_segment": random.choice(["Pyme", "Retail"]),
        "case_title": "Transferencia por monto redondo",
        "case_reason": (
            "El monto redondo y elevado es un patron frecuente en intentos de salida "
            "rapida de fondos o pruebas de limite."
        ),
        "review_hint": "Comparar contra montos historicos del cliente y frecuencia del beneficiario.",
        "recommended_action": "Revisar",
        "severity_boost": 0.13,
    }


def _scenario_regular_payment(_: float) -> dict[str, Any]:
    amount = random.uniform(800, 65_000)
    return {
        "step": _random_step(),
        "type": "PAYMENT",
        "amount": amount,
        "oldbalanceOrg": amount * random.uniform(2.5, 9.0),
        "oldbalanceDest": random.uniform(0, amount * 2.0),
        "channel": random.choice(["App movil", "POS comercio"]),
        "customer_segment": random.choice(["Retail", "Frecuente"]),
        "case_title": "Pago cotidiano",
        "case_reason": "Operacion comun de bajo monto con balances consistentes.",
        "review_hint": "No requiere accion adicional salvo monitoreo pasivo.",
        "recommended_action": "Pendiente",
        "severity_boost": 0.0,
    }


def _scenario_regular_transfer(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(5_000, high_amount_threshold * 0.55)
    return {
        "step": _random_step(),
        "type": "TRANSFER",
        "amount": amount,
        "oldbalanceOrg": amount * random.uniform(1.8, 5.5),
        "oldbalanceDest": random.uniform(amount * 0.4, amount * 3.5),
        "channel": random.choice(["Portal web", "App movil"]),
        "customer_segment": random.choice(["Retail", "Pyme"]),
        "case_title": "Transferencia habitual",
        "case_reason": "Transferencia con contexto operativo estable para scoring.",
        "review_hint": "Mantener seguimiento normal.",
        "recommended_action": "Pendiente",
        "severity_boost": 0.0,
    }


def _scenario_regular_cash_out(high_amount_threshold: float) -> dict[str, Any]:
    amount = random.uniform(10_000, high_amount_threshold * 0.45)
    return {
        "step": _random_step(),
        "type": "CASH_OUT",
        "amount": amount,
        "oldbalanceOrg": amount * random.uniform(2.0, 4.8),
        "oldbalanceDest": random.uniform(amount * 0.6, amount * 2.8),
        "channel": random.choice(["ATM", "Portal web"]),
        "customer_segment": random.choice(["Retail", "Frecuente"]),
        "case_title": "Cash-out operativo",
        "case_reason": "Retiro con balances compatibles y sin senal dominante adicional.",
        "review_hint": "Continuar observacion regular.",
        "recommended_action": "Pendiente",
        "severity_boost": 0.0,
    }


def _estimate_alert_seed(payload: dict[str, Any], scenario: dict[str, Any]) -> float:
    """Genera una probabilidad base de monitoreo para reflejar escenarios operativos."""
    score = 0.01
    if payload["type"] == "TRANSFER":
        score += 0.05
    if payload["type"] == "CASH_OUT":
        score += 0.03
    score += min(math.log10(max(payload["amount"], 1)) / 35, 0.06)
    score += payload["flag_monto_alto"] * 0.10
    score += payload["regla_monto_alto_transfer"] * 0.08
    score += payload["regla_ratio_alto"] * 0.14
    score += payload["flag_transfer"] * 0.02
    score += float(scenario.get("severity_boost", 0.0))

    if scenario.get("channel") == "API partner":
        score += 0.04
    if scenario.get("customer_segment") == "Cuenta nueva":
        score += 0.05
    if scenario.get("balance_status") == "Inconsistente":
        score += 0.06
    elif scenario.get("balance_status") == "Tensionado":
        score += 0.03
    if scenario.get("scenario") == "Regular":
        score -= 0.02

    return round(min(max(score, 0.01), 0.72), 4)


def derive_time_window(*, step: int | None = None, timestamp: Any = None) -> str:
    """Deriva la franja horaria desde timestamp o step."""
    hour = _extract_hour(timestamp=timestamp, step=step)
    if hour is None:
        return "No definido"
    if 6 <= hour <= 11:
        return "Manana"
    if 12 <= hour <= 17:
        return "Tarde"
    return "Noche"


def _extract_hour(*, timestamp: Any = None, step: int | None = None) -> int | None:
    """Extrae hora desde timestamp real o step simulado."""
    if timestamp not in (None, ""):
        parsed = pd.to_datetime(timestamp, errors="coerce")
        if not pd.isna(parsed):
            if isinstance(parsed, pd.Timestamp):
                return int(parsed.hour)
            if isinstance(parsed, datetime):
                return int(parsed.hour)
    if step is not None:
        return int(step) % 24
    return None


def _random_step(preferred_window: str | None = None) -> int:
    """Genera steps simulados preservando la franja deseada cuando aplica."""
    if preferred_window == "Noche":
        base_hour = random.choice([0, 1, 2, 3, 4, 5, 18, 19, 20, 21, 22, 23])
    elif preferred_window == "Manana":
        base_hour = random.choice([6, 7, 8, 9, 10, 11])
    elif preferred_window == "Tarde":
        base_hour = random.choice([12, 13, 14, 15, 16, 17])
    else:
        base_hour = random.randint(0, 23)

    cycle = random.choice([0, 24, 48])
    step = base_hour + cycle
    while step == 0 or step > 60:
        cycle = random.choice([0, 24, 48])
        step = base_hour + cycle
    return step


def _build_simulated_timestamp(
    *,
    step: int,
    batch_index: int,
    base_timestamp: pd.Timestamp,
) -> str:
    """Construye timestamps simulados variados para analitica horaria en Power BI."""
    hour = int(step) % 24
    day_offset = max((int(step) - 1) // 24, 0)
    minute = (batch_index * 7 + random.randint(0, 8)) % 60
    second = (batch_index * 11 + random.randint(0, 17)) % 60
    timestamp = base_timestamp + pd.Timedelta(days=day_offset)
    timestamp = timestamp + pd.Timedelta(hours=hour, minutes=minute, seconds=second)
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")


def build_results_dataframe(transactions: list[dict[str, Any]]) -> pd.DataFrame:
    """Construye el dataset enriquecido que alimenta monitoreo e historico."""
    processed_at = pd.Timestamp.now().floor("ms")
    processed_at_label = processed_at.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    rows: list[dict[str, Any]] = []

    for item in transactions:
        original = dict(item.get("original_input", {}))
        event_timestamp = _normalize_export_timestamp(
            item.get("timestamp"),
            fallback=processed_at,
        )
        row = {
            **original,
            "transaction_id": item["transaction_id"],
            "timestamp": event_timestamp,
            "type": item["type"],
            "amount": float(item["amount"]),
            "oldbalanceOrg": float(item["oldbalanceOrg"]),
            "oldbalanceDest": float(item["oldbalanceDest"]),
            "probabilidad_fraude": float(item.get("probabilidad", 0.0)),
            "prediccion": int(item.get("fraude", 0)),
            "nivel_riesgo": item["risk_level"],
            "riesgo_badge": item["risk_indicator"],
            "probabilidad_monitoreo": float(item.get("probabilidad_monitoreo", 0.0)),
            "timestamp_procesamiento": processed_at_label,
            "origen": str(item["input_source"]).lower(),
            "modalidad": item["modality_label"],
            "contexto": f"{item['customer_segment']} | {item['balance_status']}",
            "caso": item["case_title"],
            "alerta": "Si" if item.get("alert") else "No",
            "escenario": item["scenario"],
            "accion_analista": item["analyst_action"],
            "channel": item["channel"],
            "time_window": item["time_window"],
            "customer_segment": item["customer_segment"],
            "balance_status": item["balance_status"],
        }
        rows.append(row)

    return pd.DataFrame(rows)


def build_powerbi_export_dataframe(results_df: pd.DataFrame) -> pd.DataFrame:
    """Reduce el dataset al esquema estable que Power BI debe consumir."""
    export_df = results_df.reindex(columns=POWER_BI_OUTPUT_COLUMNS).copy()

    if "probabilidad_monitoreo" in results_df.columns:
        export_df["probabilidad_fraude"] = pd.to_numeric(
            results_df["probabilidad_monitoreo"],
            errors="coerce",
        ).fillna(pd.to_numeric(export_df["probabilidad_fraude"], errors="coerce"))

    export_df["transaction_id"] = export_df["transaction_id"].fillna("").astype(str).str.strip()
    export_df["timestamp"] = export_df["timestamp"].fillna("").astype(str).str.strip()
    export_df["type"] = export_df["type"].fillna("No definido").astype(str).str.strip()
    export_df["channel"] = export_df["channel"].fillna("No definido").astype(str).str.strip()
    export_df["customer_segment"] = (
        export_df["customer_segment"].fillna("No definido").astype(str).str.strip()
    )
    export_df["nivel_riesgo"] = (
        export_df["nivel_riesgo"].fillna("No definido").astype(str).str.strip()
    )
    export_df["alerta"] = export_df["alerta"].fillna("No").astype(str).str.strip()
    export_df["time_window"] = (
        export_df["time_window"].fillna("No definido").astype(str).str.strip()
    )
    export_df["amount"] = (
        pd.to_numeric(export_df["amount"], errors="coerce").fillna(0.0).round(0).astype("Int64")
    )
    export_df["probabilidad_fraude"] = pd.to_numeric(
        export_df["probabilidad_fraude"],
        errors="coerce",
    ).fillna(0.0).round(6)

    return export_df


def persist_monitoring_history(
    results_df: pd.DataFrame,
    *,
    mode: str = MONITORING_CSV_MODE,
) -> pd.DataFrame:
    """Guarda el dataset para Power BI en modo overwrite o append."""
    if results_df.empty:
        return pd.DataFrame(columns=POWER_BI_OUTPUT_COLUMNS)

    normalized_mode = str(mode).strip().lower()
    if normalized_mode not in {"append", "overwrite"}:
        raise ValueError("El modo de escritura del CSV debe ser 'append' u 'overwrite'.")

    MONITORING_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    export_df = build_powerbi_export_dataframe(results_df)

    if normalized_mode == "append" and MONITORING_OUTPUT_PATH.exists():
        existing_df = pd.read_csv(MONITORING_OUTPUT_PATH)
        existing_df = existing_df.reindex(columns=POWER_BI_OUTPUT_COLUMNS)
        total_df = pd.concat([existing_df, export_df], ignore_index=True, sort=False)
    else:
        total_df = export_df.copy()

    total_df = total_df.drop_duplicates(
        subset=MONITORING_DEDUPLICATION_KEYS,
        keep="last",
    ).reset_index(drop=True)
    total_df.to_csv(
        MONITORING_OUTPUT_PATH,
        index=False,
        encoding="utf-8-sig",
        sep=",",
        decimal=".",
        lineterminator="\n",
    )
    return total_df


def get_risk_indicator(risk_level: str) -> str:
    """Devuelve un indicador visual simple para tablas."""
    mapping = {
        "alto": "\U0001F534 Alto",
        "medio": "\U0001F7E1 Medio",
        "bajo": "\U0001F7E2 Bajo",
    }
    return mapping.get(risk_level, "\U0001F7E2 Bajo")


def _normalize_export_timestamp(value: Any, *, fallback: pd.Timestamp) -> str:
    """Normaliza timestamps para dejar un formato estable y amigable para Power BI."""
    if value in (None, "") or pd.isna(value):
        return fallback.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return str(value)

    if isinstance(parsed, pd.Timestamp):
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(parsed, datetime):
        return parsed.strftime("%Y-%m-%d %H:%M:%S")

    return str(value)


def derive_step_value(
    *,
    step: Any = None,
    timestamp: Any = None,
    fallback_index: int = 1,
) -> int:
    """Deriva un step valido para la API usando step, timestamp o indice."""
    if step not in (None, "") and not pd.isna(step):
        try:
            parsed_step = int(float(step))
            if parsed_step >= 1:
                return parsed_step
        except (TypeError, ValueError):
            pass

    hour = _extract_hour(timestamp=timestamp)
    if hour is not None:
        return hour + 1

    return max(int(fallback_index), 1)
