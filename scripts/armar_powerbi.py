"""Arma el tablero de Power BI como proyecto de texto (PBIP: TMDL + PBIR).

Así el modelo, el Power Query, las medidas DAX y las páginas quedan en archivos que
se pueden leer y revisar en GitHub. Power BI Desktop abre el .pbip y desde ahí se
guarda el .pbix y se exporta el PDF (pasos en docs/guia_power_bi.md).

Uso:
    python scripts/armar_powerbi.py                 # tablero con datos ficticios (repo)
    python scripts/armar_powerbi.py --datos datos_reales   # copia privada en datos_reales/powerbi/

También escribe dax/medidas.md con todas las medidas, para leerlas sin Power BI.
"""
from __future__ import annotations

import argparse
import json
import shutil
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOMBRE = "taller3d-costos"
NS = uuid.UUID("0d7c5e8e-5a0e-4b6e-9a51-3a2f6c1b7d00")

# Colores: un solo azul de acento, grises para lo demás (sin neón ni degradados).
AZUL = "#1a5fb4"
TEXTO = "#1f2933"
TEXTO_SUAVE = "#52606d"
BORDE = "#d9e0e7"
FONDO = "#f5f7f9"


def gid(*partes: str) -> str:
    return str(uuid.uuid5(NS, "/".join(partes)))


def hexid(*partes: str) -> str:
    return uuid.uuid5(NS, "/".join(partes)).hex[:20]


# ---------------------------------------------------------------------------
# Modelo semántico (TMDL)
# ---------------------------------------------------------------------------
LEER_CSV = ('Csv.Document(File.Contents(CarpetaDatos & "{archivo}.csv"), '
            '[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])')

# tabla: (archivo, [(columna, tipo_m, tipo_tmdl, formato, resumen, oculta)], pasos_extra)
TABLAS_CSV = {
    "Tarifas": ("tarifas", [
        ("parametro", "type text", "string", None, "none", False),
        ("valor", "type number", "double", None, "none", False),
        ("unidad", "type text", "string", None, "none", False),
        ("aplica_a", "type text", "string", None, "none", False),
        ("descripcion", "type text", "string", None, "none", False),
    ]),
    "Canales": ("canales", [
        ("canal", "type text", "string", None, "none", False),
        ("comision_pct", "type number", "double", "0%", "none", False),
        ("descripcion", "type text", "string", None, "none", True),
    ]),
    "Clientes": ("clientes", [
        ("id_cliente", "type text", "string", None, "none", False),
        ("ciudad", "type text", "string", None, "none", False),
    ]),
    "Pedidos": ("pedidos", [
        ("id_pedido", "type text", "string", None, "none", False),
        ("fecha", "type date", "dateTime", "Short Date", "none", False),
        ("canal", "type text", "string", None, "none", False),
        ("id_cliente", "type text", "string", None, "none", False),
        ("estado", "type text", "string", None, "none", False),
        ("origen_datos", "type text", "string", None, "none", True),
    ]),
    "Detalle": ("pedido_detalle", [
        ("id_pedido", "type text", "string", None, "none", True),
        ("linea", "Int64.Type", "int64", "0", "none", True),
        ("id_pieza", "type text", "string", None, "none", True),
        ("cantidad", "Int64.Type", "int64", "0", "sum", False),
        ("precio_unitario", "type number", "double", "\\$#,0", "none", False),
        ("descuento_pct", "type number", "double", "0%", "none", False),
    ]),
    "Gastos": ("gastos", [
        ("id_gasto", "type text", "string", None, "none", True),
        ("fecha", "type date", "dateTime", "Short Date", "none", True),
        ("categoria", "type text", "string", None, "none", False),
        ("concepto", "type text", "string", None, "none", False),
        ("valor", "type number", "double", "\\$#,0", "sum", False),
    ]),
}

PIEZAS_COLUMNAS = [
    ("id_pieza", "string", None, "none", False),
    ("nombre", "string", None, "none", False),
    ("categoria", "string", None, "none", False),
    ("tecnologia", "string", None, "none", False),
    ("material_cantidad", "double", "#,0.0", "none", False),
    ("horas_placa", "double", "#,0.0", "none", False),
    ("piezas_por_placa", "int64", "0", "none", False),
    ("minutos_acabado", "double", "0", "none", False),
    ("precio_lista", "double", "\\$#,0", "none", False),
    ("Costo material", "double", "\\$#,0", "sum", False),
    ("Costo insumos", "double", "\\$#,0", "sum", False),
    ("Costo energía", "double", "\\$#,0", "sum", False),
    ("Costo máquina", "double", "\\$#,0", "sum", False),
    ("Costo mano de obra", "double", "\\$#,0", "sum", False),
    ("Costo fallas", "double", "\\$#,0", "sum", False),
    ("Costo unitario", "double", "\\$#,0", "sum", False),
]

