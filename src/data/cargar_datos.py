"""Funciones para cargar datos del proyecto.

Este archivo centraliza la lectura de archivos CSV desde las carpetas del
proyecto. La idea es evitar rutas absolutas en notebooks y mantener una forma
unica, clara y reutilizable de cargar el dataset PaySim.
"""

from pathlib import Path
from typing import List, Optional

import pandas as pd


RUTA_PROYECTO = Path(__file__).resolve().parents[2]
RUTA_DATA = RUTA_PROYECTO / "data"
RUTA_RAW = RUTA_DATA / "raw"


def validar_archivo_existe(ruta_archivo: Path) -> None:
    """Valida que el archivo exista antes de intentar cargarlo.

    Parameters
    ----------
    ruta_archivo:
        Ruta completa del archivo que se quiere leer.

    Raises
    ------
    FileNotFoundError
        Se lanza cuando el archivo no existe en la ruta indicada.
    """
    if not ruta_archivo.exists():
        raise FileNotFoundError(
            f"No se encontro el archivo: {ruta_archivo}. "
            "Verifica que el dataset este dentro de data/raw."
        )


def listar_archivos_csv(carpeta: str = "raw") -> List[Path]:
    """Lista archivos CSV disponibles dentro de una carpeta de `data`.

    Parameters
    ----------
    carpeta:
        Subcarpeta dentro de `data`. Por defecto se usa `raw`, donde deberia
        vivir el archivo original de PaySim.

    Returns
    -------
    list[pathlib.Path]
        Lista ordenada de archivos CSV encontrados.
    """
    ruta_carpeta = RUTA_DATA / carpeta

    if not ruta_carpeta.exists():
        return []

    return sorted(ruta_carpeta.glob("*.csv"))


def cargar_csv(
    nombre_archivo: str,
    carpeta: str = "raw",
    separador: str = ",",
    n_filas: Optional[int] = None,
    columnas: Optional[List[str]] = None,
    muestra: Optional[int] = None,
    random_state: int = 42,
) -> pd.DataFrame:
    """Carga un archivo CSV desde una carpeta del proyecto.

    Esta funcion deja preparada una lectura simple y reutilizable para
    notebooks, scripts y dashboard. Incluye opciones basicas para trabajar con
    archivos grandes sin cargar necesariamente todo el dataset en memoria.

    Parameters
    ----------
    nombre_archivo:
        Nombre del archivo CSV que se quiere cargar.
    carpeta:
        Subcarpeta dentro de `data`. Por defecto, `raw`.
    separador:
        Caracter usado para separar columnas. PaySim normalmente usa coma.
    n_filas:
        Cantidad maxima de filas a leer desde el archivo. Es util para una
        primera exploracion rapida.
    columnas:
        Lista opcional de columnas a cargar. Ayuda a reducir memoria cuando se
        trabaja con archivos grandes.
    muestra:
        Cantidad opcional de filas a muestrear despues de la carga. Si se usa
        junto con `n_filas`, el muestreo se aplica sobre esas primeras filas.
    random_state:
        Semilla para que el muestreo sea reproducible.

    Returns
    -------
    pandas.DataFrame
        Tabla con los datos cargados.
    """
    ruta_archivo = RUTA_DATA / carpeta / nombre_archivo
    validar_archivo_existe(ruta_archivo)

    datos = pd.read_csv(
        ruta_archivo,
        sep=separador,
        nrows=n_filas,
        usecols=columnas,
    )

    if datos.empty:
        raise ValueError("El archivo fue cargado, pero no contiene registros.")

    if muestra is not None and muestra < len(datos):
        datos = datos.sample(n=muestra, random_state=random_state)

    return datos


def cargar_dataset(nombre_archivo: str, separador: str = ",") -> pd.DataFrame:
    """Carga el dataset PaySim desde `data/raw`.

    Esta funcion se mantiene como alias simple para notebooks anteriores. Para
    nuevas exploraciones se recomienda usar `cargar_csv`, porque permite leer
    parcialmente archivos grandes.
    """
    return cargar_csv(nombre_archivo=nombre_archivo, separador=separador)


def obtener_resumen_carga(datos: pd.DataFrame) -> dict:
    """Entrega un resumen breve de la carga de datos.

    Este resumen sirve para validar rapidamente el tamano del dataset y
    confirmar que las columnas esperadas fueron leidas correctamente.
    """
    return {
        "filas": datos.shape[0],
        "columnas": datos.shape[1],
        "nombres_columnas": list(datos.columns),
    }
