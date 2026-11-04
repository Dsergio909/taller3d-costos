"""Arma un taller de impresión 3D INVENTADO para la plantilla pública.

Todo lo que sale de aquí es ficticio: tarifas redondas, catálogo, clientes,
pedidos y gastos. Ninguna cifra es de un taller real. Cada fila de cada CSV
lleva la columna origen_datos = "ficticio", y una prueba de GitHub falla si
aparece un CSV sin esa marca.

Uso:
    python scripts/generar_datos_ficticios.py            # escribe en datos/
    python scripts/generar_datos_ficticios.py --salida otra_carpeta

Siempre da los mismos datos (semilla fija), para que las pruebas puedan
comprobar totales conocidos.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from costeo import costo_unitario  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
MARCA = "ficticio"
SEMILLA = 2025
ANIO = 2025

# ---------------------------------------------------------------------------
# Tarifas inventadas y redondas. NO son las de ningún taller real.
# ---------------------------------------------------------------------------
TARIFAS = [
    # parametro, valor, unidad, aplica_a, descripcion
    ("resina_precio_litro", 150000, "COP/L", "Resina", "Precio de la resina estándar"),
    ("resina_soportes_pct", 0.30, "fracción", "Resina", "Resina extra que se va en soportes y base"),
    ("alcohol_ml_por_placa", 150, "ml", "Resina", "Alcohol isopropílico que se gasta lavando una placa"),
    ("alcohol_precio_litro", 40000, "COP/L", "Resina", "Precio del alcohol isopropílico"),
    ("guantes_pares_por_placa", 2, "pares", "Resina", "Guantes de nitrilo por placa"),
    ("guantes_precio_par", 1000, "COP/par", "Resina", "Precio de un par de guantes"),
    ("papel_por_placa", 1000, "COP", "Resina", "Toallas de papel y filtros por placa"),
    ("fep_precio", 60000, "COP", "Resina", "Film FEP de repuesto de la cuba"),
    ("fep_placas_vida", 60, "placas", "Resina", "Placas que dura un film FEP"),
    ("resina_potencia_w", 100, "W", "Resina", "Consumo promedio de la impresora de resina"),
    ("resina_maquina_hora", 400, "COP/h", "Resina", "Desgaste y pago de la impresora por hora de uso"),
    ("resina_tasa_fallas", 0.10, "fracción", "Resina", "De cada 10 placas, 1 sale mal"),
    ("filamento_precio_kg", 100000, "COP/kg", "FDM", "Precio del filamento PLA"),
    ("fdm_purga_pct", 0.10, "fracción", "FDM", "Filamento que se va en purga y torre al cambiar color"),
    ("fdm_insumos_por_placa", 500, "COP", "FDM", "Pegante de placa y limpieza"),
    ("fdm_potencia_w", 150, "W", "FDM", "Consumo promedio de la impresora FDM"),
    ("fdm_maquina_hora", 500, "COP/h", "FDM", "Desgaste (boquilla, placa) y pago de la impresora por hora"),
    ("fdm_tasa_fallas", 0.05, "fracción", "FDM", "De cada 20 placas, 1 sale mal"),
    ("energia_precio_kwh", 1000, "COP/kWh", "Ambas", "Tarifa de la luz"),
    ("mano_obra_hora", 15000, "COP/h", "Ambas", "Valor de una hora de trabajo"),
    ("preparacion_min_por_placa", 15, "min", "Ambas", "Rebanar, cargar y retirar una placa"),
    ("minutos_acabado_a_medida", 30, "min", "Ambas", "Acabado de una pieza a medida (cotizador de n8n)"),
    ("margen_objetivo", 0.40, "fracción", "Ambas", "Margen que se quiere ganar sobre el precio"),
    ("redondeo_precio", 500, "COP", "Ambas", "El precio sugerido se redondea hacia arriba a este múltiplo"),
]

CANALES = [
    # canal, comision_pct, descripcion
    ("TikTok", 0.10, "Comisión de la tienda de la plataforma"),
    ("Instagram", 0.03, "Cobro del link de pago"),
    ("WhatsApp", 0.00, "Pago por transferencia"),
]

# Catálogo inventado. material_cantidad: ml (resina) o gramos (FDM) por pieza.
PIEZAS = [
    # id, nombre, categoria, tecnologia, material, horas_placa, piezas_placa, min_acabado, precio_lista
    ("R01", "Ficha de juego", "Juegos", "Resina", 1.2, 1.5, 40, 3, 6000),
    ("R02", "Aretes (par)", "Accesorios", "Resina", 1.0, 1.0, 30, 5, 15000),
    ("R03", "Miniatura 32 mm", "Figuras", "Resina", 6, 2.5, 12, 10, 25000),
    ("R04", "Figura 10 cm", "Figuras", "Resina", 45, 5, 2, 40, 90000),
    ("R05", "Busto 12 cm", "Figuras", "Resina", 80, 6, 1, 60, 120000),
    ("R06", "Dije", "Accesorios", "Resina", 2, 1.2, 25, 5, 12000),
    ("R07", "Anillo", "Accesorios", "Resina", 1.5, 1.0, 20, 5, 18000),
    ("R08", "Llavero detallado", "Llaveros", "Resina", 4, 1.5, 15, 8, 14000),
    ("F01", "Llavero", "Llaveros", "FDM", 6, 1.5, 12, 2, 8000),
    ("F02", "Maceta pequeña", "Hogar", "FDM", 60, 3, 2, 5, 25000),
    ("F03", "Soporte de celular", "Escritorio", "FDM", 35, 2, 2, 3, 18000),
    ("F04", "Organizador de escritorio", "Escritorio", "FDM", 150, 6, 1, 5, 45000),
    ("F05", "Lámpara (base)", "Hogar", "FDM", 120, 7, 1, 20, 70000),
    ("F06", "Figura multicolor", "Figuras", "FDM", 50, 4, 1, 10, 30000),
    ("F07", "Imán de nevera", "Hogar", "FDM", 8, 2, 16, 2, 6000),
    ("F08", "Repuesto a medida", "A medida", "FDM", 25, 1.5, 1, 30, 20000),
    ("F09", "Caja con tapa", "Hogar", "FDM", 90, 5, 1, 5, 35000),
]

CIUDADES = [("Bogotá", 55), ("Medellín", 15), ("Cali", 10), ("Barranquilla", 7), ("Bucaramanga", 6), ("Otra", 7)]

# Qué se vende más en cada canal (peso relativo por pieza).
PREFERENCIA = {
    "TikTok": {"R01": 6, "R02": 8, "R06": 6, "F01": 9, "F07": 7, "R08": 5, "R03": 4, "F06": 4, "F03": 3},
    "Instagram": {"R02": 5, "R03": 6, "R04": 4, "R07": 5, "F02": 5, "F05": 3, "F06": 4, "R06": 3, "F09": 3, "F03": 3},
    "WhatsApp": {"R04": 4, "R05": 3, "F04": 4, "F05": 4, "F08": 6, "F09": 3, "R01": 3, "F02": 2, "R03": 2},
}

# Pedidos por mes (base) y temporada: mayo (madres), octubre (Halloween), diciembre.
TEMPORADA = {1: 0.8, 2: 0.85, 3: 0.9, 4: 0.95, 5: 1.25, 6: 1.0, 7: 0.95, 8: 1.0, 9: 1.0, 10: 1.2, 11: 1.3, 12: 1.7}
PEDIDOS_BASE = 38


def escribir(carpeta: Path, nombre: str, columnas: list[str], filas: list[list]) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    with open(carpeta / nombre, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(columnas + ["origen_datos"])
        for fila in filas:
            # 150000.0 se escribe 150000; 0.3 queda 0.3
            limpia = [int(v) if isinstance(v, float) and v.is_integer() and abs(v) >= 1 else v for v in fila]
            w.writerow(limpia + [MARCA])


def elegir(rng: random.Random, pesos: dict) -> str:
    claves = list(pesos)
    return rng.choices(claves, weights=[pesos[k] for k in claves])[0]


def mezcla_canales(mes: int) -> dict[str, float]:
    """TikTok crece en el año, Instagram baja, WhatsApp se mantiene."""
    avance = (mes - 1) / 11
    tiktok = 0.25 + 0.25 * avance
    whatsapp = 0.25
    return {"TikTok": tiktok, "Instagram": 1 - tiktok - whatsapp, "WhatsApp": whatsapp}


def generar(salida: Path) -> dict[str, int]:
    rng = random.Random(SEMILLA)

    escribir(salida, "tarifas.csv", ["parametro", "valor", "unidad", "aplica_a", "descripcion"], [list(t) for t in TARIFAS])
    escribir(salida, "canales.csv", ["canal", "comision_pct", "descripcion"], [list(c) for c in CANALES])
    escribir(
        salida,
        "piezas.csv",
        ["id_pieza", "nombre", "categoria", "tecnologia", "material_cantidad", "horas_placa",
         "piezas_por_placa", "minutos_acabado", "precio_lista"],
        [list(p) for p in PIEZAS],
    )

    # Clientes inventados: solo un código y una ciudad. Sin nombres ni teléfonos.
    clientes = []
    for i in range(1, 321):
        ciudad = rng.choices([c for c, _ in CIUDADES], weights=[w for _, w in CIUDADES])[0]
        clientes.append((f"CLI-{i:03d}", ciudad))
    escribir(salida, "clientes.csv", ["id_cliente", "ciudad"], clientes)

    precio = {p[0]: p[8] for p in PIEZAS}
    pedidos, detalle = [], []
    # Los clientes de WhatsApp vuelven más: se eligen de un grupo pequeño.
    grupo_whatsapp = [c[0] for c in clientes[:70]]
    n = 0
    for mes in range(1, 13):
        cuantos = round(PEDIDOS_BASE * TEMPORADA[mes] * (1 + 0.02 * (mes - 1)))
        dias_mes = (date(ANIO + (mes == 12), mes % 12 + 1, 1) - date(ANIO, mes, 1)).days
        mezcla = mezcla_canales(mes)
        for _ in range(cuantos):
            n += 1
            id_pedido = f"PED-{n:04d}"
            fecha = date(ANIO, mes, 1) + timedelta(days=rng.randrange(dias_mes))
            canal = elegir(rng, mezcla)
            if canal == "WhatsApp" and rng.random() < 0.6:
                id_cliente = rng.choice(grupo_whatsapp)
            else:
                id_cliente = rng.choice(clientes)[0]
            r = rng.random()
            estado = "Entregado" if r < 0.94 else ("Cancelado" if r < 0.98 else "Devuelto")
            pedidos.append((id_pedido, fecha.isoformat(), canal, id_cliente, estado))

            lineas = rng.choices([1, 2, 3], weights=[70, 22, 8])[0]
            usadas = set()
            for linea in range(1, lineas + 1):
                pieza = elegir(rng, PREFERENCIA[canal])
                if pieza in usadas:
                    continue
                usadas.add(pieza)
                if pieza == "R01":
                    cantidad = rng.choice([4, 8, 16, 16])
                elif pieza == "F07":
                    cantidad = rng.choice([2, 4, 6])
                else:
                    cantidad = rng.choices([1, 2, 3], weights=[75, 18, 7])[0]
                descuento = 0.0
                if canal == "TikTok" and mes in (11, 12) and rng.random() < 0.5:
                    descuento = 0.15  # promociones de fin de año
                elif canal == "WhatsApp" and id_cliente in grupo_whatsapp and rng.random() < 0.3:
                    descuento = 0.10  # cliente que vuelve
                detalle.append((id_pedido, len(usadas), pieza, cantidad, precio[pieza], descuento))
    escribir(salida, "pedidos.csv", ["id_pedido", "fecha", "canal", "id_cliente", "estado"], pedidos)
    escribir(
        salida, "pedido_detalle.csv",
        ["id_pedido", "linea", "id_pieza", "cantidad", "precio_unitario", "descuento_pct"], detalle,
    )

    # Gastos de caja por mes, a partir de lo que se produjo.
    tarifas = {t[0]: float(t[1]) for t in TARIFAS}
    piezas = {p[0]: dict(zip(["id_pieza", "nombre", "categoria", "tecnologia", "material_cantidad", "horas_placa",
                              "piezas_por_placa", "minutos_acabado", "precio_lista"], p)) for p in PIEZAS}
    estado_pedido = {p[0]: p[4] for p in pedidos}
    mes_pedido = {p[0]: int(p[1][5:7]) for p in pedidos}
    gastos = []
    film_acumulado = 0.0
    for mes in range(1, 13):
        ml = g = placas_resina = horas_resina = horas_fdm = 0.0
        ordenes = 0
        for (idp, _l, pz, cant, _pr, _d) in detalle:
            if mes_pedido[idp] != mes or estado_pedido[idp] == "Cancelado":
                continue
            p = piezas[pz]
            fraccion = cant / p["piezas_por_placa"]
            if p["tecnologia"] == "Resina":
                ml += cant * p["material_cantidad"] * (1 + tarifas["resina_soportes_pct"])
                placas_resina += fraccion
                horas_resina += fraccion * p["horas_placa"]
            else:
                g += cant * p["material_cantidad"] * (1 + tarifas["fdm_purga_pct"])
                horas_fdm += fraccion * p["horas_placa"]
        ordenes = sum(1 for p in pedidos if int(p[1][5:7]) == mes and p[4] != "Cancelado")
        ml *= 1 + tarifas["resina_tasa_fallas"]
        g *= 1 + tarifas["fdm_tasa_fallas"]
        dia = lambda d: date(ANIO, mes, d).isoformat()  # noqa: E731
        litros = math.ceil(ml / 1000)
        kilos = math.ceil(g / 1000)
        gastos.append((dia(3), "Materiales", "Resina", litros * tarifas["resina_precio_litro"]))
        gastos.append((dia(3), "Materiales", "Filamento", kilos * tarifas["filamento_precio_kg"]))
        insumos = math.ceil(placas_resina) * (
            tarifas["alcohol_ml_por_placa"] * tarifas["alcohol_precio_litro"] / 1000
            + tarifas["guantes_pares_por_placa"] * tarifas["guantes_precio_par"] + tarifas["papel_por_placa"])
        gastos.append((dia(10), "Insumos", "Alcohol, guantes y papel", round(insumos, -3)))
        kwh = (horas_resina * tarifas["resina_potencia_w"] + horas_fdm * tarifas["fdm_potencia_w"]) / 1000
        gastos.append((dia(20), "Energía", "Luz de las impresoras", max(1000, round(kwh * tarifas["energia_precio_kwh"], -3))))
        film_acumulado += placas_resina
        if film_acumulado >= tarifas["fep_placas_vida"]:
            film_acumulado -= tarifas["fep_placas_vida"]
            gastos.append((dia(15), "Repuestos", "Film FEP", tarifas["fep_precio"]))
        if mes in (4, 9):
            gastos.append((dia(15), "Repuestos", "Boquilla y placa FDM", 80000))
        gastos.append((dia(1), "Publicidad", "Pauta en redes", 150000 + (250000 if mes in (11, 12) else 0)))
        gastos.append((dia(25), "Empaques", "Bolsas, cajas y etiquetas", ordenes * 1500))
        if mes == 3:
            gastos.append((dia(8), "Herramientas", "Lámpara de curado", 120000))
        if mes == 8:
            gastos.append((dia(8), "Herramientas", "Alicates y espátulas", 60000))
    gastos = [(f"GAS-{i:03d}", *gs) for i, gs in enumerate(gastos, 1)]
    escribir(salida, "gastos.csv", ["id_gasto", "fecha", "categoria", "concepto", "valor"], gastos)

    # Costo por pieza ya calculado (lo usa la plantilla y se compara en las pruebas).
    filas_costo = []
    for p in PIEZAS:
        c = costo_unitario(piezas[p[0]], tarifas)
        filas_costo.append([p[0]] + [round(c[k], 2) for k in
                                     ["material", "insumos", "energia", "maquina", "mano_obra", "fallas", "costo_total"]])
    escribir(salida, "costo_por_pieza.csv",
             ["id_pieza", "material", "insumos", "energia", "maquina", "mano_obra", "fallas", "costo_total"], filas_costo)

    return {"pedidos": len(pedidos), "lineas": len(detalle), "gastos": len(gastos), "clientes": len(clientes)}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--salida", default=str(RAIZ / "datos"))
    args = ap.parse_args()
    destino = Path(args.salida)
    if destino.name == "datos_reales":
        sys.exit("No escribo datos ficticios dentro de datos_reales/.")
    print(generar(destino))