# La fórmula de scripts/costeo.py, en Power Query. T es la tabla de tarifas hecha registro.
PIEZAS_M = """let
    Origen = Csv.Document(File.Contents(CarpetaDatos & "piezas.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),
    // Los CSV usan punto decimal: se leen con cultura en-US para que 0.3 no se vuelva 3
    Tipos = Table.TransformColumnTypes(Encabezados, {{"material_cantidad", type number}, {"horas_placa", type number}, {"piezas_por_placa", Int64.Type}, {"minutos_acabado", type number}, {"precio_lista", type number}}, "en-US"),
    T = Record.FromList(Tarifas[valor], Tarifas[parametro]),
    EsResina = (fila) => fila[tecnologia] = "Resina",
    Material = Table.AddColumn(Tipos, "Costo material", each if EsResina(_) then [material_cantidad] * (1 + T[resina_soportes_pct]) * T[resina_precio_litro] / 1000 else [material_cantidad] * (1 + T[fdm_purga_pct]) * T[filamento_precio_kg] / 1000, type number),
    Insumos = Table.AddColumn(Material, "Costo insumos", each (if EsResina(_) then T[alcohol_ml_por_placa] * T[alcohol_precio_litro] / 1000 + T[guantes_pares_por_placa] * T[guantes_precio_par] + T[papel_por_placa] + T[fep_precio] / T[fep_placas_vida] else T[fdm_insumos_por_placa]) / [piezas_por_placa], type number),
    Energia = Table.AddColumn(Insumos, "Costo energía", each [horas_placa] * (if EsResina(_) then T[resina_potencia_w] else T[fdm_potencia_w]) / 1000 * T[energia_precio_kwh] / [piezas_por_placa], type number),
    Maquina = Table.AddColumn(Energia, "Costo máquina", each [horas_placa] * (if EsResina(_) then T[resina_maquina_hora] else T[fdm_maquina_hora]) / [piezas_por_placa], type number),
    ManoObra = Table.AddColumn(Maquina, "Costo mano de obra", each (T[preparacion_min_por_placa] / [piezas_por_placa] + [minutos_acabado]) / 60 * T[mano_obra_hora], type number),
    Base = (f) => f[Costo material] + f[Costo insumos] + f[Costo energía] + f[Costo máquina] + f[Costo mano de obra],
    Fallas = Table.AddColumn(ManoObra, "Costo fallas", each let tasa = if EsResina(_) then T[resina_tasa_fallas] else T[fdm_tasa_fallas] in Base(_) * tasa / (1 - tasa), type number),
    Total = Table.AddColumn(Fallas, "Costo unitario", each Base(_) + [Costo fallas], type number),
    SinMarca = Table.RemoveColumns(Total, {"origen_datos"})
in
    SinMarca"""


def m_tabla(archivo: str, columnas: list) -> str:
    tipos = ", ".join(f'{{"{c}", {tm}}}' for c, tm, *_ in columnas)
    quitar = "" if any(c == "origen_datos" for c, *_ in columnas) else (
        ',\n    SinMarca = Table.RemoveColumns(Tipos, {"origen_datos"})')
    final = "Tipos" if not quitar else "SinMarca"
    return (
        "let\n"
        f"    Origen = {LEER_CSV.format(archivo=archivo)},\n"
        "    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),\n"
        "    // Cultura en-US: los CSV usan punto decimal y fechas AAAA-MM-DD\n"
        f'    Tipos = Table.TransformColumnTypes(Encabezados, {{{tipos}}}, "en-US"){quitar}\n'
        "in\n"
        f"    {final}"
    )


def indentar(texto: str, tabs: int) -> str:
    return "\n".join(("\t" * tabs + l) if l.strip() else "" for l in texto.splitlines())


def nombre_tmdl(n: str) -> str:
    return n if n.replace("_", "").isalnum() and n.isascii() else "'" + n.replace("'", "''") + "'"


def columna_tmdl(tabla, nombre, tipo, formato, resumen, oculta, fuente=None, extra="") -> str:
    lineas = [f"\tcolumn {nombre_tmdl(nombre)}", f"\t\tdataType: {tipo}"]
    if formato:
        lineas.append(f"\t\tformatString: {formato}")
    if oculta:
        lineas.append("\t\tisHidden")
    lineas += [f"\t\tlineageTag: {gid('col', tabla, nombre)}", f"\t\tsummarizeBy: {resumen}",
               f"\t\tsourceColumn: {fuente or nombre}"]
    if extra:
        lineas.append(extra)
    lineas += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
    return "\n".join(lineas)


