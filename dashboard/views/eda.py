"""Vista de analisis exploratorio y evaluacion de riesgo."""

from __future__ import annotations

import streamlit as st

try:
    from dashboard.components.ui import (
        render_capability_card,
        render_section_header,
        render_subsection_header,
        render_text_block,
        section_card,
    )
    from dashboard.services.story_data import (
        get_eda_summary,
        make_amount_boxplot,
        make_class_distribution_chart,
        make_fraud_rate_by_type_chart,
        make_risk_level_chart,
        make_risk_variable_chart,
    )
except ModuleNotFoundError:  # pragma: no cover - fallback para streamlit desde dashboard/
    from components.ui import (
        render_capability_card,
        render_section_header,
        render_subsection_header,
        render_text_block,
        section_card,
    )
    from services.story_data import (
        get_eda_summary,
        make_amount_boxplot,
        make_class_distribution_chart,
        make_fraud_rate_by_type_chart,
        make_risk_level_chart,
        make_risk_variable_chart,
    )


def render() -> None:
    """Renderiza la seccion de analisis del dashboard."""
    summary = get_eda_summary()

    render_section_header(
        "Patrones del fraude en transacciones",
        (
            'Este bloque responde a la pregunta "\u00bfComo se comporta el fraude '
            'en los datos?" Aqui se observan los patrones base del fraude para '
            "entender su frecuencia, los tipos de operacion donde se concentra y "
            "como se comportan los montos. Los graficos se construyen con una "
            f"muestra de hasta {summary['raw_sample_rows']:,} transacciones para "
            "mantener la app fluida."
        ),
        eyebrow="Analisis exploratorio",
    )
    st.markdown("<div class='space-32'></div>", unsafe_allow_html=True)

    render_subsection_header("Principales hallazgos")
    finding_cols = st.columns(4)
    findings = [
        (
            "\u2696\ufe0f",
            "Fraude minoritario",
            "El fraude representa una fraccion muy pequena del total analizado.",
        ),
        (
            "\U0001F4B3",
            "Concentracion por tipo",
            "El riesgo se acumula en ciertos tipos de transaccion.",
        ),
        (
            "\U0001F4B0",
            "Montos diferenciados",
            "Las operaciones riesgosas muestran patrones de monto distintos.",
        ),
        (
            "\U0001F50D",
            "Senales visibles",
            "Los datos permiten identificar patrones tempranos antes del score de riesgo.",
        ),
    ]
    for column, (icon, title, body) in zip(finding_cols, findings, strict=True):
        with column:
            render_capability_card(icon, title, body)

    st.markdown("<div class='space-32'></div>", unsafe_allow_html=True)

    pattern_tabs = st.tabs(["Frecuencia", "Tipos", "Montos"])

    with pattern_tabs[0]:
        _render_eda_tab(
            title="\u00bfQue tan frecuente es el fraude?",
            description=(
                "A partir de la base de datos PaySim se identifica la variable "
                "objetivo isFraud, la cual indica si una transaccion corresponde o "
                "no a un caso de fraude.\n\n"
                "Esto permite comparar directamente el volumen de operaciones "
                "legitimas frente a las fraudulentas, dimensionando el nivel real "
                "de incidencia dentro del sistema.\n\n"
                "Aunque el volumen total es alto, los casos de fraude representan "
                "una fraccion muy pequena, lo que implica un desafio importante "
                "para su deteccion."
            ),
            insight=(
                "La baja incidencia del fraude obliga a priorizar una deteccion "
                "precisa sobre volumenes muy altos de operaciones."
            ),
            figure=make_class_distribution_chart(summary["fraud_counts"]),
            interpretation=(
                "La data evidencia un fuerte desbalance en la variable objetivo: "
                "la gran mayoria de las transacciones no corresponden a fraude, "
                "mientras que los casos fraudulentos son escasos.\n\n"
                "Este comportamiento es tipico en escenarios reales y obliga a "
                "replantear el uso de metricas tradicionales, ya que indicadores "
                "como accuracy pueden resultar enganosos."
            ),
        )

    with pattern_tabs[1]:
        _render_eda_tab(
            title="\u00bfEn que tipos se concentra?",
            description=(
                "Se observa como se distribuyen las transacciones segun su tipo "
                "para identificar donde se concentra la actividad y el riesgo.\n\n"
                "El dataset PaySim considera cinco tipos principales: TRANSFER "
                "(transferencia), CASH_OUT (retiro), CASH_IN (deposito), DEBIT "
                "(pago con debito) y PAYMENT (pago general).\n\n"
                "Esto permite entender en que tipos de operacion se concentra la "
                "actividad y detectar posibles focos donde el fraude podria "
                "manifestarse con mayor frecuencia."
            ),
            insight=(
                "No todos los tipos de transaccion presentan la misma exposicion "
                "operativa al fraude."
            ),
            figure=make_fraud_rate_by_type_chart(summary["fraud_rate_by_type"]),
            interpretation=(
                "El fraude no se distribuye de forma uniforme entre los distintos "
                "tipos de transaccion.\n\n"
                "TRANSFER (transferencias) y CASH_OUT (retiros) concentran la "
                "mayor proporcion de casos fraudulentos, lo que sugiere que estos "
                "movimientos representan escenarios de mayor riesgo operativo."
            ),
        )

    with pattern_tabs[2]:
        _render_eda_tab(
            title="\u00bfLos montos diferencian fraude?",
            description=(
                "Se comparan los montos de las transacciones entre casos de fraude "
                "y no fraude utilizando un boxplot.\n\n"
                "Este tipo de visualizacion permite observar la distribucion de "
                "los datos, incluyendo mediana, cuantiles y valores extremos.\n\n"
                "Asi, se puede evaluar si existen diferencias relevantes en el "
                "comportamiento de los montos entre ambos grupos."
            ),
            insight=(
                "El monto aparece como una senal relevante para diferenciar "
                "operaciones normales de eventos potencialmente riesgosos."
            ),
            figure=make_amount_boxplot(summary["amount_sample"]),
            interpretation=(
                "Las transacciones fraudulentas tienden a concentrarse en montos "
                "mas elevados en comparacion con las transacciones normales.\n\n"
                "El monto minimo observado en fraude es significativamente mayor, "
                "lo que sugiere que estos eventos no suelen ocurrir en montos bajos.\n\n"
                "Ademas, la presencia de valores extremos refuerza la importancia "
                "del monto como variable clave en la deteccion de riesgo."
            ),
        )

    st.markdown("<div class='space-32'></div>", unsafe_allow_html=True)

    render_section_header(
        "\u00bfComo se mide el riesgo?",
        (
            "Este bloque separa la logica de negocio del analisis exploratorio para "
            "mostrar como se construye y valida la primera capa de evaluacion. "
            "A partir de senales operativas simples, las transacciones se ordenan "
            "en niveles de riesgo para priorizar alertas antes de aplicar el "
            "modelo de machine learning."
        ),
        eyebrow="Evaluacion de riesgo",
    )
    st.markdown("<div class='space-32'></div>", unsafe_allow_html=True)

    render_subsection_header("Reglas de negocio")
    render_text_block(
        "Estas reglas resumen criterios operativos que permiten traducir patrones "
        "observados en una evaluacion de riesgo clara y accionable."
    )
    st.markdown("<div class='space-24'></div>", unsafe_allow_html=True)

    rule_cols = st.columns(4)
    rule_cards = [
        (
            "\U0001F4CF",
            "Ratio monto/saldo alto",
            "Cuando la diferencia entre cuentas es significativa, aumenta el riesgo.",
        ),
        (
            "\U0001F501",
            "Transferencias",
            "Las transferencias presentan mayor exposicion a fraude.",
        ),
        (
            "\U0001F4B8",
            "Monto alto",
            "Montos elevados representan mayor impacto potencial.",
        ),
        (
            "\U0001F9E9",
            "Regla combinada",
            "La combinacion de multiples senales aumenta la probabilidad de fraude.",
        ),
    ]
    for column, (icon, title, body) in zip(rule_cols, rule_cards, strict=True):
        with column:
            render_capability_card(icon, title, body)

    st.markdown("<div class='space-32'></div>", unsafe_allow_html=True)

    render_subsection_header("Validacion del riesgo")
    risk_tabs = st.tabs(["Niveles de riesgo", "Senales operativas"])

    with risk_tabs[0]:
        _render_eda_tab(
            title="\u00bfComo se distribuyen los niveles de riesgo?",
            description=(
                "A partir de un conjunto de condiciones operativas, cada "
                "transaccion es evaluada y asignada a una categoria que refleja "
                "su nivel de exposicion. Esto permite clasificar la muestra en "
                "distintos niveles de riesgo y priorizar alertas antes de aplicar "
                "modelos mas complejos."
            ),
            insight=(
                "Las reglas permiten construir una capa inicial de priorizacion "
                "para ordenar la operacion antes del modelo predictivo."
            ),
            figure=make_risk_level_chart(summary["risk_level_distribution"]),
            interpretation=(
                "La segmentacion en niveles de riesgo muestra como las reglas "
                "logran organizar la muestra en grupos diferenciados.\n\n"
                "Esto facilita la toma de decisiones operativas, permitiendo "
                "enfocar la atencion en las transacciones con mayor probabilidad "
                "de fraude antes incluso de aplicar el modelo predictivo."
            ),
        )

    with risk_tabs[1]:
        _render_eda_tab(
            title="\u00bfQue senales operativas explican el riesgo?",
            description=(
                "Se analizan variables operativas clave para entender que senales "
                "generan mayor diferencia entre transacciones fraudulentas y no "
                "fraudulentas. Estas variables fueron utilizadas como base para "
                "construir las reglas de riesgo."
            ),
            insight=(
                "Las diferencias entre ambas clases respaldan que las reglas "
                "operativas capturan senales utiles para priorizar alertas."
            ),
            figure=make_risk_variable_chart(summary["risk_variable_comparison"]),
            interpretation=(
                "Variables como el ratio monto/saldo, la presencia de "
                "transferencias y la combinacion de reglas operativas muestran "
                "diferencias claras entre fraude y no fraude.\n\n"
                "En particular, cuando existe una alta variabilidad entre montos "
                "o diferencias significativas entre cuentas, aumenta "
                "considerablemente la probabilidad de que la transaccion sea "
                "riesgosa.\n\n"
                "Esto es coherente con escenarios reales, donde movimientos "
                "abruptos o desproporcionados suelen activar alertas."
            ),
        )

    st.markdown("<div class='space-32'></div>", unsafe_allow_html=True)
    with section_card():
        render_text_block(
            "En conjunto, las reglas operativas permiten construir una primera "
            "capa de evaluacion del riesgo, que luego es refinada por el modelo "
            "de machine learning para mejorar la precision en la deteccion de fraude."
        )


def _render_eda_tab(
    *,
    title: str,
    description: str,
    insight: str,
    figure,
    interpretation: str,
) -> None:
    """Renderiza un grafico narrativo con explicacion de negocio."""
    with section_card():
        chart_col, text_col = st.columns([1.8, 1], vertical_alignment="center")
        with chart_col:
            st.pyplot(figure, use_container_width=True)
            st.markdown("<div class='space-24'></div>", unsafe_allow_html=True)
            with st.expander("Ver interpretacion"):
                _render_paragraphs(interpretation)
        with text_col:
            render_subsection_header(title)
            _render_paragraphs(description)
            st.markdown("<div class='space-24'></div>", unsafe_allow_html=True)
            render_text_block(insight)


def _render_paragraphs(text: str) -> None:
    """Renderiza un texto largo como varios parrafos breves."""
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]
    for paragraph in paragraphs:
        render_text_block(paragraph)
