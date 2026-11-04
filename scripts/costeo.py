"""Costeo de una pieza impresa en 3D (resina o FDM).

Este archivo es la fórmula de referencia del proyecto. Las mismas cuentas están en:
- sql/01_costo_por_pieza.sql (SQLite),
- flujos/costeo.js (el nodo de código del flujo de n8n),
- el modelo de Power BI (Power Query, consulta «CostoPieza»).
Las pruebas comprueban que las cuatro den lo mismo.

La idea: una placa de impresión se reparte entre las piezas que caben en ella.
Lo que cuesta por placa (lavado, guantes, luz, máquina, preparar) se divide por
las piezas de la placa. Lo que cuesta por pieza (material y acabado) va directo.
Al final se suma lo que se pierde por placas que salen mal (tasa de fallas).
"""
from __future__ import annotations

import csv
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

COMPONENTES = ["material", "insumos", "energia", "maquina", "mano_obra", "fallas"]


def leer_tarifas(carpeta: Path) -> dict[str, float]:
    """Lee tarifas.csv y devuelve {parametro: valor}."""
    with open(Path(carpeta) / "tarifas.csv", encoding="utf-8-sig", newline="") as f:
        return {fila["parametro"]: float(fila["valor"]) for fila in csv.DictReader(f)}


def leer_canales(carpeta: Path) -> dict[str, float]:
    """Lee canales.csv y devuelve {canal: comision (fracción)}."""
    with open(Path(carpeta) / "canales.csv", encoding="utf-8-sig", newline="") as f:
        return {fila["canal"]: float(fila["comision_pct"]) for fila in csv.DictReader(f)}


def leer_piezas(carpeta: Path) -> list[dict]:
    with open(Path(carpeta) / "piezas.csv", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def costo_unitario(pieza: dict, t: dict[str, float]) -> dict[str, float]:
    """Costo de UNA pieza, por componente, en pesos (sin redondear).

    pieza necesita: tecnologia ("Resina" o "FDM"), material_cantidad (ml o g),
    horas_placa, piezas_por_placa y minutos_acabado.
    """
    tec = pieza["tecnologia"]
    cantidad = float(pieza["material_cantidad"])
    horas = float(pieza["horas_placa"])
    ppp = float(pieza["piezas_por_placa"])
    acabado_min = float(pieza["minutos_acabado"])
    if ppp <= 0 or cantidad < 0 or horas < 0 or acabado_min < 0:
        raise ValueError("Datos de la pieza fuera de rango")

    if tec == "Resina":
        material = cantidad * (1 + t["resina_soportes_pct"]) * t["resina_precio_litro"] / 1000
        insumos_placa = (
            t["alcohol_ml_por_placa"] * t["alcohol_precio_litro"] / 1000
            + t["guantes_pares_por_placa"] * t["guantes_precio_par"]
            + t["papel_por_placa"]
            + t["fep_precio"] / t["fep_placas_vida"]
        )
        potencia_w, maquina_hora, tasa = t["resina_potencia_w"], t["resina_maquina_hora"], t["resina_tasa_fallas"]
    elif tec == "FDM":
        material = cantidad * (1 + t["fdm_purga_pct"]) * t["filamento_precio_kg"] / 1000
        insumos_placa = t["fdm_insumos_por_placa"]
        potencia_w, maquina_hora, tasa = t["fdm_potencia_w"], t["fdm_maquina_hora"], t["fdm_tasa_fallas"]
    else:
        raise ValueError(f"Tecnología desconocida: {tec}")

    insumos = insumos_placa / ppp
    energia = horas * potencia_w / 1000 * t["energia_precio_kwh"] / ppp
    maquina = horas * maquina_hora / ppp
    mano_obra = (t["preparacion_min_por_placa"] / ppp + acabado_min) / 60 * t["mano_obra_hora"]
    base = material + insumos + energia + maquina + mano_obra
    fallas = base * tasa
    partes = {
        "material": material,
        "insumos": insumos,
        "energia": energia,
        "maquina": maquina,
        "mano_obra": mano_obra,
        "fallas": fallas,
    }
    partes["costo_total"] = sum(partes[c] for c in COMPONENTES)
    return partes


def precio_sugerido(costo: float, t: dict[str, float], comision: float = 0.0) -> float:
    """Precio para ganar el margen objetivo después de la comisión del canal.

    precio = costo / (1 - margen - comisión), redondeado hacia arriba al múltiplo
    de «redondeo_precio» (por ejemplo, de 500 en 500 pesos).
    """
    divisor = 1 - t["margen_objetivo"] - comision
    if divisor <= 0:
        raise ValueError("Margen más comisión no pueden sumar 100 % o más")
    paso = t["redondeo_precio"]
    # round(…, 9) quita el ruido de coma flotante antes del techo (igual en JS y SQL).
    return math.ceil(round(costo / divisor / paso, 9)) * paso


def cotizar(pieza: dict, cantidad: int, canal: str, t: dict[str, float], canales: dict[str, float]) -> dict:
    """Cotización completa de un pedido: costo, precio y margen."""
    if cantidad < 1 or cantidad != int(cantidad):
        raise ValueError("La cantidad debe ser un entero mayor que cero")
    if canal not in canales:
        raise ValueError(f"Canal desconocido: {canal}")
    c = costo_unitario(pieza, t)
    comision = canales[canal]
    precio_u = precio_sugerido(c["costo_total"], t, comision)
    total = precio_u * cantidad
    costo_total = c["costo_total"] * cantidad
    comision_valor = total * comision
    return {
        "costo_unitario": c["costo_total"],
        "precio_unitario": precio_u,
        "cantidad": int(cantidad),
        "total": total,
        "comision": comision_valor,
        "ganancia": total - costo_total - comision_valor,
        "margen_pct": (total - costo_total - comision_valor) / total,
    }


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Muestra el costo por pieza del catálogo")
    p.add_argument("--datos", default=str(RAIZ / "datos"), help="carpeta con los CSV (datos o datos_reales)")
    a = p.parse_args()
    tarifas = leer_tarifas(Path(a.datos))
    for pz in leer_piezas(Path(a.datos)):
        c = costo_unitario(pz, tarifas)
        print(f"{pz['id_pieza']:4} {pz['nombre']:<28} {pz['tecnologia']:<6} costo {c['costo_total']:>9,.0f}  precio {float(pz['precio_lista']):>9,.0f}")