# Medidas: (nombre, dax, formato, carpeta, descripción)
MONEDA = "\\$#,0"
PCT = "0.0%"
MEDIDAS = [
    ("Origen de los datos",
     'VAR reales = CALCULATE(COUNTROWS(Pedidos), Pedidos[origen_datos] <> "ficticio", REMOVEFILTERS())\n'
     'RETURN IF(reales = 0, "Datos ficticios · taller de ejemplo", "DATOS REALES · no publicar")',
     None, "Control", "Aviso que sale en cada página: dice si el tablero está leyendo datos ficticios o reales."),
    ("Ventas netas",
     'CALCULATE(\n    SUMX(Detalle, Detalle[cantidad] * Detalle[precio_unitario] * (1 - Detalle[descuento_pct])),\n'
     '    Pedidos[estado] = "Entregado"\n)',
     MONEDA, "Ventas", "Precio x cantidad menos el descuento, solo pedidos entregados."),
    ("Unidades vendidas", 'CALCULATE(SUM(Detalle[cantidad]), Pedidos[estado] = "Entregado")', "#,0", "Ventas", None),
    ("Pedidos", "COUNTROWS(Pedidos)", "#,0", "Ventas", "Todos los pedidos, incluidos cancelados y devueltos."),
    ("Pedidos entregados", 'CALCULATE(COUNTROWS(Pedidos), Pedidos[estado] = "Entregado")', "#,0", "Ventas", None),
    ("% cancelados o devueltos", "DIVIDE([Pedidos] - [Pedidos entregados], [Pedidos])", PCT, "Ventas", None),
    ("Ticket promedio", "DIVIDE([Ventas netas], [Pedidos entregados])", MONEDA, "Ventas", "Venta promedio por pedido entregado."),
    ("Clientes que vuelven %",
     'VAR porCliente = ADDCOLUMNS(VALUES(Pedidos[id_cliente]), "@n", CALCULATE(COUNTROWS(Pedidos), Pedidos[estado] = "Entregado"))\n'
     "RETURN DIVIDE(COUNTROWS(FILTER(porCliente, [@n] > 1)), COUNTROWS(FILTER(porCliente, [@n] >= 1)))",
     PCT, "Ventas", "De los clientes con al menos un pedido entregado, cuántos compraron más de una vez."),
    ("Costo de lo vendido",
     'CALCULATE(SUMX(Detalle, Detalle[cantidad] * RELATED(Piezas[Costo unitario])), Pedidos[estado] = "Entregado")',
     MONEDA, "Ganancia", "Unidades vendidas x costo unitario de cada pieza (Power Query, consulta Piezas)."),
    ("Comisiones",
     "CALCULATE(\n    SUMX(Detalle, Detalle[cantidad] * Detalle[precio_unitario] * (1 - Detalle[descuento_pct])"
     " * RELATED(Canales[comision_pct])),\n    Pedidos[estado] = \"Entregado\"\n)",
     MONEDA, "Ganancia", "Lo que cobra cada canal (tienda de la plataforma o link de pago)."),
    ("Ganancia", "[Ventas netas] - [Costo de lo vendido] - [Comisiones]", MONEDA, "Ganancia", None),
    ("Margen %", "DIVIDE([Ganancia], [Ventas netas])", PCT, "Ganancia", None),
    ("Ventas menos comisiones", "[Ventas netas] - [Comisiones]", MONEDA, "Ganancia",
     "Ventas netas (después de descuentos) menos lo que cobran los canales."),
    ("Gastos", "SUM(Gastos[valor])", MONEDA, "Gastos", "Lo que salió de la caja (compras de material, pauta, empaques, repuestos)."),
    ("Gasto promedio por mes", "AVERAGEX(VALUES(Calendario[Mes clave]), [Gastos])", MONEDA, "Gastos", None),
    ("Resultado de caja", "[Ventas menos comisiones] - [Gastos]", MONEDA, "Gastos", "Ventas menos comisiones, menos gastos de caja del mes."),
    ("Material", "SUM(Piezas[Costo material])", MONEDA, "Costo por pieza", None),
    ("Insumos", "SUM(Piezas[Costo insumos])", MONEDA, "Costo por pieza", "Alcohol, guantes, papel y film FEP (resina) o pegante (FDM), repartidos en la placa."),
    ("Luz", "SUM(Piezas[Costo energía])", MONEDA, "Costo por pieza", None),
    ("Máquina", "SUM(Piezas[Costo máquina])", MONEDA, "Costo por pieza", "Desgaste y pago de la impresora por hora de uso."),
    ("Mano de obra", "SUM(Piezas[Costo mano de obra])", MONEDA, "Costo por pieza", "Preparar la placa (repartido) y el acabado de cada pieza."),
    ("Fallas", "SUM(Piezas[Costo fallas])", MONEDA, "Costo por pieza", "Lo que se pierde por placas que salen mal."),
    ("Costo por unidad", "SUM(Piezas[Costo unitario])", MONEDA, "Costo por pieza", None),
    ("% mano de obra", "DIVIDE([Mano de obra], [Costo por unidad])", PCT, "Costo por pieza", "Qué parte del costo es trabajo (preparar y acabar)."),
    ("% material", "DIVIDE([Material], [Costo por unidad])", PCT, "Costo por pieza", "Qué parte del costo es resina o filamento."),
    ("Costo promedio", "AVERAGE(Piezas[Costo unitario])", MONEDA, "Costo por pieza", "Promedio simple del catálogo."),
    ("Precio de lista", "AVERAGE(Piezas[precio_lista])", MONEDA, "Precio", None),
    ("Ganancia por hora de impresora",
     "DIVIDE(\n    SUMX(Piezas, Piezas[precio_lista] - Piezas[Costo unitario]),\n"
     "    SUMX(Piezas, Piezas[horas_placa] / Piezas[piezas_por_placa])\n)",
     MONEDA, "Precio", "Ganancia a precio de lista por cada hora que la pieza ocupa la impresora (placa llena). "
     "La impresora es el cuello de botella: esto dice qué conviene imprimir."),
    ("Margen objetivo", 'CALCULATE(MAX(Tarifas[valor]), Tarifas[parametro] = "margen_objetivo")', PCT, "Precio", None),
    ("Margen a precio de lista",
     "VAR comision = SELECTEDVALUE('Canal para precio'[Comisión], 0)\n"
     "RETURN DIVIDE(SUMX(Piezas, Piezas[precio_lista] * (1 - comision) - Piezas[Costo unitario]), SUM(Piezas[precio_lista]))",
     PCT, "Precio", "Margen de cada pieza a su precio de lista, después de la comisión del canal elegido en «Canal para precio» (sin canal: sin comisión)."),
    ("Precio sugerido",
     "VAR comision = SELECTEDVALUE('Canal para precio'[Comisión], 0)\n"
     'VAR paso = CALCULATE(MAX(Tarifas[valor]), Tarifas[parametro] = "redondeo_precio")\n'
     "VAR exacto = DIVIDE(SELECTEDVALUE(Piezas[Costo unitario]), 1 - [Margen objetivo] - comision)\n"
     "RETURN IF(HASONEVALUE(Piezas[id_pieza]), CEILING(ROUND(exacto / paso, 9), 1) * paso)",
     MONEDA, "Precio", "Precio para ganar el margen objetivo después de la comisión, redondeado hacia arriba (igual que costeo.py)."),
    ("Ajuste de precio", "SELECTEDVALUE('Ajuste de precio'[Ajuste de precio %], 0) / 100", "+0%;-0%;0%", "Qué pasa si", None),
    ("Ajuste de cantidad", "SELECTEDVALUE('Ajuste de cantidad'[Ajuste de cantidad %], 0) / 100", "+0%;-0%;0%", "Qué pasa si", None),
    ("Ventas con ajuste",
     "VAR ap = [Ajuste de precio]\nVAR ac = [Ajuste de cantidad]\nRETURN CALCULATE(\n"
     "    SUMX(Detalle, Detalle[cantidad] * (1 + ac) * Detalle[precio_unitario] * (1 - Detalle[descuento_pct]) * (1 + ap)),\n"
     '    Pedidos[estado] = "Entregado"\n)',
     MONEDA, "Qué pasa si", "Ventas del año si el precio y la cantidad cambian según los dos parámetros."),
    ("Ganancia con ajuste",
     "VAR ap = [Ajuste de precio]\nVAR ac = [Ajuste de cantidad]\nRETURN CALCULATE(\n"
     "    SUMX(Detalle,\n        Detalle[cantidad] * (1 + ac) * (\n"
     "            Detalle[precio_unitario] * (1 - Detalle[descuento_pct]) * (1 + ap) * (1 - RELATED(Canales[comision_pct]))\n"
     "            - RELATED(Piezas[Costo unitario])\n        )\n    ),\n"
     '    Pedidos[estado] = "Entregado"\n)',
     MONEDA, "Qué pasa si", "Misma cuenta de sql/07_que_pasa_si.sql."),
    ("Cambio en la ganancia", "[Ganancia con ajuste] - [Ganancia]", "+\\$#,0;-\\$#,0;\\$0", "Qué pasa si", None),
    ("Margen con ajuste %", "DIVIDE([Ganancia con ajuste], [Ventas con ajuste])", PCT, "Qué pasa si", None),
]


