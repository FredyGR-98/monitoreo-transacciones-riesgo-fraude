"""Funciones base para analisis de anomalias.

Este archivo deja preparados puntos de entrada para detectar comportamientos
inusuales. En esta etapa no se implementan modelos complejos; solo se agregan
placeholders y una regla simple de outliers para apoyar el EDA.
"""

import pandas as pd


def detectar_outliers_iqr(datos: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Marca outliers usando la regla del rango intercuartilico.

    Esta es una tecnica descriptiva simple. Sirve como primer acercamiento para
    revisar transacciones con montos o ratios extremadamente altos.
    """
    datos_outliers = datos.copy()

    q1 = datos_outliers[columna].quantile(0.25)
    q3 = datos_outliers[columna].quantile(0.75)
    iqr = q3 - q1

    limite_inferior = q1 - 1.5 * iqr
    limite_superior = q3 + 1.5 * iqr

    datos_outliers[f"outlier_{columna}"] = (
        (datos_outliers[columna] < limite_inferior)
        | (datos_outliers[columna] > limite_superior)
    )

    return datos_outliers


def preparar_clustering_placeholder(datos: pd.DataFrame) -> pd.DataFrame:
    """Placeholder para preparar datos antes de clustering.

    En una etapa posterior se podrian seleccionar variables, escalar valores y
    aplicar un algoritmo como K-Means. Por ahora se devuelve una copia para
    mantener clara la futura responsabilidad de esta funcion.
    """
    return datos.copy()


def detectar_anomalias_placeholder(datos: pd.DataFrame) -> pd.DataFrame:
    """Placeholder para deteccion avanzada de anomalias.

    Esta funcion marca el lugar donde mas adelante podrian evaluarse tecnicas
    como Isolation Forest, Local Outlier Factor u otros metodos. No se implementa
    ningun modelo en esta version base del proyecto.
    """
    datos_anomalias = datos.copy()
    datos_anomalias["anomalia_modelo"] = False

    return datos_anomalias
