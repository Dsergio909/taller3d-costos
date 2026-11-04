"""Revisa una carpeta de datos antes de usarla (y la arregla si viene de Excel).

Excel en español (Colombia) guarda los CSV con punto y coma, coma decimal («0,3»),
fechas «20/01/2025» y a veces en ANSI o con BOM. El tablero, el SQL y n8n esperan
coma, punto decimal, fechas AAAA-MM-DD y UTF-8. Este script:

- revisa que estén todos los archivos y columnas, los tipos, los rangos y las
  referencias (cada pedido con un canal y un cliente que existan, etc.);
- revisa la marca origen_datos: «ficticio» en datos/, «real» en datos_reales/;
- con --arreglar, deja los archivos en el formato esperado y guarda antes una copia
  de los originales en <carpeta>/_originales/.

Uso:
    python scripts/revisar_datos.py                          # revisa datos/
    python scripts/revisar_datos.py --datos datos_reales --arreglar
"""
from __future__ import annotations

import argparse
import csv
import io
import shutil
import sys
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

TEXTO, NUM, ENTERO, FECHA = "texto", "número", "entero", "fecha"
ESQUEMA = {
    "tarifas": {"parametro": TEXTO, "valor": NUM, "unidad": TEXTO, "aplica_a": TEXTO, "descripcion": TEXTO},
    "canales": {"canal": TEXTO, "comision_pct": NUM, "descripcion": TEXTO},
    "piezas": {"id_pieza": TEXTO, "nombre": TEXTO, "categoria": TEXTO, "tecnologia": TEXTO,
               "material_cantidad": NUM, "horas_placa": NUM, "piezas_por_placa": ENTERO,
               "minutos_acabado": NUM, "precio_lista": NUM},
    "clientes": {"id_cliente": TEXTO, "ciudad": TEXTO},
    "pedidos": {"id_pedido": TEXTO, "fecha": FECHA, "canal": TEXTO, "id_cliente": TEXTO, "estado": TEXTO},
    "pedido_detalle": {"id_pedido": TEXTO, "linea": ENTERO, "id_pieza": TEXTO, "cantidad": ENTERO,
                       "precio_unitario": NUM, "descuento_pct": NUM},
    "gastos": {"id_gasto": TEXTO, "fecha": FECHA, "categoria": TEXTO, "concepto": TEXTO, "valor": NUM},
}
OPCIONALES = {"costo_por_pieza"}  # lo calcula el generador; no hace falta en datos reales
TARIFAS_NECESARIAS = [
    "resina_precio_litro", "resina_soportes_pct", "alcohol_ml_por_placa", "alcohol_precio_litro",
    "guantes_pares_por_placa", "guantes_precio_par", "papel_por_placa", "fep_precio", "fep_placas_vida",
    "resina_potencia_w", "resina_maquina_hora", "resina_tasa_fallas", "filamento_precio_kg", "fdm_purga_pct",
    "fdm_insumos_por_placa", "fdm_potencia_w", "fdm_maquina_hora", "fdm_tasa_fallas", "energia_precio_kwh",
    "mano_obra_hora", "preparacion_min_por_placa", "minutos_acabado_a_medida", "margen_objetivo", "redondeo_precio",
]
FRACCIONES = {"resina_soportes_pct", "resina_tasa_fallas", "fdm_purga_pct", "fdm_tasa_fallas", "margen_objetivo"}


def leer_texto(ruta: Path) -> tuple[str, str]:
    crudo = ruta.read_bytes()
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            return crudo.decode(codificacion), codificacion
        except UnicodeDecodeError:
            continue
    raise ValueError(f"{ruta.name}: no se pudo leer (ni UTF-8 ni ANSI)")


def a_numero(v: str) -> float:
    """Acepta 0.3, 0,3, 150000, 150.000 y 1.234,5."""
    s = v.strip().replace(" ", "").replace("$", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") > 1 or (s.count(".") == 1 and len(s.split(".")[1]) == 3 and len(s.split(".")[0]) <= 3
                              and s.split(".")[0] not in ("0", "-0")):
        # 150.000 (miles con punto). Ojo: 1.234 se lee como mil doscientos treinta y cuatro.
        s = s.replace(".", "")
    return float(s)