def tabla_medidas() -> str:
    partes = ["table Medidas", f"\tlineageTag: {gid('tabla', 'Medidas')}", ""]
    for nombre, dax, formato, carpeta, desc in MEDIDAS:
        if desc:
            partes.append(f"\t/// {desc}")
        if "\n" in dax:
            partes.append(f"\tmeasure {nombre_tmdl(nombre)} =")
            partes.append(indentar(dax, 3))
        else:
            partes.append(f"\tmeasure {nombre_tmdl(nombre)} = {dax}")
        if formato:
            partes.append(f"\t\tformatString: {formato}")
        partes += [f"\t\tdisplayFolder: {carpeta}", f"\t\tlineageTag: {gid('medida', nombre)}", ""]
    partes += [
        "\tcolumn Orden", "\t\tdataType: int64", "\t\tisHidden", f"\t\tlineageTag: {gid('col', 'Medidas', 'Orden')}",
        "\t\tsummarizeBy: none", "\t\tsourceColumn: [Orden]", "",
        "\tpartition Medidas = calculated", "\t\tmode: import", '\t\tsource = ROW("Orden", 1)', "",
    ]
    return "\n".join(partes)


def tabla_parametro(nombre: str, columna: str) -> str:
    return "\n".join([
        f"table '{nombre}'", f"\tlineageTag: {gid('tabla', nombre)}", "",
        f"\tcolumn '{columna}'", "\t\tdataType: int64", "\t\tformatString: +0;-0;0",
        f"\t\tlineageTag: {gid('col', nombre, columna)}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: [{columna}]", "",
        "\t\textendedProperty ParameterMetadata =", "\t\t\t\t{", '\t\t\t\t  "version": 0', "\t\t\t\t}", "",
        f"\tpartition '{nombre}' = calculated", "\t\tmode: import",
        f'\t\tsource = SELECTCOLUMNS(GENERATESERIES(-30, 30, 5), "{columna}", [Value])', "",
        "\tannotation PBI_Id = " + hexid("param", nombre), "",
    ])


def tabla_canal_precio() -> str:
    """Copia desconectada de Canales: elegir aquí un canal NO filtra las ventas, solo el precio sugerido."""
    return "\n".join([
        "table 'Canal para precio'", f"\tlineageTag: {gid('tabla', 'Canal para precio')}", "",
        columna_tmdl("Canal para precio", "Canal", "string", None, "none", False, "[Canal]"),
        columna_tmdl("Canal para precio", "Comisión", "double", "0%", "none", False, "[Comisión]"),
        "\tpartition 'Canal para precio' = calculated", "\t\tmode: import",
        '\t\tsource = SELECTCOLUMNS(Canales, "Canal", Canales[canal], "Comisión", Canales[comision_pct])', "",
    ])


def tabla_calendario() -> str:
    fuente = (
        "VAR inicio = MIN(MIN(Pedidos[fecha]), MIN(Gastos[fecha]))\n"
        "VAR fin = MAX(MAX(Pedidos[fecha]), MAX(Gastos[fecha]))\n"
        "RETURN ADDCOLUMNS(\n"
        "    CALENDAR(DATE(YEAR(inicio), 1, 1), DATE(YEAR(fin), 12, 31)),\n"
        '    "Año", YEAR([Date]),\n'
        '    "Mes clave", YEAR([Date]) * 100 + MONTH([Date]),\n'
        '    "Mes", FORMAT([Date], "mmm yy")\n'
        ")"
    )
    cols = [
        columna_tmdl("Calendario", "Fecha", "dateTime", "Short Date", "none", False, "[Date]"),
        columna_tmdl("Calendario", "Año", "int64", "0", "none", False, "[Año]"),
        columna_tmdl("Calendario", "Mes clave", "int64", "0", "none", True, "[Mes clave]"),
        columna_tmdl("Calendario", "Mes", "string", None, "none", False, "[Mes]", "\t\tsortByColumn: 'Mes clave'"),
    ]
    return "\n".join(["table Calendario", f"\tlineageTag: {gid('tabla', 'Calendario')}", "", "\n".join(cols),
                      "\tpartition Calendario = calculated", "\t\tmode: import", "\t\tsource =", indentar(fuente, 4), ""])


def tabla_csv(nombre: str, archivo: str, columnas: list, oculta: bool = False) -> str:
    cols = [columna_tmdl(nombre, c, tt, fmt, res, oc) for c, _tm, tt, fmt, res, oc in columnas]
    cab = [f"table {nombre}"] + (["\tisHidden"] if oculta else []) + [f"\tlineageTag: {gid('tabla', nombre)}", ""]
    return "\n".join(cab + cols + [f"\tpartition {nombre} = m", "\t\tmode: import", "\t\tsource =",
                                   indentar(m_tabla(archivo, columnas), 4), "",
                                   "\tannotation PBI_ResultType = Table", ""])


def tabla_piezas() -> str:
    cols = [columna_tmdl("Piezas", c, t, f, r, o) for c, t, f, r, o in PIEZAS_COLUMNAS]
    return "\n".join([f"table Piezas", f"\tlineageTag: {gid('tabla', 'Piezas')}", ""] + cols + [
        "\tpartition Piezas = m", "\t\tmode: import", "\t\tsource =", indentar(PIEZAS_M, 4), "",
        "\tannotation PBI_ResultType = Table", ""])


RELACIONES = [
    ("Detalle", "id_pedido", "Pedidos", "id_pedido"),
    ("Detalle", "id_pieza", "Piezas", "id_pieza"),
    ("Pedidos", "id_cliente", "Clientes", "id_cliente"),
    ("Pedidos", "canal", "Canales", "canal"),
    ("Pedidos", "fecha", "Calendario", "Fecha"),
    ("Gastos", "fecha", "Calendario", "Fecha"),
]


