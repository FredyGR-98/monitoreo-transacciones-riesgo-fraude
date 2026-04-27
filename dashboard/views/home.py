"""Vista de contexto operativo para el dashboard de fraude."""

from __future__ import annotations

from html import escape

import streamlit as st

try:
    from dashboard.components.ui import (
        render_capability_card,
        render_info_card,
        render_metric_card,
        render_subsection_header,
        render_text_block,
    )
    from dashboard.services.api_client import ApiClientError
    from dashboard.services.story_data import get_overview_metrics
except ModuleNotFoundError:  # pragma: no cover - fallback para streamlit desde dashboard/
    from components.ui import (
        render_capability_card,
        render_info_card,
        render_metric_card,
        render_subsection_header,
        render_text_block,
    )
    from services.api_client import ApiClientError
    from services.story_data import get_overview_metrics


def render(api_client) -> None:
    """Renderiza la portada operativa del dashboard.

    Parámetros:
        api_client: Cliente HTTP usado para consultar el estado de la API.

    Retorna:
        None: Streamlit dibuja la vista de contexto y sus métricas principales.
    """
    overview = get_overview_metrics()

    _render_home_header(api_client)

    render_subsection_header("Qué permite hacer esta herramienta")
    capability_cols = st.columns(4)
    capability_cards = [
        ("🔍", "Detectar fraude", "Identifica transacciones sospechosas en tiempo real."),
        ("⚠️", "Evaluar riesgo", "Permite anticipar operaciones con mayor exposición."),
        ("📊", "Analizar patrones", "Visualiza comportamiento y señales de fraude."),
        ("🧠", "Simular decisiones", "Prueba escenarios antes de ejecutar acciones."),
    ]
    for column, (icon, title, body) in zip(capability_cols, capability_cards, strict=True):
        with column:
            render_capability_card(icon, title, body)

    render_subsection_header("Motor de análisis")
    render_text_block(
        "El sistema utiliza datos históricos de PaySim para evaluar transacciones "
        "mediante un modelo de aprendizaje automático, permitiendo identificar "
        "patrones de riesgo y priorizar alertas según criticidad operativa."
    )
    st.markdown("<div class='space-24'></div>", unsafe_allow_html=True)

    metrics = st.columns(4)
    with metrics[0]:
        render_metric_card(
            "Muestra",
            f"{overview['transacciones_analizadas']:,}",
            caption="Transacciones incluidas en el análisis.",
            variant="highlight",
        )
    with metrics[1]:
        render_metric_card(
            "Fraudes",
            f"{overview['fraudes_detectados_muestra']:,}",
            caption="Casos identificados como fraude en la muestra.",
            variant="highlight",
        )
    with metrics[2]:
        render_metric_card(
            "Tasa",
            f"{overview['fraud_rate_pct']:.4f}%",
            caption="Participación del fraude sobre el total analizado.",
            variant="highlight",
        )
    with metrics[3]:
        render_metric_card(
            "Variables",
            str(overview["features_modelo"]),
            tone="emphasis",
            caption="Variables usadas para evaluar cada operación.",
            variant="highlight",
        )

    render_text_block(
        "Con esta base, el sistema entrena un modelo capaz de anticipar "
        "comportamientos potencialmente fraudulentos y apoyar la detección temprana "
        "junto con la priorización de revisiones."
    )
    st.markdown("<div class='space-32'></div>", unsafe_allow_html=True)

    context_cols = st.columns(2)
    with context_cols[0]:
        render_info_card(
            "Cobertura funcional",
            (
                "La herramienta conecta contexto de negocio, análisis, modelo y API "
                "para transformar datos transaccionales en alertas claras para seguimiento operativo."
            ),
            tags=["Análisis", "API"],
            variant="light",
        )
    with context_cols[1]:
        render_info_card(
            "Parámetros operativos",
            (
                "El modelo opera con un umbral activo de "
                f"{overview['threshold_modelo']:.2f} y considera como referencia un monto "
                f"alto de {overview['umbral_monto_alto_transfer']:,.0f} para transferencias."
            ),
            tags=["PaySim", "Random Forest", f"Threshold {overview['threshold_modelo']:.2f}"],
            variant="light",
        )


def _render_home_header(api_client) -> None:
    """Renderiza la cabecera principal con estado operativo de la API.

    Parámetros:
        api_client: Cliente HTTP con capacidad de consultar `/health`.

    Retorna:
        None: Inserta el encabezado principal de la vista de contexto.
    """
    is_active = False
    status_label = "API inactiva"

    if api_client is not None:
        try:
            api_client.health()
            is_active = True
            status_label = "API activa"
        except ApiClientError:
            status_label = "API inactiva"

    badge_class = "active" if is_active else "inactive"
    meta_cols = st.columns([5, 1.4])
    with meta_cols[0]:
        st.markdown("<div class='section-eyebrow'>Contexto operativo</div>", unsafe_allow_html=True)
    with meta_cols[1]:
        st.markdown(
            f"""
            <div style="display:flex; justify-content:flex-end;">
                <div class="status-badge {badge_class}">
                    <span class="status-dot"></span>
                    <span>{escape(status_label)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="section-header">
            <h1>Monitoreo de Transacciones</h1>
            <p class="section-subtitle">
                Este dashboard simula cómo una entidad financiera puede identificar
                transacciones sospechosas antes de que se materialice un fraude.
                A partir de datos históricos (PaySim), se construyó un modelo
                capaz de detectar patrones de riesgo en tiempo real, priorizando casos
                críticos y reduciendo alertas innecesarias. El objetivo no es solo
                predecir, sino apoyar decisiones operativas: qué revisar, cuándo y por qué.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
