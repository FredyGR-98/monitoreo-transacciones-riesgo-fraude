"""Funciones auxiliares generales.

Este modulo agrupa utilidades pequenas que pueden ser usadas por notebooks,
scripts o dashboard. Deben mantenerse simples para evitar mezclar logica de
negocio con tareas de soporte.
"""

from pathlib import Path
from typing import Union


def obtener_ruta_proyecto() -> Path:
    """Devuelve la ruta raiz del proyecto."""
    return Path(__file__).resolve().parents[2]


def crear_directorio_si_no_existe(ruta: Union[str, Path]) -> Path:
    """Crea un directorio cuando no existe y devuelve su ruta como Path."""
    ruta_directorio = Path(ruta)
    ruta_directorio.mkdir(parents=True, exist_ok=True)

    return ruta_directorio


def construir_ruta(*partes: str) -> Path:
    """Construye una ruta absoluta dentro del proyecto.

    Ejemplo
    -------
    construir_ruta("data", "raw", "archivo.csv")
    """
    return obtener_ruta_proyecto().joinpath(*partes)
