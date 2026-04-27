"""Helpers visuales para unificar la UI del dashboard de fraude."""

from __future__ import annotations

from contextlib import contextmanager
from html import escape
from textwrap import dedent
from typing import Iterator

import streamlit as st


@contextmanager
def section_card() -> Iterator[None]:
    """Crea una card base usando el contenedor nativo con borde."""
    with st.container(border=True):
        yield


def render_section_header(
    title: str,
    subtitle: str | None = None,
    eyebrow: str | None = None,
) -> None:
    """Renderiza el encabezado principal de una seccion."""
    eyebrow_html = (
        f"<div class='section-eyebrow'>{escape(eyebrow)}</div>" if eyebrow else ""
    )
    subtitle_html = (
        f"<p class='section-subtitle'>{escape(subtitle)}</p>" if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="section-header">
            {eyebrow_html}
            <h1>{escape(title)}</h1>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_subsection_header(title: str, subtitle: str | None = None) -> None:
    """Renderiza un subtitulo consistente."""
    subtitle_html = (
        f"<p class='subsection-copy'>{escape(subtitle)}</p>" if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="subsection-header">
            <h2>{escape(title)}</h2>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_text_block(text: str) -> None:
    """Renderiza un bloque de texto descriptivo."""
    st.markdown(
        f"<p class='text-block'>{escape(text)}</p>",
        unsafe_allow_html=True,
    )


def render_info_card(
    title: str,
    body: str,
    eyebrow: str | None = None,
    tags: list[str] | None = None,
    variant: str = "default",
) -> None:
    """Renderiza una card informativa estatica."""
    eyebrow_html = (
        f"<div class='card-eyebrow'>{escape(eyebrow)}</div>" if eyebrow else ""
    )
    tags_html = ""
    if tags:
        tags_html = "<div class='chip-row'>" + "".join(
            f"<span class='chip'>{escape(tag)}</span>" for tag in tags
        ) + "</div>"

    html = dedent(
        f"""
        <div class="info-card info-card-{escape(variant)}">
            {eyebrow_html}
            <h3>{escape(title)}</h3>
            <p>{escape(body)}</p>
            {tags_html}
        </div>
        """
    ).strip()

    st.html(html)


def render_metric_card(
    label: str,
    value: str,
    tone: str = "default",
    caption: str | None = None,
    variant: str = "default",
) -> None:
    """Renderiza una tarjeta de metrica."""
    caption_html = (
        f"<div class='metric-caption'>{escape(caption)}</div>" if caption else ""
    )
    st.markdown(
        f"""
        <div class="metric-card metric-{escape(tone)} metric-{escape(variant)}">
            <div class="metric-label">{escape(label)}</div>
            <div class="metric-value">{escape(value)}</div>
            {caption_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_capability_card(icon: str, title: str, body: str) -> None:
    """Renderiza una card compacta para resumir capacidades del producto."""
    st.markdown(
        f"""
        <div class="capability-card">
            <div class="capability-icon">{escape(icon)}</div>
            <div class="capability-title">{escape(title)}</div>
            <div class="capability-body">{escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart_card(
    title: str,
    figure,
    explanation: str,
    info_label: str = "Ver interpretación",
    subtitle: str | None = None,
) -> None:
    """Renderiza una card de grafico con panel explicativo expandible."""
    with section_card():
        render_subsection_header(title, subtitle)
        st.pyplot(figure, use_container_width=True)
        with st.expander(info_label):
            paragraphs = [
                paragraph.strip() for paragraph in explanation.split("\n\n") if paragraph.strip()
            ]
            for paragraph in paragraphs:
                st.markdown(
                    f"<div class='info-panel'>{escape(paragraph)}</div>",
                    unsafe_allow_html=True,
                )


def render_prediction_result_card(
    label: str,
    probability: float,
    threshold: float,
    tone: str,
) -> None:
    """Renderiza el resultado principal de la predicción."""
    probability_pct = f"{probability:.2%}"
    threshold_value = f"{threshold:.2f}"
    indicator_label = "Riesgo alto" if tone == "critico" else "Riesgo bajo"

    st.markdown(
        f"""
        <div class="prediction-card prediction-{escape(tone)}">
            <div class="prediction-header">
                <div>
                    <div class="prediction-label">Resultado</div>
                    <div class="prediction-class">{escape(label)}</div>
                </div>
                <div class="risk-indicator risk-{escape(tone)}">{escape(indicator_label)}</div>
            </div>
            <div class="prediction-grid">
                <div class="prediction-metric">
                    <span>Probabilidad</span>
                    <strong>{probability_pct}</strong>
                </div>
                <div class="prediction-metric">
                    <span>Threshold</span>
                    <strong>{threshold_value}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
