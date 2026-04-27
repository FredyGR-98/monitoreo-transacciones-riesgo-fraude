"""Funciones base para limpieza de datos.

El objetivo de este modulo es concentrar reglas simples de limpieza para que
los notebooks se mantengan claros y enfocados en el analisis. En esta etapa no
se aplican transformaciones agresivas; solo se dejan funciones reutilizables.
"""

import pandas as pd


def revisar_nulos(datos: pd.DataFrame) -> pd.DataFrame:
    """Calcula la cantidad y porcentaje de nulos por columna.

    Returns
    -------
    pandas.DataFrame
        Tabla ordenada con conteo y porcentaje de valores nulos.
    """
    total_nulos = datos.isna().sum()
    porcentaje_nulos = (total_nulos / len(datos)) * 100

    resumen = pd.DataFrame(
        {
            "nulos": total_nulos,
            "porcentaje_nulos": porcentaje_nulos.round(2),
        }
    )

    return resumen.sort_values("porcentaje_nulos", ascending=False)


def eliminar_duplicados(datos: pd.DataFrame) -> pd.DataFrame:
    """Elimina filas duplicadas y devuelve una copia limpia.

    PaySim normalmente no deberia traer duplicados exactos, pero esta funcion
    ayuda a documentar una validacion basica de calidad de datos.
    """
    return datos.drop_duplicates().copy()


def convertir_tipos_basicos(datos: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas conocidas de PaySim a tipos mas adecuados.

    La funcion usa conversiones conservadoras. Si una columna no existe, no se
    genera error; esto permite reutilizarla con muestras o versiones reducidas.
    """
    datos_limpios = datos.copy()

    columnas_categoricas = ["type", "nameOrig", "nameDest"]
    columnas_enteras = ["step", "isFraud", "isFlaggedFraud"]

    for columna in columnas_categoricas:
        if columna in datos_limpios.columns:
            datos_limpios[columna] = datos_limpios[columna].astype("category")

    for columna in columnas_enteras:
        if columna in datos_limpios.columns:
            datos_limpios[columna] = pd.to_numeric(
                datos_limpios[columna], errors="coerce"
            ).astype("Int64")

    return datos_limpios


def limpieza_general(datos: pd.DataFrame) -> pd.DataFrame:
    """Aplica una limpieza inicial simple y trazable.

    Esta funcion agrupa pasos basicos que suelen ejecutarse al comienzo del
    proyecto: copiar datos, eliminar duplicados y ajustar tipos conocidos.
    """
    datos_limpios = datos.copy()
    datos_limpios = eliminar_duplicados(datos_limpios)
    datos_limpios = convertir_tipos_basicos(datos_limpios)

    return datos_limpios