def a_fecha(v: str) -> date:
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(v.strip(), formato).date()
        except ValueError:
            continue
    raise ValueError(v)


def bonito(v: float) -> str:
    return str(int(v)) if float(v).is_integer() and abs(v) >= 1 else repr(round(v, 10))


def revisar(carpeta: Path, arreglar: bool = False) -> tuple[list[str], list[str]]:
    """Devuelve (errores, cambios). Sin errores, la carpeta sirve para todo el proyecto."""
    errores, cambios = [], []
    esperado = "real" if carpeta.name == "datos_reales" else "ficticio"
    tablas: dict[str, list[dict]] = {}
    for nombre, columnas in ESQUEMA.items():
        ruta = carpeta / f"{nombre}.csv"
        if not ruta.exists():
            errores.append(f"falta {nombre}.csv")
            continue
        texto, codificacion = leer_texto(ruta)
        primera = texto.splitlines()[0] if texto.strip() else ""
        separador = ";" if primera.count(";") > primera.count(",") else ","
        filas = list(csv.DictReader(io.StringIO(texto), delimiter=separador))
        cab = [c.strip() for c in (filas[0].keys() if filas else primera.split(separador))]
        faltan = [c for c in list(columnas) + ["origen_datos"] if c not in cab]
        if faltan:
            errores.append(f"{nombre}.csv: faltan columnas {faltan}")
            continue
        limpias, malas = [], 0
        for i, fila in enumerate(filas, 2):
            fila = {k.strip(): (v or "").strip() for k, v in fila.items() if k}
            if not any(fila.values()):
                continue  # fila vacía que deja Excel al final
            nueva = dict(fila)
            for col, tipo in columnas.items():
                v = fila[col]
                try:
                    if tipo in (NUM, ENTERO):
                        n = a_numero(v)
                        if tipo == ENTERO and not n.is_integer():
                            raise ValueError
                        nueva[col] = bonito(n)
                    elif tipo == FECHA:
                        nueva[col] = a_fecha(v).isoformat()
                    elif not v and col not in ("descripcion", "concepto", "unidad", "aplica_a", "ciudad", "categoria"):
                        raise ValueError
                except ValueError:
                    malas += 1
                    if malas <= 5:
                        errores.append(f"{nombre}.csv línea {i}: «{v}» no es {tipo} válido en {col}")
            if fila["origen_datos"] != esperado:
                malas += 1
                if malas <= 5:
                    errores.append(f"{nombre}.csv línea {i}: origen_datos es «{fila['origen_datos']}» y en "
                                   f"{carpeta.name}/ debe ser «{esperado}»")
            limpias.append(nueva)
        tablas[nombre] = limpias
        formato_ok = separador == "," and codificacion == "utf-8-sig" and not texto.startswith("﻿") \
            and "\r\n" not in texto
        valores_ok = all(f == {k.strip(): (v or "").strip() for k, v in o.items() if k}
                         for f, o in zip(limpias, filas))
        if not (formato_ok and valores_ok):
            cambios.append(f"{nombre}.csv: separador «{separador}», {codificacion}"
                           + ("" if valores_ok else ", números o fechas en formato de Excel"))
            if arreglar and malas == 0:
                respaldo = carpeta / "_originales"
                respaldo.mkdir(exist_ok=True)
                if not (respaldo / ruta.name).exists():
                    shutil.copy2(ruta, respaldo / ruta.name)
                with open(ruta, "w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(columnas) + ["origen_datos"], extrasaction="ignore",
                                       lineterminator="\n")
                    w.writeheader()
                    w.writerows(limpias)
    if errores:
        return errores, cambios

    # Identificadores repetidos (Python se quedaría con el último sin avisar; Power Query falla)
    for tabla, clave in (("tarifas", "parametro"), ("canales", "canal"), ("piezas", "id_pieza"),
                         ("clientes", "id_cliente"), ("gastos", "id_gasto")):
        vistos, repetidos = set(), set()
        for f in tablas[tabla]:
            (repetidos if f[clave] in vistos else vistos).add(f[clave])
        if repetidos:
            errores.append(f"{tabla}.csv: {clave} repetido: {sorted(repetidos)[:5]}")

    # Reglas del negocio y referencias entre tablas
    t = {f["parametro"]: float(f["valor"]) for f in tablas["tarifas"]}
    for p in TARIFAS_NECESARIAS:
        if p not in t:
            errores.append(f"tarifas.csv: falta el parámetro {p}")
        elif t[p] < 0:
            errores.append(f"tarifas.csv: {p} no puede ser negativo")
    for p in FRACCIONES & set(t):
        if not 0 <= t[p] < 1:
            errores.append(f"tarifas.csv: {p} = {t[p]} debe ser una fracción (0,4 = 40 %), no un porcentaje")
    canales = {c["canal"]: float(c["comision_pct"]) for c in tablas["canales"]}
    for c, v in canales.items():
        if not 0 <= v < 1:
            errores.append(f"canales.csv: la comisión de {c} debe ser una fracción (0,10 = 10 %)")
        elif "margen_objetivo" in t and t["margen_objetivo"] + v >= 1:
            errores.append(f"canales.csv: margen objetivo + comisión de {c} llega al 100 %")
    piezas = {p["id_pieza"]: p for p in tablas["piezas"]}
    for p in tablas["piezas"]:
        if p["tecnologia"] not in ("Resina", "FDM"):
            errores.append(f"piezas.csv: {p['id_pieza']} tiene tecnología «{p['tecnologia']}» (debe ser Resina o FDM)")
        if float(p["piezas_por_placa"]) < 1:
            errores.append(f"piezas.csv: {p['id_pieza']} debe tener al menos 1 pieza por placa")
        if float(p["precio_lista"]) <= 0:
            errores.append(f"piezas.csv: {p['id_pieza']} sin precio de lista")
    clientes = {c["id_cliente"] for c in tablas["clientes"]}
    pedidos = {}
    for p in tablas["pedidos"]:
        if p["canal"] not in canales:
            errores.append(f"pedidos.csv: {p['id_pedido']} tiene un canal que no está en canales.csv ({p['canal']})")
        if p["id_cliente"] not in clientes:
            errores.append(f"pedidos.csv: {p['id_pedido']} tiene un cliente que no está en clientes.csv")
        if p["estado"] not in ("Entregado", "Cancelado", "Devuelto"):
            errores.append(f"pedidos.csv: {p['id_pedido']} tiene estado «{p['estado']}»")
        if p["id_pedido"] in pedidos:
            errores.append(f"pedidos.csv: {p['id_pedido']} está repetido")
        pedidos[p["id_pedido"]] = p
    for d in tablas["pedido_detalle"]:
        if d["id_pedido"] not in pedidos:
            errores.append(f"pedido_detalle.csv: el pedido {d['id_pedido']} no está en pedidos.csv")
        if d["id_pieza"] not in piezas:
            errores.append(f"pedido_detalle.csv: la pieza {d['id_pieza']} no está en piezas.csv")
        if float(d["cantidad"]) < 1 or not 0 <= float(d["descuento_pct"]) < 1:
            errores.append(f"pedido_detalle.csv: {d['id_pedido']} línea {d['linea']} con cantidad o descuento fuera de rango")
    for g in tablas["gastos"]:
        if float(g["valor"]) < 0:
            errores.append(f"gastos.csv: {g['id_gasto']} con valor negativo")
    return errores[:40], cambios


def main() -> None:
    ap = argparse.ArgumentParser(description="Revisa (y arregla) una carpeta de datos")
    ap.add_argument("--datos", default="datos")
    ap.add_argument("--arreglar", action="store_true", help="dejar los CSV en el formato esperado")
    a = ap.parse_args()
    carpeta = Path(a.datos) if Path(a.datos).is_absolute() else RAIZ / a.datos
    errores, cambios = revisar(carpeta, a.arreglar)
    for c in cambios:
        print(("Arreglado: " if a.arreglar and not errores else "Formato de Excel: ") + c)
    if errores:
        print(f"\n{len(errores)} problema(s) en {carpeta.name}/:")
        for e in errores:
            print("  -", e)
        sys.exit(1)
    if cambios and not a.arreglar:
        print("\nCorre de nuevo con --arreglar para dejarlos en el formato que usan el tablero, el SQL y n8n.")
        sys.exit(1)
    print(f"{carpeta.name}/ está bien: sirve para el tablero, el SQL y n8n.")


if __name__ == "__main__":
    main()