def escribir_modelo(base: Path, carpeta_datos: str) -> None:
    sm = base / f"{NOMBRE}.SemanticModel"
    d = sm / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)
    (d / "cultures").mkdir(parents=True, exist_ok=True)
    escribir(sm / "definition.pbism", json.dumps({"version": "4.2", "settings": {}}, indent=2))
    escribir(sm / ".platform", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NOMBRE},
        "config": {"version": "2.0", "logicalId": gid("modelo")}}, indent=2))
    escribir(d / "database.tmdl", "database\n\tcompatibilityLevel: 1606\n")
    escribir(d / "cultures" / "es-ES.tmdl", "cultureInfo es-ES\n")
    tablas = ["Tarifas", "Canales", "Clientes", "Pedidos", "Detalle", "Gastos", "Piezas", "Calendario",
              "Ajuste de precio", "Ajuste de cantidad", "Canal para precio", "Medidas"]
    escribir(d / "model.tmdl", "\n".join([
        "model Model", "\tculture: es-ES", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: es-CO", "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
        "annotation __PBI_TimeIntelligenceEnabled = 0", "",
        'annotation PBI_QueryOrder = ["CarpetaDatos","Tarifas","Canales","Clientes","Pedidos","Detalle","Gastos","Piezas"]', "",
        'annotation PBI_ProTooling = ["DevMode"]', "",
        *[f"ref table {nombre_tmdl(t)}" for t in tablas], "", "ref cultureInfo es-ES", ""]))
    ruta = str(RAIZ / carpeta_datos).replace("/", "\\") + "\\" if carpeta_datos != "datos" else (
        "C:\\Trabajo\\taller3d-costos\\datos\\")
    escribir(d / "expressions.tmdl", "\n".join([
        "/// Carpeta con los CSV. Cámbiala a la carpeta donde clonaste el repo (termina en \\datos\\).",
        "/// Para tus datos reales, apunta a ...\\datos_reales\\ (esa carpeta nunca se sube a GitHub).",
        f'expression CarpetaDatos = "{ruta}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]',
        f"\tlineageTag: {gid('param', 'CarpetaDatos')}", "", "\tannotation PBI_ResultType = Text", ""]))
    for nombre, (archivo, columnas) in TABLAS_CSV.items():
        escribir(d / "tables" / f"{nombre}.tmdl", tabla_csv(nombre, archivo, columnas, oculta=nombre == "Tarifas"))
    escribir(d / "tables" / "Piezas.tmdl", tabla_piezas())
    escribir(d / "tables" / "Calendario.tmdl", tabla_calendario())
    escribir(d / "tables" / "Canal para precio.tmdl", tabla_canal_precio())
    escribir(d / "tables" / "Ajuste de precio.tmdl", tabla_parametro("Ajuste de precio", "Ajuste de precio %"))
    escribir(d / "tables" / "Ajuste de cantidad.tmdl", tabla_parametro("Ajuste de cantidad", "Ajuste de cantidad %"))
    escribir(d / "tables" / "Medidas.tmdl", tabla_medidas())
    rel = []
    for desde_t, desde_c, hacia_t, hacia_c in RELACIONES:
        rel += [f"relationship {gid('rel', desde_t, desde_c)}", f"\tfromColumn: {desde_t}.{desde_c}",
                f"\ttoColumn: {hacia_t}.{nombre_tmdl(hacia_c)}", ""]
    escribir(d / "relationships.tmdl", "\n".join(rel))


# ---------------------------------------------------------------------------
# Informe (PBIR)
# ---------------------------------------------------------------------------
ESQ = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"


def lit(v) -> dict:
    if isinstance(v, bool):
        txt = "true" if v else "false"
    elif isinstance(v, (int, float)):
        txt = f"{v}D"
    else:
        txt = "'" + str(v).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": txt}}}


def col(tabla: str, columna: str) -> tuple[dict, str]:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": columna}}, f"{tabla}.{columna}"


def med(nombre: str) -> tuple[dict, str]:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "Medidas"}}, "Property": nombre}}, f"Medidas.{nombre}"


def proyeccion(campo: tuple[dict, str], alias: str | None = None) -> dict:
    p = {"field": campo[0], "queryRef": campo[1], "nativeQueryRef": alias or campo[1].split(".", 1)[1]}
    if alias:
        p["displayName"] = alias
    return p


def titulo(texto: str | None, subtitulo: str | None = None) -> dict:
    obj = {"title": [{"properties": {"show": lit(bool(texto)), **({"text": lit(texto)} if texto else {}),
                                     "fontColor": {"solid": {"color": lit(TEXTO)}}, "fontSize": lit(11)}}],
           "border": [{"properties": {"show": lit(True), "color": {"solid": {"color": lit(BORDE)}}, "radius": lit(4)}}],
           "background": [{"properties": {"show": lit(True), "color": {"solid": {"color": lit("#FFFFFF")}}}}],
           "padding": [{"properties": {"top": lit(8), "bottom": lit(8), "left": lit(10), "right": lit(10)}}]}
    obj["subTitle"] = [{"properties": {"show": lit(bool(subtitulo)), **({"text": lit(subtitulo)} if subtitulo else {}),
                                       "fontColor": {"solid": {"color": lit(TEXTO_SUAVE)}}}}]
    return obj


