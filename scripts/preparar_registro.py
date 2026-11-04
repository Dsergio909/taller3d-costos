"""Crea registro/ con los encabezados de los CSV que llena el flujo de n8n.

registro/ está en .gitignore: ahí quedan nombres de clientes y decisiones.
"""
from __future__ import annotations

import csv
from pathlib import Path

from armar_flujo import COLUMNAS_ERRORES, COLUMNAS_PENDIENTES, COLUMNAS_REGISTRO

RAIZ = Path(__file__).resolve().parent.parent


def preparar(carpeta: Path = RAIZ / "registro") -> list[Path]:
    carpeta.mkdir(exist_ok=True)
    creados = []
    for nombre, columnas in (("cotizaciones.csv", COLUMNAS_REGISTRO), ("pendientes.csv", COLUMNAS_PENDIENTES),
                             ("errores.csv", COLUMNAS_ERRORES)):
        ruta = carpeta / nombre
        if not ruta.exists():
            with open(ruta, "w", encoding="utf-8", newline="") as f:
                csv.writer(f, lineterminator="\n").writerow(columnas)
            creados.append(ruta)
    return creados


if __name__ == "__main__":
    for r in preparar():
        print("Creado", r.relative_to(RAIZ))
