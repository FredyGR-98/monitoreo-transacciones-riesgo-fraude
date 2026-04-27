"""Servicios de datos para el dashboard narrativo de fraude."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from sklearn.metrics import precision_recall_curve


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = BASE_DIR / "data" / "raw" / "paysim.csv"
RISK_DATA_PATH = BASE_DIR / "data" / "processed" / "tabla_riesgo_reglas.csv"
METADATA_PATH = BASE_DIR / "artifacts" / "fraude_api_metadata.json"
FEATURES_PATH = BASE_DIR / "artifacts" / "fraude_api_features.json"
PIPELINE_PATH = BASE_DIR / "artifacts" / "fraude_api_pipeline.joblib"
BENCHMARK_PATH = BASE_DIR / "artifacts" / "dashboard_model_benchmark.json"

RAW_SAMPLE_ROWS = 300_000
RISK_SAMPLE_ROWS = 250_000

RAW_COLUMNS = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "oldbalanceDest",
    "isFraud",
]

RISK_COLUMNS = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "oldbalanceDest",
    "ratio_monto_saldo",
    "flag_monto_alto",
    "flag_transfer",
    "cantidad_flags",
    "regla_monto_alto_transfer",
    "regla_ratio_alto",
    "risk_score",
    "risk_level",
    "isFraud",
]

PALETTE = {
    "fraude": "#c14d38",
    "seguro": "#1f6f78",
    "acento": "#d99f5d",
    "fondo": "#f7f3ea",
    "texto": "#17323a",
}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@st.cache_data(show_spinner=False)
def load_metadata() -> dict[str, Any]:
    """Carga la metadata del modelo desplegado."""
    return _load_json(METADATA_PATH)


@st.cache_data(show_spinner=False)
def load_features() -> list[str]:
    """Carga la lista ordenada de features esperadas por la API."""
    return _load_json(FEATURES_PATH)


@st.cache_data(show_spinner="Cargando muestra de transacciones...")
def load_raw_sample() -> pd.DataFrame:
    """Carga una muestra del dataset raw para EDA narrativo."""
    return pd.read_csv(RAW_DATA_PATH, usecols=RAW_COLUMNS, nrows=RAW_SAMPLE_ROWS)


@st.cache_data(show_spinner="Cargando tabla de riesgo...")
def load_risk_sample() -> pd.DataFrame:
    """Carga una muestra de la tabla enriquecida con reglas de riesgo."""
    return pd.read_csv(RISK_DATA_PATH, usecols=RISK_COLUMNS, nrows=RISK_SAMPLE_ROWS)


@st.cache_data(show_spinner="Preparando holdout del modelo desplegado...")
def load_model_holdout() -> pd.DataFrame:
    """Carga solo las columnas necesarias para evaluar el modelo desplegado."""
    metadata = load_metadata()
    features = load_features()
    columns = list(dict.fromkeys(["step", *features, metadata.get("target", "isFraud")]))
    dataframe = pd.read_csv(RISK_DATA_PATH, usecols=columns)

    cutoff = int(metadata.get("temporal_holdout_step_cutoff", dataframe["step"].max()))
    holdout = dataframe.loc[dataframe["step"] > cutoff].copy()

    if holdout.empty:
        holdout = dataframe.copy()

    return holdout


@st.cache_resource(show_spinner=False)
def load_pipeline():
    """Carga el pipeline serializado usado por la API."""
    return joblib.load(PIPELINE_PATH)


@st.cache_data(show_spinner=False)
def get_power_bi_url() -> str | None:
    """Recupera la URL de Power BI desde variables de entorno o secrets."""
    env_url = os.getenv("POWER_BI_URL")
    if env_url:
        return env_url

    try:
        return st.secrets.get("POWER_BI_URL")
    except Exception:  # pragma: no cover - depende del runtime de Streamlit
        return None


@st.cache_data(show_spinner=False)
def get_overview_metrics() -> dict[str, Any]:
    """Resume el contexto principal del proyecto para la portada."""
    raw = load_raw_sample()
    metadata = load_metadata()
    transfer_amounts = raw.loc[raw["type"].eq("TRANSFER"), "amount"]
    high_amount_threshold = (
        float(transfer_amounts.quantile(0.95))
        if not transfer_amounts.empty
        else float(raw["amount"].quantile(0.95))
    )

    return {
        "transacciones_analizadas": int(len(raw)),
        "fraudes_detectados_muestra": int(raw["isFraud"].sum()),
        "fraud_rate_pct": float(raw["isFraud"].mean() * 100),
        "umbral_monto_alto_transfer": high_amount_threshold,
        "modelo": metadata.get("model_name", "modelo_no_identificado"),
        "threshold_modelo": float(metadata.get("threshold_selected", 0.5)),
        "features_modelo": len(metadata.get("features_finales", [])),
    }


@st.cache_data(show_spinner=False)
def get_eda_summary() -> dict[str, Any]:
    """Calcula agregados de EDA para alimentar los graficos."""
    raw = load_raw_sample().copy()
    risk = load_risk_sample().copy()

    fraud_counts = (
        raw["isFraud"]
        .value_counts()
        .rename(index={0: "No fraude", 1: "Fraude"})
        .reset_index()
    )
    fraud_counts.columns = ["clase", "transacciones"]

    fraud_rate_by_type = (
        raw.groupby("type", observed=True)["isFraud"]
        .agg(["count", "mean"])
        .reset_index()
        .rename(columns={"count": "transacciones", "mean": "fraud_rate"})
        .sort_values("fraud_rate", ascending=False)
    )
    fraud_rate_by_type["fraud_rate_pct"] = fraud_rate_by_type["fraud_rate"] * 100

    amount_sample = raw.copy()
    amount_sample["clase"] = amount_sample["isFraud"].map({0: "No fraude", 1: "Fraude"})
    upper_amount = float(amount_sample["amount"].quantile(0.99))
    amount_sample = amount_sample.loc[amount_sample["amount"] <= upper_amount].copy()

    risk_level_distribution = (
        risk["risk_level"]
        .value_counts()
        .rename_axis("risk_level")
        .reset_index(name="transacciones")
    )

    risk_variable_columns = {
        "Ratio monto/saldo": "ratio_monto_saldo",
        "Cantidad de flags": "cantidad_flags",
        "Monto alto": "flag_monto_alto",
        "Transferencia": "flag_transfer",
        "Regla ratio alto": "regla_ratio_alto",
        "Regla monto alto + transfer": "regla_monto_alto_transfer",
    }

    comparison_rows = []
    for label, column in risk_variable_columns.items():
        summary = risk.groupby("isFraud", observed=True)[column].mean()
        comparison_rows.append(
            {
                "variable": label,
                "No fraude": float(summary.get(0, 0.0)),
                "Fraude": float(summary.get(1, 0.0)),
            }
        )

    risk_variable_comparison = pd.DataFrame(comparison_rows)
    risk_variable_comparison["brecha"] = (
        risk_variable_comparison["Fraude"] - risk_variable_comparison["No fraude"]
    ).abs()
    risk_variable_comparison = risk_variable_comparison.sort_values("brecha", ascending=False)

    return {
        "fraud_counts": fraud_counts,
        "fraud_rate_by_type": fraud_rate_by_type,
        "amount_sample": amount_sample,
        "risk_level_distribution": risk_level_distribution,
        "risk_variable_comparison": risk_variable_comparison,
        "raw_sample_rows": RAW_SAMPLE_ROWS,
        "sample_note": (
            f"Los graficos se construyen con una muestra de hasta {RAW_SAMPLE_ROWS:,} "
            "transacciones para mantener la app fluida."
        ),
    }


@st.cache_data(show_spinner=False)
def get_model_story() -> dict[str, Any]:
    """Construye el relato del modelado usando metadata y el pipeline desplegado."""
    metadata = load_metadata()
    holdout = load_model_holdout()
    pipeline = load_pipeline()
    features = metadata.get("features_finales", load_features())
    target = metadata.get("target", "isFraud")

    scores = pipeline.predict_proba(holdout[features])[:, 1]
    precision, recall, thresholds = precision_recall_curve(holdout[target], scores)

    curve_frame = pd.DataFrame({"precision": precision, "recall": recall})
    step = max(len(curve_frame) // 250, 1)
    curve_frame = curve_frame.iloc[::step].copy()

    threshold_frame = pd.DataFrame(
        [
            {
                "escenario": "Threshold operativo API",
                "threshold": float(metadata.get("threshold_selected", 0.5)),
            },
            {
                "escenario": "Threshold referencia validacion",
                "threshold": float(metadata.get("threshold_referencia_validacion", 0.5)),
            },
        ]
    )

    benchmark_rows = []
    if BENCHMARK_PATH.exists():
        raw_benchmark = _load_json(BENCHMARK_PATH)
        if isinstance(raw_benchmark, list):
            benchmark_rows = raw_benchmark

    if not benchmark_rows:
        benchmark_rows = [
            {
                "modelo": "Logistic Regression",
                "estado": "Baseline de notebook",
                "precision": None,
                "recall": None,
                "f1_score": None,
                "pr_auc": None,
                "comentario": (
                    "Se uso como baseline interpretable para estudiar el trade-off "
                    "entre fraude detectado y falsas alertas."
                ),
            },
            {
                "modelo": "RandomForest operativo",
                "estado": "Modelo desplegado en API",
                "precision": metadata["metricas_temporal_holdout"]["precision"],
                "recall": metadata["metricas_temporal_holdout"]["recall"],
                "f1_score": metadata["metricas_temporal_holdout"]["f1_score"],
                "pr_auc": metadata["metricas_temporal_holdout"]["pr_auc"],
                "comentario": (
                    "Se eligio para la API por su desempeno sobre holdout temporal "
                    "y por excluir variables posteriores a la transaccion."
                ),
            },
        ]

    benchmark = pd.DataFrame(benchmark_rows)

    return {
        "metadata": metadata,
        "curve": curve_frame,
        "thresholds": threshold_frame,
        "benchmark": benchmark,
        "benchmark_has_numeric_baseline": benchmark["precision"].notna().sum() > 1,
    }


def make_class_distribution_chart(data: pd.DataFrame):
    """Genera el grafico de distribucion fraude vs no fraude."""
    fig, ax = plt.subplots(figsize=(6, 4), facecolor=PALETTE["fondo"])
    sns.barplot(
        data=data,
        x="clase",
        y="transacciones",
        palette=[PALETTE["seguro"], PALETTE["fraude"]],
        ax=ax,
    )
    ax.set_title("Distribucion de transacciones")
    ax.set_xlabel("")
    ax.set_ylabel("Cantidad")
    ax.ticklabel_format(style="plain", axis="y")
    sns.despine(ax=ax)
    plt.tight_layout()
    return fig


def make_fraud_rate_by_type_chart(data: pd.DataFrame):
    """Genera el grafico de tasa de fraude por tipo de transaccion."""
    fig, ax = plt.subplots(figsize=(7, 4), facecolor=PALETTE["fondo"])
    sns.barplot(
        data=data,
        x="type",
        y="fraud_rate_pct",
        color=PALETTE["seguro"],
        ax=ax,
    )
    ax.set_title("Tasa de fraude por tipo de transaccion")
    ax.set_xlabel("Tipo")
    ax.set_ylabel("% de fraude")
    sns.despine(ax=ax)
    plt.tight_layout()
    return fig


def make_amount_boxplot(data: pd.DataFrame):
    """Genera boxplots de monto segun clase."""
    fig, ax = plt.subplots(figsize=(7, 4), facecolor=PALETTE["fondo"])
    sns.boxplot(
        data=data,
        x="clase",
        y="amount",
        palette=[PALETTE["seguro"], PALETTE["fraude"]],
        ax=ax,
    )
    ax.set_yscale("log")
    ax.set_title("Montos por clase (escala log)")
    ax.set_xlabel("")
    ax.set_ylabel("Monto")
    sns.despine(ax=ax)
    plt.tight_layout()
    return fig


def make_risk_level_chart(data: pd.DataFrame):
    """Genera el grafico de niveles de riesgo."""
    palette = ["#52796f", "#d8a657", "#c97c3d", "#b23a48"]
    fig, ax = plt.subplots(figsize=(6, 4), facecolor=PALETTE["fondo"])
    sns.barplot(
        data=data,
        x="risk_level",
        y="transacciones",
        palette=palette,
        ax=ax,
    )
    ax.set_title("Distribucion de niveles de riesgo")
    ax.set_xlabel("Nivel")
    ax.set_ylabel("Cantidad")
    ax.ticklabel_format(style="plain", axis="y")
    sns.despine(ax=ax)
    plt.tight_layout()
    return fig


def make_risk_variable_chart(data: pd.DataFrame):
    """Genera el grafico comparativo de variables de riesgo."""
    melted = data.melt(
        id_vars=["variable", "brecha"],
        value_vars=["No fraude", "Fraude"],
        var_name="clase",
        value_name="valor",
    )
    fig, ax = plt.subplots(figsize=(9, 4.8), facecolor=PALETTE["fondo"])
    sns.barplot(
        data=melted,
        x="variable",
        y="valor",
        hue="clase",
        palette={"No fraude": PALETTE["seguro"], "Fraude": PALETTE["fraude"]},
        ax=ax,
    )
    ax.set_title("Senales operativas: fraude vs no fraude")
    ax.set_xlabel("")
    ax.set_ylabel("Promedio / proporcion")
    ax.tick_params(axis="x", rotation=24)
    ax.legend(title="")
    sns.despine(ax=ax)
    plt.tight_layout()
    return fig


def make_metric_bar_chart(metadata: dict[str, Any]):
    """Genera un grafico de barras para las metricas del modelo final."""
    metrics = metadata.get("metricas_temporal_holdout", {})
    frame = pd.DataFrame(
        {
            "metrica": ["precision", "recall", "f1_score", "pr_auc"],
            "valor": [
                float(metrics.get("precision", 0.0)),
                float(metrics.get("recall", 0.0)),
                float(metrics.get("f1_score", 0.0)),
                float(metrics.get("pr_auc", 0.0)),
            ],
        }
    )
    fig, ax = plt.subplots(figsize=(7, 4), facecolor=PALETTE["fondo"])
    sns.barplot(data=frame, x="metrica", y="valor", color=PALETTE["seguro"], ax=ax)
    ax.set_ylim(0, 1.05)
    ax.set_title("Metricas del modelo desplegado")
    ax.set_xlabel("")
    ax.set_ylabel("Score")
    sns.despine(ax=ax)
    plt.tight_layout()
    return fig


def make_precision_recall_curve(curve: pd.DataFrame):
    """Genera la curva precision-recall del modelo desplegado."""
    fig, ax = plt.subplots(figsize=(6.5, 4.5), facecolor=PALETTE["fondo"])
    ax.plot(
        curve["recall"],
        curve["precision"],
        color=PALETTE["fraude"],
        linewidth=2.2,
    )
    ax.set_title("Precision-Recall del pipeline desplegado")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0, 1.05)
    ax.grid(alpha=0.25)
    sns.despine(ax=ax)
    plt.tight_layout()
    return fig