class Pagina:
    def __init__(self, clave: str, nombre: str):
        self.clave = clave
        self.id = hexid("pagina", clave)
        self.nombre = nombre
        self.visuales: list[dict] = []

    def agregar(self, clave, x, y, w, h, visual: dict, contenedor: dict | None = None):
        v = {"$schema": f"{ESQ}/visualContainer/2.14.0/schema.json", "name": hexid(self.clave, clave),
             "position": {"x": x, "y": y, "z": len(self.visuales) * 1000, "height": h, "width": w,
                          "tabOrder": len(self.visuales) * 1000},
             "visual": visual}
        if contenedor is not None:
            v["visual"]["visualContainerObjects"] = contenedor
        self.visuales.append(v)

    # --- tipos de visual ---------------------------------------------------
    def texto(self, clave, x, y, w, h, lineas: list[tuple[str, int, bool, str]]):
        parrafos = [{"textRuns": [{"value": t, "textStyle": {"fontFamily": "Segoe UI", "fontSize": f"{tam}pt",
                                                              **({"fontWeight": "bold"} if negrita else {}),
                                                              "color": color}}]}
                    for t, tam, negrita, color in lineas]
        self.agregar(clave, x, y, w, h, {"visualType": "textbox",
                                         "objects": {"general": [{"properties": {"paragraphs": parrafos}}]},
                                         "drillFilterOtherVisuals": True},
                     {"background": [{"properties": {"show": lit(False)}}]})

    def tarjeta(self, clave, x, y, w, h, medida: str, etiqueta: str | None = None):
        self.agregar(clave, x, y, w, h, {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proyeccion(med(medida), etiqueta)]}}},
            "objects": {"labels": [{"properties": {"color": {"solid": {"color": lit(TEXTO)}}, "fontSize": lit(22),
                                                   "labelDisplayUnits": lit(1)}}],
                        "categoryLabels": [{"properties": {"show": lit(True), "color": {"solid": {"color": lit(TEXTO_SUAVE)}},
                                                           "fontSize": lit(10)}}]},
            "drillFilterOtherVisuals": True}, titulo(None))

    def aviso(self, clave, x, y, w, h):
        """Tarjeta pequeña con «Datos ficticios» (o «DATOS REALES» si se cambió la carpeta)."""
        self.agregar(clave, x, y, w, h, {
            "visualType": "card",
            "query": {"queryState": {"Values": {"projections": [proyeccion(med("Origen de los datos"))]}}},
            "objects": {"labels": [{"properties": {"color": {"solid": {"color": lit(TEXTO_SUAVE)}}, "fontSize": lit(10)}}],
                        "categoryLabels": [{"properties": {"show": lit(False)}}]},
            "drillFilterOtherVisuals": True},
            {"background": [{"properties": {"show": lit(False)}}], "border": [{"properties": {"show": lit(False)}}]})

    def segmentador(self, clave, x, y, w, h, campo, encabezado: str, unico: bool = False, estricto: bool = False,
                    valor_inicial: int | None = None):
        objetos = {"data": [{"properties": {"mode": lit("Dropdown")}}],
                   "selection": [{"properties": {"singleSelect": lit(unico), "strictSingleSelect": lit(estricto)}}],
                   "header": [{"properties": {"show": lit(True), "text": lit(encabezado),
                                              "fontColor": {"solid": {"color": lit(TEXTO_SUAVE)}}}}]}
        if valor_inicial is not None:  # valor ya elegido al abrir (así lo guarda Power BI)
            tabla, columna = campo[1].split(".", 1)
            objetos["general"] = [{"properties": {"filter": {"filter": {
                "Version": 2, "From": [{"Name": "a", "Entity": tabla, "Type": 0}],
                "Where": [{"Condition": {"In": {
                    "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "a"}}, "Property": columna}}],
                    "Values": [[{"Literal": {"Value": f"{valor_inicial}L"}}]]}}}]}}}}]
        self.agregar(clave, x, y, w, h, {
            "visualType": "slicer",
            "query": {"queryState": {"Values": {"projections": [proyeccion(campo)]}}},
            "objects": objetos,
            "drillFilterOtherVisuals": True}, titulo(None))

    def grafico(self, clave, x, y, w, h, tipo, categoria, valores: list, titulo_txt: str, serie=None,
                orden=None, sub: str | None = None, etiquetas: bool = False, info: list | None = None):
        estado = {"Category": {"projections": [proyeccion(categoria)]},
                  "Y": {"projections": [proyeccion(v) for v in valores]}}
        if serie:
            estado["Series"] = {"projections": [proyeccion(serie)]}
        if info:
            estado["Tooltips"] = {"projections": [proyeccion(v) for v in info]}
        query = {"queryState": estado}
        if orden:
            campo, sentido = orden
            query["sortDefinition"] = {"sort": [{"field": campo[0], "direction": sentido}], "isDefaultSort": False}
        objetos = {"categoryAxis": [{"properties": {"showAxisTitle": lit(False)}}],
                   "valueAxis": [{"properties": {"showAxisTitle": lit(False), "gridlineColor": {"solid": {"color": lit("#e9edf1")}}}}],
                   "legend": [{"properties": {"show": lit(len(valores) > 1 or serie is not None), "position": lit("Top")}}]}
        if etiquetas:
            objetos["labels"] = [{"properties": {"show": lit(True), "color": {"solid": {"color": lit(TEXTO_SUAVE)}}}}]
        if tipo == "lineChart":  # recta: la curva inventa subidas entre meses
            objetos["lineStyles"] = [{"properties": {"lineChartType": lit("'linear'")}}]
        if len(valores) == 1 and serie is None:
            objetos["dataPoint"] = [{"properties": {"fill": {"solid": {"color": lit(AZUL)}}}}]
        self.agregar(clave, x, y, w, h, {"visualType": tipo, "query": query, "objects": objetos,
                                         "drillFilterOtherVisuals": True}, titulo(titulo_txt, sub))

    def tabla(self, clave, x, y, w, h, campos: list, titulo_txt: str, orden=None):
        query = {"queryState": {"Values": {"projections": [proyeccion(c, a) for c, a in campos]}}}
        if orden:
            query["sortDefinition"] = {"sort": [{"field": orden[0][0], "direction": orden[1]}], "isDefaultSort": False}
        self.agregar(clave, x, y, w, h, {
            "visualType": "tableEx", "query": query,
            "objects": {"grid": [{"properties": {"gridHorizontalColor": {"solid": {"color": lit("#e9edf1")}},
                                                 "rowPadding": lit(2), "textSize": lit(10)}}],
                        "columnHeaders": [{"properties": {"fontColor": {"solid": {"color": lit(TEXTO)}},
                                                          "backColor": {"solid": {"color": lit(FONDO)}}}}],
                        "total": [{"properties": {"totals": lit(False)}}]},
            "drillFilterOtherVisuals": True}, titulo(titulo_txt))

    def encabezado(self, titulo_txt: str, pregunta: str):
        self.texto("titulo", 24, 12, 900, 64, [(titulo_txt, 20, True, TEXTO), (pregunta, 11, False, TEXTO_SUAVE)])
        self.aviso("aviso", 1000, 12, 256, 56)


