"""Vista de desempeño y decisiones del modelo de fraude."""

from __future__ import annotations

import pandas as pd
import streamlit as st

try:
    from dashboard.components.ui import (
        render_capability_card,
        render_metric_card,
        render_section_header,
        render_subsection_header,
        render_text_block,
        section_card,
    )
    from dashboard.services.story_data import (
        get_model_story,
        make_metric_bar_chart,
        make_precision_recall_curve,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback para streamlit desde dashboard/
    from components.ui import (
        render_capability_card,
        render_metric_card,
        render_section_header,
        render_subsection_header,
        render_text_block,
        section_card,
    )
    from services.story_data import (
        get_model_story,
        make_metric_bar_chart,
        make_precision_recall_curve,
    )


def render() -> None:
    """Renderiza la sección de modelo sin alterar métricas ni gráficos.

    Retorna:
        None: Streamlit muestra el bloque de desempeño, comparación y operación.
    """
    story = get_model_story()
    metadata = story["metadata"]
    benchmark = _build_benchmark_table(story["benchmark"])
    metrics = metadata.get("metricas_temporal_holdout", {})

    render_section_header(
        "¿Cómo toma decisiones el modelo?",
        (
            "El modelo fue entrenado utilizando la base de datos PaySim, donde "
            "aprendió a distinguir entre transacciones normales y fraudulentas a "
            "partir de patrones reales en los datos. A diferencia de un enfoque "
            "manual, este sistema no evalúa una sola variable, sino combinaciones "
            "de señales que, en conjunto, permiten anticipar cuándo una operación "
            "podría representar un riesgo."
        ),
        eyebrow="Selección del modelo",
    )

    metric_cols = st.columns(4)
    metric_cards = [
        (
            "🎯 Precisión",
            f"{float(metrics.get('precision', 0.0)):.3f}",
            "positive",
            (
                "Mide qué tan confiables son las alertas del modelo. Un valor alto "
                "indica que cuando el sistema marca fraude, probablemente es correcto."
            ),
        ),
        (
            "🔎 Recall",
            f"{float(metrics.get('recall', 0.0)):.3f}",
            "positive",
            (
                "Indica cuántos fraudes reales logra detectar el modelo. Un recall "
                "alto significa que deja pasar muy pocos casos peligrosos."
            ),
        ),
        (
            "⚖️ F1 Score",
            f"{float(metrics.get('f1_score', 0.0)):.3f}",
            "positive",
            (
                "Equilibra precisión y cobertura. Permite evaluar si el modelo "
                "detecta fraudes sin generar un exceso de falsas alertas."
            ),
        ),
        (
            "📈 PR AUC",
            f"{float(metrics.get('pr_auc', 0.0)):.3f}",
            "emphasis",
            (
                "Resume el comportamiento del modelo en distintos escenarios. Es "
                "especialmente útil en fraude, donde los casos reales son escasos."
            ),
        ),
    ]
    for column, (label, value, tone, caption) in zip(metric_cols, metric_cards, strict=True):
        with column:
            render_metric_card(
                label,
                value,
                tone=tone,
                caption=caption,
                variant="highlight",
            )

    st.markdown("<div class='space-24'></div>", unsafe_allow_html=True)
    with st.expander("Ver interpretación"):
        render_text_block(
            "El modelo alcanza una precisión perfecta (1.000), lo que indica que "
            "prácticamente todas las alertas generadas corresponden a fraudes reales. "
            "Esto ocurre porque en los datos existe una separación clara entre "
            "comportamientos normales y sospechosos."
        )
        render_text_block(
            "Sin embargo, el recall (0.875) muestra que aún existen algunos casos "
            "de fraude que no son detectados. Este equilibrio es intencional: en "
            "contextos reales, es preferible evitar alertas innecesarias sin dejar "
            "de capturar la mayoría de los eventos críticos."
        )
        render_text_block(
            "En conjunto, las métricas reflejan un modelo que no solo memoriza los "
            "datos, sino que logra generalizar patrones útiles para la detección de fraude."
        )

    with section_card():
        render_subsection_header("Comparación de modelos")
        render_text_block(
            "La comparación resume el rol del baseline y del modelo que pasó a producción, "
            "priorizando una lectura ejecutiva de desempeño e implicancia operativa."
        )
        st.table(_style_benchmark_table(benchmark))

    if not story["benchmark_has_numeric_baseline"]:
        with section_card():
            with st.expander("⚙️ Ver detalle técnico"):
                render_text_block(
                    "La app muestra todas las métricas serializadas del modelo desplegado. "
                    "Si luego exportas un benchmark comparativo desde el notebook a "
                    "`artifacts/dashboard_model_benchmark.json`, esta tabla se completará "
                    "automáticamente con la comparación numérica."
                )

    chart_left, chart_right = st.columns(2)
    with chart_left:
        _render_visible_chart_card(
            title="Métricas del modelo",
            figure=make_metric_bar_chart(metadata),
            subtitle="Vista sintética del rendimiento del modelo desplegado.",
            explanation=(
                "El gráfico resume cómo responde el modelo en las dimensiones que más "
                "importan para el negocio: confianza en las alertas, cobertura de "
                "fraudes reales y equilibrio general entre detección y ruido operativo."
            ),
        )
    with chart_right:
        _render_visible_chart_card(
            title="Curva Precision-Recall",
            figure=make_precision_recall_curve(story["curve"]),
            subtitle="Curva generada sobre el holdout temporal del pipeline desplegado.",
            explanation=(
                "La curva precision-recall muestra cómo cambia el comportamiento del "
                "modelo al ajustar el nivel de sensibilidad.\n\n"
                "En escenarios de fraude, donde los casos reales son poco frecuentes, "
                "esta curva permite entender el equilibrio entre detectar más fraudes "
                "(recall) y evitar falsas alarmas (precisión).\n\n"
                "El comportamiento observado confirma que el modelo mantiene alta "
                "precisión incluso al aumentar la cobertura, lo que respalda su uso "
                "en un entorno operativo real."
            ),
        )

    with section_card():
        render_subsection_header("Para considerar en producción")
        render_text_block(
            "La selección final prioriza realismo operativo y decisiones utilizables "
            "en producción sin depender de información que no estaría disponible al "
            "momento de evaluar la transacción."
        )
        st.markdown("<div class='space-24'></div>", unsafe_allow_html=True)

        note_cols = st.columns(4)
        notes = [
            (
                "🎯",
                "Enfoque operativo",
                "El modelo prioriza decisiones aplicables en contexto real sobre métricas teóricas.",
            ),
            (
                "⏱",
                "Variables en tiempo real",
                "Solo utiliza información disponible al momento de la transacción.",
            ),
            (
                "⚖️",
                "Balance controlado",
                "Mantiene equilibrio entre detección de fraude y volumen de alertas.",
            ),
            (
                "🔧",
                "Threshold ajustable",
                "El umbral 0.50 funciona como base, pero puede calibrarse en producción.",
            ),
        ]
        for column, (icon, title, body) in zip(note_cols, notes, strict=True):
            with column:
                render_capability_card(icon, title, body)

        st.markdown("<div class='space-24'></div>", unsafe_allow_html=True)
        render_text_block(
            "En términos operativos, este modelo permite priorizar revisiones en "
            "aquellas transacciones con mayor probabilidad de fraude, reduciendo "
            "carga innecesaria y enfocando los recursos en los casos realmente críticos."
        )


def _build_benchmark_table(benchmark: pd.DataFrame) -> pd.DataFrame:
    """Normaliza la tabla comparativa para una lectura ejecutiva.

    Parámetros:
        benchmark (pd.DataFrame): Tabla base con resultados y comentarios del modelo.

    Retorna:
        pd.DataFrame: Vista renombrada y resumida para el dashboard.
    """
    frame = benchmark.copy()

    status_mapping = {
        "Baseline de notebook": "Baseline",
        "Modelo desplegado en API": "Producción",
    }
    insight_mapping = {
        "Logistic Regression": "Modelo base para entender trade-off detección vs falsas alertas",
        "RandomForest operativo": "Mejor desempeño en datos temporales con variables operativas",
    }

    frame["estado"] = frame["estado"].replace(status_mapping)
    frame["comentario"] = frame["modelo"].map(insight_mapping).fillna(frame["comentario"])

    numeric_columns = ["precision", "recall", "f1_score", "pr_auc"]
    for column in numeric_columns:
        frame[column] = frame[column].apply(
            lambda value: "-" if pd.isna(value) else f"{float(value):.3f}"
        )

    frame = frame.rename(
        columns={
            "modelo": "Modelo",
            "estado": "Tipo",
            "precision": "Precisión",
            "recall": "Recall",
            "f1_score": "F1",
            "pr_auc": "PR AUC",
            "comentario": "Insight",
        }
    )

    return frame[["Modelo", "Tipo", "Precisión", "Recall", "F1", "PR AUC", "Insight"]]


def _style_benchmark_table(benchmark: pd.DataFrame):
    """Aplica formato visual para mejorar lectura y evitar scroll lateral.

    Parámetros:
        benchmark (pd.DataFrame): Tabla formateada para la comparación de modelos.

    Retorna:
        Styler: Estilo visual aplicado para su renderización en Streamlit.
    """
    return benchmark.style.hide(axis="index").set_table_styles(
        [
            {"selector": "th.col_heading", "props": "text-align: left;"},
            {"selector": "th.col0", "props": "width: 18%;"},
            {"selector": "th.col1", "props": "width: 10%;"},
            {"selector": "th.col2, th.col3, th.col4, th.col5", "props": "width: 8%;"},
            {"selector": "th.col6", "props": "width: 32%;"},
        ]
    )


def _render_visible_chart_card(
    *,
    title: str,
    figure,
    subtitle: str,
    explanation: str,
) -> None:
    """Renderiza un gráfico con interpretación expandible.

    Parámetros:
        title (str): Título visible del bloque.
        figure: Figura de Matplotlib ya construida.
        subtitle (str): Texto corto de contexto para el gráfico.
        explanation (str): Interpretación narrativa asociada al gráfico.

    Retorna:
        None: Streamlit renderiza el gráfico y su interpretación expandible.
    """
    with section_card():
        render_subsection_header(title, subtitle)
        st.pyplot(figure, use_container_width=True)
        with st.expander("Ver interpretación"):
            for paragraph in [part.strip() for part in explanation.split("\n\n") if part.strip()]:
                render_text_block(paragraph)
