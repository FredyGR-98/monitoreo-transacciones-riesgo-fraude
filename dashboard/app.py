"""Aplicación Streamlit para monitoreo de transacciones y riesgo de fraude."""

from __future__ import annotations

import os

import streamlit as st

try:
    from dashboard.services.api_client import ApiClient
    from dashboard.views import eda, home, modeling, predictor
except ModuleNotFoundError:  # pragma: no cover - fallback para ejecuciones locales especiales
    from services.api_client import ApiClient
    from views import eda, home, modeling, predictor


class FraudMonitoringApp:
    """Orquesta la carga del dashboard y su conexión con la API."""

    def __init__(self) -> None:
        self.api_client: ApiClient | None = None

    def configure_page(self) -> None:
        """Configura la página principal de Streamlit.

        Retorna:
            None: Streamlit registra la configuración global de la app.
        """
        st.set_page_config(
            page_title="Monitoreo de Transacciones y Riesgo de Fraude",
            page_icon="FD",
            layout="wide",
            initial_sidebar_state="expanded",
        )

    def inject_styles(self) -> None:
        """Aplica estilos visuales compartidos para todo el dashboard.

        Retorna:
            None: Inserta la hoja de estilos en la aplicación activa.
        """
        st.markdown(
            """
            <style>
            :root {
                --green-900: #1B5E20;
                --green-700: #2E7D32;
                --green-500: #4CAF50;
                --green-200: #A5D6A7;
                --green-100: #E8F5E9;
                --surface: #ffffff;
                --surface-soft: #f6f8f6;
                --border: #dce7dc;
                --text-900: #111827;
                --text-700: #374151;
                --text-600: #4b5563;
                --shadow: 0 16px 36px rgba(27, 94, 32, 0.07);
            }
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(165, 214, 167, 0.22), transparent 26%),
                    radial-gradient(circle at right top, rgba(76, 175, 80, 0.08), transparent 24%),
                    linear-gradient(180deg, #fafcf9 0%, #f4f7f4 100%);
                color: var(--text-900);
            }
            section[data-testid="stSidebar"] {
                background:
                    radial-gradient(circle at top left, rgba(165, 214, 167, 0.16), transparent 22%),
                    linear-gradient(180deg, #16361a 0%, #0f2612 100%);
                border-right: 1px solid rgba(255, 255, 255, 0.08);
            }
            section[data-testid="stSidebar"] * {
                color: #eef8ef;
            }
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span {
                color: #eef8ef !important;
            }
            section[data-testid="stSidebar"] [data-testid="stTextInputRootElement"] input {
                background: rgba(255, 255, 255, 0.95);
                color: var(--text-900);
                border-radius: 14px;
            }
            .section-header {
                margin-bottom: 1.4rem;
            }
            .section-header h1 {
                margin: 0.15rem 0 0.45rem 0;
                font-size: 2.45rem;
                line-height: 1.08;
                color: var(--text-900);
                font-weight: 800;
            }
            .section-subtitle {
                margin: 0 0 1rem 0;
                font-size: 1.01rem;
                color: var(--text-600);
                line-height: 1.72;
                max-width: 980px;
                text-align: justify;
            }
            .section-eyebrow,
            .card-eyebrow {
                text-transform: uppercase;
                letter-spacing: 0.14em;
                font-size: 0.76rem;
                font-weight: 700;
                color: var(--green-700);
                margin-bottom: 0.35rem;
            }
            .header-meta-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 0.35rem;
                flex-wrap: wrap;
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.42rem 0.85rem;
                border-radius: 999px;
                font-size: 0.84rem;
                font-weight: 700;
                border: 1px solid var(--border);
                background: var(--surface);
                color: var(--text-900);
                box-shadow: var(--shadow);
            }
            .status-badge.active {
                border-color: rgba(27, 94, 32, 0.18);
                background: rgba(232, 245, 233, 0.96);
                color: var(--green-900);
            }
            .status-badge.inactive {
                border-color: rgba(183, 28, 28, 0.16);
                background: rgba(255, 235, 238, 0.96);
                color: #8a1c1c;
            }
            .status-dot {
                width: 0.58rem;
                height: 0.58rem;
                border-radius: 999px;
                display: inline-block;
                flex: 0 0 auto;
            }
            .status-badge.active .status-dot {
                background: #2e7d32;
            }
            .status-badge.inactive .status-dot {
                background: #c62828;
            }
            .subsection-header {
                margin-bottom: 0.65rem;
            }
            .subsection-header h2 {
                margin: 0;
                font-size: 1.55rem;
                line-height: 1.2;
                font-weight: 800;
                color: var(--text-900);
            }
            .subsection-copy,
            .text-block {
                margin: 0 0 0.9rem 0;
                color: var(--text-600);
                line-height: 1.68;
                font-size: 0.98rem;
                text-align: justify;
            }
            .section-subtitle:last-child,
            .subsection-copy:last-child,
            .text-block:last-child {
                margin-bottom: 0;
            }
            .info-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 24px;
                padding: 1.2rem 1.2rem;
                box-shadow: var(--shadow);
                margin-bottom: 1rem;
            }
            .info-card h3 {
                margin: 0 0 0.45rem 0;
                color: var(--text-900);
                font-size: 1.28rem;
                font-weight: 800;
            }
            .info-card p {
                margin: 0;
                color: var(--text-600);
                line-height: 1.66;
                text-align: justify;
            }
            .info-card-light {
                background: var(--surface-soft);
                box-shadow: 0 6px 14px rgba(17, 24, 39, 0.04);
                padding: 0.95rem 1rem;
            }
            .chip-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
                margin-top: 1rem;
            }
            .chip {
                display: inline-flex;
                align-items: center;
                border: 1px solid var(--green-200);
                background: var(--green-100);
                color: var(--green-900);
                border-radius: 999px;
                padding: 0.42rem 0.85rem;
                font-size: 0.85rem;
                font-weight: 700;
            }
            .metric-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1rem 1.1rem;
                box-shadow: var(--shadow);
                margin-bottom: 0.8rem;
                min-height: 118px;
            }
            .metric-label {
                font-size: 0.84rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--text-600);
                font-weight: 700;
                margin-bottom: 0.7rem;
            }
            .metric-value {
                font-size: 2.05rem;
                line-height: 1;
                color: var(--text-900);
                font-weight: 800;
            }
            .metric-emphasis .metric-value,
            .metric-positive .metric-value {
                color: var(--green-900);
            }
            .metric-highlight {
                min-height: 142px;
                padding: 1.05rem 1.15rem;
                text-align: center;
            }
            .metric-highlight .metric-label {
                font-size: 0.72rem;
                letter-spacing: 0.12em;
                margin-bottom: 0.55rem;
                text-align: center;
            }
            .metric-highlight .metric-value {
                font-size: 2.45rem;
                margin-bottom: 0.55rem;
                text-align: center;
            }
            .metric-highlight .metric-caption {
                text-align: center;
            }
            .metric-caption {
                font-size: 0.86rem;
                color: var(--text-600);
                line-height: 1.45;
            }
            .space-24 {
                height: 24px;
            }
            .space-32 {
                height: 32px;
            }
            .capability-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1rem 1.05rem;
                box-shadow: var(--shadow);
                min-height: 156px;
                display: flex;
                flex-direction: column;
                gap: 0.45rem;
                margin-bottom: 0.8rem;
                align-items: center;
                text-align: center;
            }
            .capability-icon {
                font-size: 1.4rem;
                line-height: 1;
                text-align: center;
            }
            .capability-title {
                font-size: 1rem;
                font-weight: 800;
                color: var(--text-900);
                line-height: 1.25;
                text-align: center;
            }
            .capability-body {
                font-size: 0.93rem;
                color: var(--text-600);
                line-height: 1.5;
                text-align: center;
            }
            [data-testid="stTable"] table {
                width: 100%;
                table-layout: fixed;
                border-collapse: collapse;
            }
            [data-testid="stTable"] th,
            [data-testid="stTable"] td {
                white-space: normal !important;
                word-break: break-word;
                vertical-align: top;
                text-align: left;
                padding: 0.72rem 0.7rem;
                line-height: 1.45;
            }
            [data-testid="stTable"] th {
                font-weight: 800;
                color: var(--text-900);
            }
            [data-testid="stTable"] td {
                color: var(--text-600);
            }
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 24px;
                box-shadow: var(--shadow);
                padding: 0.35rem 0.55rem 0.55rem 0.55rem;
                margin-bottom: 1rem;
            }
            div[data-testid="stExpander"] {
                border: 1px solid var(--green-200);
                border-radius: 16px;
                background: var(--green-100);
            }
            .info-panel {
                color: var(--text-700);
                line-height: 1.68;
                font-size: 0.96rem;
                text-align: justify;
            }
            .prediction-card {
                border-radius: 24px;
                padding: 1.2rem 1.2rem;
                border: 1px solid var(--border);
                box-shadow: var(--shadow);
                background: var(--surface);
            }
            .prediction-estable {
                border-left: 8px solid var(--green-500);
            }
            .prediction-critico {
                border-left: 8px solid #2e7d32;
                background: linear-gradient(180deg, #ffffff 0%, #f1f8f2 100%);
            }
            .prediction-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            .prediction-label {
                font-size: 0.8rem;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                color: var(--text-600);
                font-weight: 700;
                margin-bottom: 0.4rem;
            }
            .prediction-class {
                font-size: 1.7rem;
                font-weight: 800;
                color: var(--text-900);
            }
            .prediction-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.8rem;
            }
            .prediction-metric {
                background: var(--surface-soft);
                border-radius: 18px;
                padding: 0.9rem 1rem;
            }
            .prediction-metric span {
                display: block;
                font-size: 0.82rem;
                color: var(--text-600);
                margin-bottom: 0.35rem;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-weight: 700;
            }
            .prediction-metric strong {
                font-size: 1.22rem;
                color: var(--text-900);
            }
            .risk-indicator {
                display: inline-flex;
                align-items: center;
                border-radius: 999px;
                padding: 0.5rem 0.85rem;
                font-size: 0.82rem;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.04em;
            }
            .risk-estable {
                background: var(--green-100);
                color: var(--green-900);
            }
            .risk-critico {
                background: #dff1e1;
                color: var(--green-900);
            }
            .sidebar-brand {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 22px;
                padding: 1rem 1rem;
                margin-bottom: 1rem;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.08);
            }
            .sidebar-brand-title {
                font-size: 1.35rem;
                font-weight: 800;
                margin-bottom: 0.35rem;
                color: #ffffff;
            }
            .sidebar-brand-copy {
                font-size: 0.92rem;
                color: rgba(240, 248, 240, 0.88);
                line-height: 1.5;
            }
            .sidebar-section-title {
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: rgba(240, 248, 240, 0.84);
                font-weight: 800;
                margin-bottom: 0.45rem;
            }
            .stButton button, .stForm button {
                background: linear-gradient(180deg, var(--green-700) 0%, var(--green-900) 100%);
                color: white;
                border: none;
                border-radius: 14px;
                font-weight: 800;
                padding: 0.72rem 1rem;
                box-shadow: 0 14px 28px rgba(27, 94, 32, 0.18);
            }
            .stButton button:hover, .stForm button:hover {
                background: linear-gradient(180deg, var(--green-900) 0%, #144a19 100%);
                color: white;
            }
            [data-testid="stSelectbox"] label,
            [data-testid="stSlider"] label,
            [data-testid="stNumberInput"] label,
            [data-testid="stTextInput"] label {
                color: var(--text-700);
                font-weight: 700;
            }
            [data-testid="stMarkdownContainer"] p code {
                color: var(--green-900);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

    def initialize_client(self) -> None:
        """Inicializa el cliente HTTP usando sesión o variable de entorno.

        Retorna:
            None: Deja disponible el cliente para las vistas del dashboard.
        """
        if "api_base_url" not in st.session_state:
            st.session_state.api_base_url = os.getenv(
                "API_BASE_URL",
                "http://127.0.0.1:8000",
            )
        self.api_client = ApiClient(st.session_state.api_base_url)

    def render_sidebar(self) -> str:
        """Renderiza la barra lateral y devuelve la sección seleccionada.

        Retorna:
            str: Nombre visible de la sección elegida por la persona usuaria.
        """
        st.sidebar.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">Monitoreo de Transacciones y Riesgo de Fraude</div>
                <div class="sidebar-brand-copy">
                    Panel operativo para seguimiento de transacciones sospechosas,
                    riesgo de fraude y decisiones de monitoreo apoyadas por la API.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.sidebar.markdown(
            "<div class='sidebar-section-title'>Conexión a API</div>",
            unsafe_allow_html=True,
        )
        st.sidebar.text_input(
            "Endpoint base",
            key="api_base_url",
            help="Ejemplo: http://127.0.0.1:8000",
        )
        st.sidebar.caption("Documentación interactiva disponible en /docs y /redoc")
        st.sidebar.markdown(
            "<div class='sidebar-section-title'>Navegación</div>",
            unsafe_allow_html=True,
        )

        return st.sidebar.radio(
            "Navegación",
            ["Contexto", "Análisis", "Modelo", "Simulación"],
            label_visibility="collapsed",
        )

    def run(self) -> None:
        """Ejecuta el flujo completo del dashboard.

        Retorna:
            None: Streamlit renderiza la vista correspondiente en pantalla.
        """
        self.configure_page()
        self.inject_styles()
        self.initialize_client()
        section = self.render_sidebar()

        if section == "Contexto":
            home.render(self.api_client)
        elif section == "Análisis":
            eda.render()
        elif section == "Modelo":
            modeling.render()
        else:
            predictor.render(self.api_client)


def main() -> None:
    """Inicia la aplicación Streamlit desde el punto de entrada raíz."""
    FraudMonitoringApp().run()


if __name__ == "__main__":
    main()