def paginas() -> list[Pagina]:
    p1 = Pagina("costo", "Costo por pieza")
    p1.encabezado("Costo por pieza", "¿Cuánto cuesta de verdad cada pieza, en resina y en FDM?")
    p1.segmentador("tec", 24, 84, 200, 84, col("Piezas", "tecnologia"), "Tecnología")
    p1.tarjeta("prom", 240, 84, 220, 84, "Costo promedio", "Costo promedio por pieza")
    p1.tarjeta("mo", 476, 84, 220, 84, "% mano de obra", "Del costo es mano de obra")
    p1.tarjeta("mat", 712, 84, 220, 84, "% material", "Del costo es material")
    p1.tarjeta("obj", 948, 84, 308, 84, "Margen objetivo", "Margen objetivo (tarifas.csv)")
    p1.grafico("comp", 24, 184, 580, 512, "barChart", col("Piezas", "nombre"),
               [med(m) for m in ("Material", "Insumos", "Luz", "Máquina", "Mano de obra", "Fallas")],
               "En qué se va el costo de cada pieza", orden=(med("Costo por unidad"), "Descending"),
               sub="Pesos por unidad. La placa se reparte entre las piezas que caben en ella.",
               info=[med("Costo por unidad")])
    p1.tabla("tabla", 620, 184, 636, 512, [
        (col("Piezas", "nombre"), "Pieza"), (col("Piezas", "tecnologia"), "Tecnología"),
        (med("Costo por unidad"), "Costo"), (med("Precio de lista"), "Precio de lista"),
        (med("Margen a precio de lista"), "Margen"), (med("Ganancia por hora de impresora"), "Ganancia por hora")],
        "Costo, margen y ganancia por hora de impresora", orden=(med("Ganancia por hora de impresora"), "Descending"))

    p2 = Pagina("precio", "Precio y margen")
    p2.encabezado("Precio y margen", "¿Qué pasa con la ganancia del año si cambio el precio y vendo más o menos?")
    p2.segmentador("ap", 24, 84, 200, 76, col("Ajuste de precio", "Ajuste de precio %"), "Cambio de precio %", True,
                   valor_inicial=10)
    p2.segmentador("ac", 240, 84, 200, 76, col("Ajuste de cantidad", "Ajuste de cantidad %"), "Cambio de cantidad %", True,
                   valor_inicial=-10)
    p2.tarjeta("g0", 456, 84, 190, 76, "Ganancia", "Ganancia del año")
    p2.tarjeta("g1", 662, 84, 190, 76, "Ganancia con ajuste", "Ganancia con el cambio")
    p2.tarjeta("dg", 868, 84, 190, 76, "Cambio en la ganancia", "Diferencia")
    p2.tarjeta("mg", 1074, 84, 182, 76, "Margen con ajuste %", "Margen con el cambio")
    p2.grafico("marg", 24, 176, 600, 520, "clusteredBarChart", col("Piezas", "nombre"), [med("Margen %")],
               "Margen real de lo vendido, por pieza", orden=(med("Margen %"), "Ascending"), etiquetas=True,
               sub="Después de descuentos y comisiones. Pedidos entregados del año.")
    p2.segmentador("canal", 640, 176, 220, 60, col("Canal para precio", "Canal"), "Canal", True, True)
    p2.tabla("sug", 640, 244, 616, 452, [
        (col("Piezas", "nombre"), "Pieza"), (med("Costo por unidad"), "Costo"),
        (med("Precio de lista"), "Precio de lista"), (med("Precio sugerido"), "Precio sugerido"),
        (med("Margen a precio de lista"), "Margen a precio de lista")],
        "Precio sugerido para el margen objetivo", orden=(med("Margen a precio de lista"), "Ascending"))

    p3 = Pagina("gastos", "Gastos por mes")
    p3.encabezado("Gastos por mes", "¿En qué se va la plata del taller cada mes y cuánto queda?")
    p3.tarjeta("tot", 24, 84, 300, 84, "Gastos", "Gastos del año")
    p3.tarjeta("prom", 340, 84, 300, 84, "Gasto promedio por mes", "Gasto promedio por mes")
    p3.tarjeta("vent", 656, 84, 300, 84, "Ventas menos comisiones", "Ventas menos comisiones")
    p3.tarjeta("caja", 972, 84, 284, 84, "Resultado de caja", "Resultado de caja")
    p3.grafico("mes", 24, 184, 616, 512, "columnChart", col("Calendario", "Mes"), [med("Gastos")],
               "Gastos por mes y categoría", serie=col("Gastos", "categoria"),
               sub="Lo que salió de la caja: la resina y el filamento se compran por litro o kilo.")
    p3.grafico("vs", 656, 184, 600, 512, "lineChart", col("Calendario", "Mes"),
               [med("Ventas menos comisiones"), med("Gastos")], "Ventas frente a gastos")

    p4 = Pagina("canal", "Pedidos por canal")
    p4.encabezado("Pedidos por canal", "¿Por dónde llegan los pedidos y cuál canal deja más?")
    p4.tarjeta("ped", 24, 84, 300, 84, "Pedidos", "Pedidos del año")
    p4.tarjeta("ven", 340, 84, 300, 84, "Ventas netas", "Ventas netas")
    p4.tarjeta("tick", 656, 84, 300, 84, "Ticket promedio", "Ticket promedio")
    p4.tarjeta("canc", 972, 84, 284, 84, "% cancelados o devueltos", "Cancelados o devueltos")
    p4.grafico("linea", 24, 184, 760, 330, "lineChart", col("Calendario", "Mes"), [med("Pedidos")],
               "Pedidos por mes y canal", serie=col("Pedidos", "canal"))
    p4.grafico("gan", 800, 184, 456, 330, "clusteredBarChart", col("Pedidos", "canal"),
               [med("Ventas netas"), med("Ganancia")], "Ventas y ganancia por canal",
               orden=(med("Ventas netas"), "Descending"))
    p4.tabla("tabla", 24, 530, 1232, 166, [
        (col("Pedidos", "canal"), "Canal"), (med("Pedidos entregados"), "Pedidos entregados"), (med("Ventas netas"), "Ventas netas"),
        (med("Ticket promedio"), "Ticket promedio"), (med("Comisiones"), "Comisiones"), (med("Ganancia"), "Ganancia"),
        (med("Margen %"), "Margen"), (med("Clientes que vuelven %"), "Clientes que vuelven")],
        "Resumen por canal", orden=(med("Ventas netas"), "Descending"))
    return [p1, p2, p3, p4]


