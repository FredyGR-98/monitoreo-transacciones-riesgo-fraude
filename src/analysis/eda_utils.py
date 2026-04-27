"""Utilidades para analisis exploratorio de datos.

Las funciones de este modulo entregan tablas resumidas para entender el dataset
sin repetir codigo en cada notebook. El foco es EDA simple, claro y facil de
explicar en un portafolio.
"""

import pandas as pd


def resumen_datos(datos: pd.DataFrame) -> pd.DataFrame:
    """Resume tipo de dato, nulos y valores unicos por columna.

    Este resumen es una primera fotografia de calidad y estructura del dataset.
    Ayuda a detectar columnas con problemas antes de entrar al analisis visual.
    """
    resumen = pd.DataFrame(
        {
            "tipo_dato": datos.dtypes.astype(str),
            "nulos": datos.isna().sum(),
            "porcentaje_nulos": (datos.isna().mean() * 100).round(2),
            "valores_unicos": datos.nunique(dropna=False),
        }
    )

    return resumen.sort_values("porcentaje_nulos", ascending=False)


def resumen_general(datos: pd.DataFrame) -> pd.DataFrame:
    """Genera estadisticas descriptivas para variables numericas."""
    return datos.describe().T


def conteo_por_categoria(datos: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Cuenta registros y porcentajes para una columna categorica."""
    conteos = datos[columna].value_counts(dropna=False)
    porcentajes = datos[columna].value_counts(normalize=True, dropna=False) * 100

    resumen = pd.DataFrame(
        {
            "conteo": conteos,
            "porcentaje": porcentajes.round(2),
        }
    )

    return resumen


def distribucion_variable(datos: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Resume la distribucion de una variable categorica o discreta.

    Devuelve conteos y porcentajes. Es util para variables como `type`,
    `isFraud` o cualquier segmento que se quiera revisar rapidamente.
    """
    return conteo_por_categoria(datos, columna)


def agrupar_por_fraude(datos: pd.DataFrame, columna_valor: str) -> pd.DataFrame:
    """Compara una variable numerica entre transacciones fraudulentes y normales."""
    if "isFraud" not in datos.columns:
        raise KeyError("La columna `isFraud` no existe en el DataFrame.")

    return datos.groupby("isFraud")[columna_valor].agg(
        conteo="count",
        promedio="mean",
        mediana="median",
        minimo="min",
        maximo="max",
    )


def comparar_fraude_vs_no_fraude(
    datos: pd.DataFrame,
    columna_valor: str,
    columna_fraude: str = "isFraud",
) -> pd.DataFrame:
    """Compara una variable numerica entre fraude y no fraude.

    La funcion resume conteo, promedio, mediana y rango para facilitar una
    interpretacion rapida desde negocio.
    """
    if columna_fraude not in datos.columns:
        raise KeyError(f"La columna `{columna_fraude}` no existe en el DataFrame.")

    if columna_valor not in datos.columns:
        raise KeyError(f"La columna `{columna_valor}` no existe en el DataFrame.")

    resumen = datos.groupby(columna_fraude)[columna_valor].agg(
        conteo="count",
        promedio="mean",
        mediana="median",
        minimo="min",
        maximo="max",
    )

    return resumen.round(2)


def tasa_fraude_por_grupo(datos: pd.DataFrame, columna_grupo: str) -> pd.DataFrame:
    """Calcula la tasa de fraude por grupo.

    Esta funcion es util para comparar tipos de transaccion, horas simuladas u
    otros segmentos relevantes desde negocio.
    """
    if "isFraud" not in datos.columns:
        raise KeyError("La columna `isFraud` no existe en el DataFrame.")

    resumen = datos.groupby(columna_grupo, observed=True)["isFraud"].agg(
        total_transacciones="count",
        fraudes="sum",
    )
    resumen["tasa_fraude"] = (
        resumen["fraudes"] / resumen["total_transacciones"] * 100
    ).round(4)

    return resumen.sort_values("tasa_fraude", ascending=False)
