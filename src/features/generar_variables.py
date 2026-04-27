"""Generacion de variables analiticas.

Este modulo contiene funciones simples para crear columnas que ayuden a
interpretar el comportamiento transaccional. Las variables aqui propuestas son
una base para EDA y dashboard; no representan un modelo predictivo.
"""

import numpy as np
import pandas as pd


def crear_variables_temporales(datos: pd.DataFrame) -> pd.DataFrame:
    """Crea variables temporales a partir de la columna `step`.

    En PaySim, `step` representa una unidad de tiempo del simulador. Una
    lectura habitual es tratar cada step como una hora. Esta funcion agrega
    variables simples para analizar ciclos diarios.
    """
    datos_variables = datos.copy()

    if "step" in datos_variables.columns:
        datos_variables["dia_simulado"] = ((datos_variables["step"] - 1) // 24) + 1
        datos_variables["hora_simulada"] = (datos_variables["step"] - 1) % 24

    return datos_variables


def crear_ratios_saldos(datos: pd.DataFrame) -> pd.DataFrame:
    """Crea ratios simples entre monto y saldos disponibles.

    Los ratios ayudan a comparar transacciones de distinto tamano. Se usa
    reemplazo de cero por NaN para evitar divisiones infinitas.
    """
    datos_variables = datos.copy()

    if {"amount", "oldbalanceOrg"}.issubset(datos_variables.columns):
        saldo_origen = datos_variables["oldbalanceOrg"].replace(0, np.nan)
        datos_variables["ratio_monto_saldo_origen"] = (
            datos_variables["amount"] / saldo_origen
        )

    if {"amount", "oldbalanceDest"}.issubset(datos_variables.columns):
        saldo_destino = datos_variables["oldbalanceDest"].replace(0, np.nan)
        datos_variables["ratio_monto_saldo_destino"] = (
            datos_variables["amount"] / saldo_destino
        )

    return datos_variables


def crear_variables_comportamiento_cliente(datos: pd.DataFrame) -> pd.DataFrame:
    """Agrega variables basicas de comportamiento por cliente origen.

    Estas variables resumen frecuencia y monto acumulado por cliente. Son utiles
    para entender si una transaccion ocurre dentro de un patron habitual o si
    pertenece a un cliente con comportamiento poco frecuente.
    """
    datos_variables = datos.copy()

    if {"nameOrig", "amount"}.issubset(datos_variables.columns):
        datos_variables["cantidad_transacciones_cliente"] = datos_variables.groupby(
            "nameOrig", observed=True
        )["amount"].transform("count")
        datos_variables["monto_total_cliente"] = datos_variables.groupby(
            "nameOrig", observed=True
        )["amount"].transform("sum")

    return datos_variables


def generar_variables_base(datos: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta la generacion inicial de variables del proyecto."""
    datos_variables = datos.copy()
    datos_variables = crear_variables_temporales(datos_variables)
    datos_variables = crear_ratios_saldos(datos_variables)
    datos_variables = crear_variables_comportamiento_cliente(datos_variables)

    return datos_variables