TEMA = {
    "name": "Taller3D",
    "dataColors": [AZUL, "#8fb1dd", "#3e4c59", "#c3ccd5", "#0f3a6e", "#7b8794", "#dbe6f3", "#52606d"],
    "background": "#FFFFFF", "foreground": TEXTO, "tableAccent": AZUL,
    "good": "#2f7d5b", "neutral": "#7b8794", "bad": "#b3261e",
    "textClasses": {
        "callout": {"fontFace": "Segoe UI Semibold", "fontSize": 22, "color": TEXTO},
        "title": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": TEXTO},
        "header": {"fontFace": "Segoe UI Semibold", "fontSize": 11, "color": TEXTO},
        "label": {"fontFace": "Segoe UI", "fontSize": 10, "color": TEXTO_SUAVE},
    },
    "visualStyles": {"page": {"*": {"background": [{"color": {"solid": {"color": FONDO}}, "transparency": 0}],
                                    "outspace": [{"color": {"solid": {"color": FONDO}}}]}}},
}


def escribir_informe(base: Path) -> None:
    rep = base / f"{NOMBRE}.Report"
    d = rep / "definition"
    if d.exists():
        shutil.rmtree(d)  # se regenera completo (solo esta carpeta generada)
    (d / "pages").mkdir(parents=True)
    escribir(rep / "definition.pbir", json.dumps({"version": "4.0", "datasetReference": {
        "byPath": {"path": f"../{NOMBRE}.SemanticModel"}}}, indent=2))
    escribir(rep / ".platform", json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NOMBRE},
        "config": {"version": "2.0", "logicalId": gid("informe")}}, indent=2))
    escribir(d / "version.json", json.dumps({"$schema": f"{ESQ}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2))
    version = {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"}
    escribir(d / "report.json", json.dumps({
        "$schema": f"{ESQ}/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": "Fluent2-CY26SU10", "reportVersionAtImport": version, "type": "SharedResources"},
            "customTheme": {"name": "Taller3D.json", "reportVersionAtImport": version, "type": "RegisteredResources"}},
        "objects": {"section": [{"properties": {"verticalAlignment": lit("Top")}}]},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "Fluent2-CY26SU10", "path": "BaseThemes/Fluent2-CY26SU10.json", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources",
             "items": [{"name": "Taller3D.json", "path": "Taller3D.json", "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    }, ensure_ascii=False, indent=2))
    recursos = rep / "StaticResources"
    (recursos / "SharedResources" / "BaseThemes").mkdir(parents=True, exist_ok=True)
    (recursos / "RegisteredResources").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(RAIZ / "scripts" / "powerbi_base" / "Fluent2-CY26SU10.json",
                    recursos / "SharedResources" / "BaseThemes" / "Fluent2-CY26SU10.json")
    escribir(recursos / "RegisteredResources" / "Taller3D.json", json.dumps(TEMA, ensure_ascii=False, indent=2))
    ps = paginas()
    escribir(d / "pages" / "pages.json", json.dumps({"$schema": f"{ESQ}/pagesMetadata/1.1.0/schema.json",
                                                     "pageOrder": [p.id for p in ps], "activePageName": ps[0].id}, indent=2))
    for p in ps:
        carpeta = d / "pages" / p.id
        escribir(carpeta / "page.json", json.dumps({
            "$schema": f"{ESQ}/page/2.1.0/schema.json", "name": p.id, "displayName": p.nombre,
            "displayOption": "FitToPage", "height": 720, "width": 1280}, ensure_ascii=False, indent=2))
        for v in p.visuales:
            escribir(carpeta / "visuals" / v["name"] / "visual.json", json.dumps(v, ensure_ascii=False, indent=2))


def escribir(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto if texto.endswith("\n") else texto + "\n", encoding="utf-8", newline="\n")


def escribir_medidas_md() -> None:
    partes = ["# Medidas DAX del tablero", "",
              "Copia en texto de las medidas del modelo (tabla `Medidas`), para leerlas sin abrir Power BI.",
              "Las genera `scripts/armar_powerbi.py`, el mismo script que arma el tablero.", "",
              "El costo de cada pieza no es una medida: se calcula en Power Query (consulta `Piezas`) con la misma",
              "fórmula de `scripts/costeo.py`. Las medidas usan esa columna `Piezas[Costo unitario]`.", ""]
    carpeta_actual = None
    for nombre, dax, formato, carpeta, desc in MEDIDAS:
        if carpeta != carpeta_actual:
            partes += [f"## {carpeta}", ""]
            carpeta_actual = carpeta
        partes.append(f"### {nombre}")
        if desc:
            partes.append(desc)
        partes += ["", "```dax", f"{nombre} =", dax, "```", ""]
    partes += ["## Parámetros «qué pasa si»", "",
               "Dos tablas hechas con `GENERATESERIES(-30, 30, 5)`: el cambio de precio y el de cantidad, en %.",
               "Si no se elige nada en el segmentador, las medidas usan 0 % (el año como fue).", "",
               "## Power Query: costo por pieza (consulta `Piezas`)", "", "```powerquery", PIEZAS_M, "```", ""]
    escribir(RAIZ / "dax" / "medidas.md", "\n".join(partes))


def main() -> None:
    ap = argparse.ArgumentParser(description="Arma el proyecto de Power BI (PBIP)")
    ap.add_argument("--datos", default="datos", help="datos (repo) o datos_reales (copia privada)")
    a = ap.parse_args()
    base = RAIZ / "powerbi" / "proyecto" if a.datos == "datos" else RAIZ / a.datos / "powerbi"
    escribir_modelo(base, a.datos)
    escribir_informe(base)
    escribir(base / f"{NOMBRE}.pbip", json.dumps({"version": "1.0", "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}],
                                                  "settings": {"enableAutoRecovery": True}}, indent=2))
    escribir(base / ".gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")
    if a.datos == "datos":
        escribir_medidas_md()
    print("Proyecto de Power BI en", base.relative_to(RAIZ))


if __name__ == "__main__":
    main()
