"""Graficos reutilizables para el proyecto.

Este modulo contiene funciones simples basadas en Matplotlib y Seaborn. La
idea es mantener un estilo consistente entre notebooks y dashboard.
"""

from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes


def configurar_estilo() -> None:
    """Configura un estilo visual limpio para todos los graficos."""
    sns.set_theme(style="whitegrid", palette="deep")


def graficar_histograma(
    datos: pd.DataFrame,
    columna: str,
    bins: int = 50,
    titulo: Optional[str] = None,
) -> Axes:
    """Crea un histograma para analizar la distribucion de una variable."""
    configurar_estilo()
    ax = sns.histplot(data=datos, x=columna, bins=bins, kde=False)
    ax.set_title(titulo or f"Distribucion de {columna}")
    ax.set_xlabel(columna)
    ax.set_ylabel("Frecuencia")

    return ax


def graficar_boxplot(
    datos: pd.DataFrame,
    columna_x: str,
    columna_y: str,
    titulo: Optional[str] = None,
) -> Axes:
    """Crea un boxplot para comparar una variable numerica entre grupos."""
    configurar_estilo()
    ax = sns.boxplot(data=datos, x=columna_x, y=columna_y)
    ax.set_title(titulo or f"{columna_y} por {columna_x}")
    ax.set_xlabel(columna_x)
    ax.set_ylabel(columna_y)

    return ax


def graficar_scatterplot(
    datos: pd.DataFrame,
    columna_x: str,
    columna_y: str,
    color: Optional[str] = None,
    titulo: Optional[str] = None,
) -> Axes:
    """Crea un scatterplot para revisar relaciones entre dos variables."""
    configurar_estilo()
    ax = sns.scatterplot(data=datos, x=columna_x, y=columna_y, hue=color)
    ax.set_title(titulo or f"Relacion entre {columna_x} y {columna_y}")
    ax.set_xlabel(columna_x)
    ax.set_ylabel(columna_y)

    return ax
