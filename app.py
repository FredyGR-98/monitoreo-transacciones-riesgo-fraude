"""Punto de entrada raíz para ejecutar el dashboard en Streamlit.

Propósito:
    Permite iniciar la interfaz con `streamlit run app.py` desde la raíz del
    repositorio, manteniendo intacta la implementación principal ubicada en
    `dashboard/app.py`.
"""

from dashboard.app import main


if __name__ == "__main__":
    main()
