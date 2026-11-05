"""Carga los CSV en SQLite y corre las consultas de sql/.

Uso:
    python scripts/cargar_sqlite.py                    # datos ficticios, muestra todo
    python scripts/cargar_sqlite.py --datos datos_reales
    python scripts/cargar_sqlite.py --md docs/resultados_sql.md   # guarda los resultados

Solo usa la librería estándar de Python (sqlite3 y csv): no hay que instalar nada.
"""
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SQL = RAIZ / "sql"
TABLAS = ["tarifas", "canales", "piezas", "clientes", "pedidos", "pedido_detalle", "gastos"]


def conectar(carpeta: Path | str = RAIZ / "datos", archivo: str = ":memory:") -> sqlite3.Connection:
    """Crea el esquema, carga los CSV y deja lista la vista v_costo_pieza."""
    carpeta = Path(carpeta)
    con = sqlite3.connect(archivo)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript((SQL / "00_esquema.sql").read_text(encoding="utf-8"))
    for tabla in TABLAS:
        with open(carpeta / f"{tabla}.csv", encoding="utf-8-sig", newline="") as f:
            lector = csv.reader(f)
            columnas = next(lector)
            marcas = ",".join("?" * len(columnas))
            con.executemany(
                f"INSERT INTO {tabla} ({','.join(columnas)}) VALUES ({marcas})",
                [[None if v == "" else v for v in fila] for fila in lector],
            )
    con.commit()
    # La vista de costos la crea el archivo 01 (la primera parte del script).
    con.executescript(_solo_ddl(SQL / "01_costo_por_pieza.sql"))
    return con


def _solo_ddl(ruta: Path) -> str:
    """Devuelve las sentencias DROP/CREATE de un archivo .sql (sin el SELECT final)."""
    texto = ruta.read_text(encoding="utf-8")
    partes = [p for p in texto.split(";") if p.strip()]
    ddl = [p for p in partes if any(l.strip().upper().startswith(("DROP", "CREATE")) for l in p.splitlines())]
    return ";\n".join(ddl) + ";"


def consulta_final(ruta: Path) -> str:
    """El último SELECT (o WITH ... SELECT) de un archivo .sql."""
    partes = [p for p in ruta.read_text(encoding="utf-8").split(";") if p.strip()]
    return partes[-1]


def correr(con: sqlite3.Connection, ruta: Path) -> tuple[list[str], list[tuple]]:
    cur = con.execute(consulta_final(ruta))
    return [d[0] for d in cur.description], cur.fetchall()


def _md(columnas: list[str], filas: list[tuple]) -> str:
    def fmt(v):
        if isinstance(v, float):
            return f"{v:,.1f}" if abs(v) < 1000 else f"{v:,.0f}"
        return "—" if v is None else str(v)

    lineas = ["| " + " | ".join(columnas) + " |", "|" + "---|" * len(columnas)]
    lineas += ["| " + " | ".join(fmt(v) for v in f) + " |" for f in filas]
    return "\n".join(lineas)


def main() -> None:
    ap = argparse.ArgumentParser(description="Carga los CSV en SQLite y corre las consultas")
    ap.add_argument("--datos", default=str(RAIZ / "datos"))
    ap.add_argument("--md", help="guardar los resultados en este archivo Markdown")
    a = ap.parse_args()
    con = conectar(Path(a.datos))
    salida = ["# Resultados de las consultas SQL", "",
              "Generado con `python scripts/cargar_sqlite.py --md docs/resultados_sql.md`.",
              "Datos: taller ficticio (`datos/`). Ninguna cifra es de un taller real.", ""]
    for ruta in sorted((q for q in SQL.glob("[0-9][0-9]_*.sql") if not q.name.startswith("00"))):
        columnas, filas = correr(con, ruta)
        titulo = ruta.read_text(encoding="utf-8").splitlines()[0].lstrip("- ").strip()
        print(f"\n== {titulo} ({len(filas)} filas)")
        for f in filas[:20]:
            print("  ", f)
        salida += [f"## {titulo}", f"`sql/{ruta.name}`", "", _md(columnas, filas), ""]
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text("\n".join(salida) + "\n", encoding="utf-8", newline="\n")
        print(f"\nGuardado en {a.md}")


if __name__ == "__main__":
    main()
