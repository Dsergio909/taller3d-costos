# Medidas DAX del tablero

Copia en texto de las medidas del modelo (tabla `Medidas`), para leerlas sin abrir Power BI.
Las genera `scripts/armar_powerbi.py`, el mismo script que arma el tablero.

El costo de cada pieza no es una medida: se calcula en Power Query (consulta `Piezas`) con la misma
fórmula de `scripts/costeo.py`. Las medidas usan esa columna `Piezas[Costo unitario]`.

## Control

### Origen de los datos
Aviso que sale en cada página: dice si el tablero está leyendo datos ficticios o reales.

```dax
Origen de los datos =
VAR reales = CALCULATE(COUNTROWS(Pedidos), Pedidos[origen_datos] <> "ficticio", REMOVEFILTERS())
RETURN IF(reales = 0, "Datos ficticios · taller de ejemplo", "DATOS REALES · no publicar")
```

## Ventas

### Ventas netas
Precio x cantidad menos el descuento, solo pedidos entregados.

```dax
Ventas netas =
CALCULATE(
    SUMX(Detalle, Detalle[cantidad] * Detalle[precio_unitario] * (1 - Detalle[descuento_pct])),
    Pedidos[estado] = "Entregado"
)
```

### Unidades vendidas

```dax
Unidades vendidas =
CALCULATE(SUM(Detalle[cantidad]), Pedidos[estado] = "Entregado")
```

### Pedidos
Todos los pedidos, incluidos cancelados y devueltos.

```dax
Pedidos =
COUNTROWS(Pedidos)
```

### Pedidos entregados

```dax
Pedidos entregados =
CALCULATE(COUNTROWS(Pedidos), Pedidos[estado] = "Entregado")
```

### % cancelados o devueltos

```dax
% cancelados o devueltos =
DIVIDE([Pedidos] - [Pedidos entregados], [Pedidos])
```

### Ticket promedio
Venta promedio por pedido entregado.

```dax
Ticket promedio =
DIVIDE([Ventas netas], [Pedidos entregados])
```

### Clientes que vuelven %
De los clientes con al menos un pedido entregado, cuántos compraron más de una vez.

```dax
Clientes que vuelven % =
VAR porCliente = ADDCOLUMNS(VALUES(Pedidos[id_cliente]), "@n", CALCULATE(COUNTROWS(Pedidos), Pedidos[estado] = "Entregado"))
RETURN DIVIDE(COUNTROWS(FILTER(porCliente, [@n] > 1)), COUNTROWS(FILTER(porCliente, [@n] >= 1)))
```

## Ganancia

### Costo de lo vendido
Unidades vendidas x costo unitario de cada pieza (Power Query, consulta Piezas).

```dax
Costo de lo vendido =
CALCULATE(SUMX(Detalle, Detalle[cantidad] * RELATED(Piezas[Costo unitario])), Pedidos[estado] = "Entregado")
```

### Comisiones
Lo que cobra cada canal (tienda de la plataforma o link de pago).

```dax
Comisiones =
CALCULATE(
    SUMX(Detalle, Detalle[cantidad] * Detalle[precio_unitario] * (1 - Detalle[descuento_pct]) * RELATED(Canales[comision_pct])),
    Pedidos[estado] = "Entregado"
)
```

### Ganancia

```dax
Ganancia =
[Ventas netas] - [Costo de lo vendido] - [Comisiones]
```

### Margen %

```dax
Margen % =
DIVIDE([Ganancia], [Ventas netas])
```

### Ventas menos comisiones
Ventas netas (después de descuentos) menos lo que cobran los canales.

```dax
Ventas menos comisiones =
[Ventas netas] - [Comisiones]
```

## Gastos

### Gastos
Lo que salió de la caja (compras de material, pauta, empaques, repuestos).

```dax
Gastos =
SUM(Gastos[valor])
```

### Gasto promedio por mes

```dax
Gasto promedio por mes =
AVERAGEX(VALUES(Calendario[Mes clave]), [Gastos])
```

### Resultado de caja
Ventas menos comisiones, menos gastos de caja del mes.

```dax
Resultado de caja =
[Ventas menos comisiones] - [Gastos]
```

## Costo por pieza

### Material

```dax
Material =
SUM(Piezas[Costo material])
```

### Insumos
Alcohol, guantes, papel y film FEP (resina) o pegante (FDM), repartidos en la placa.

```dax
Insumos =
SUM(Piezas[Costo insumos])
```

### Luz

```dax
Luz =
SUM(Piezas[Costo energía])
```

### Máquina
Desgaste y pago de la impresora por hora de uso.

```dax
Máquina =
SUM(Piezas[Costo máquina])
```

### Mano de obra
Preparar la placa (repartido) y el acabado de cada pieza.

```dax
Mano de obra =
SUM(Piezas[Costo mano de obra])
```

### Fallas
Lo que se pierde por placas que salen mal.

```dax
Fallas =
SUM(Piezas[Costo fallas])
```

### Costo por unidad

```dax
Costo por unidad =
SUM(Piezas[Costo unitario])
```

### % mano de obra
Qué parte del costo es trabajo (preparar y acabar).

```dax
% mano de obra =
DIVIDE([Mano de obra], [Costo por unidad])
```

### % material
Qué parte del costo es resina o filamento.

```dax
% material =
DIVIDE([Material], [Costo por unidad])
```

### Costo promedio
Promedio simple del catálogo.

```dax
Costo promedio =
AVERAGE(Piezas[Costo unitario])
```

## Precio

### Precio de lista

```dax
Precio de lista =
AVERAGE(Piezas[precio_lista])
```

### Ganancia por hora de impresora
Ganancia a precio de lista por cada hora que la pieza ocupa la impresora (placa llena). La impresora es el cuello de botella: esto dice qué conviene imprimir.

```dax
Ganancia por hora de impresora =
DIVIDE(
    SUMX(Piezas, Piezas[precio_lista] - Piezas[Costo unitario]),
    SUMX(Piezas, Piezas[horas_placa] / Piezas[piezas_por_placa])
)
```

### Margen objetivo

```dax
Margen objetivo =
CALCULATE(MAX(Tarifas[valor]), Tarifas[parametro] = "margen_objetivo")
```

### Margen a precio de lista
Margen de cada pieza a su precio de lista, después de la comisión del canal elegido en «Canal para precio» (sin canal: sin comisión).

```dax
Margen a precio de lista =
VAR comision = SELECTEDVALUE('Canal para precio'[Comisión], 0)
RETURN DIVIDE(SUMX(Piezas, Piezas[precio_lista] * (1 - comision) - Piezas[Costo unitario]), SUM(Piezas[precio_lista]))
```

### Precio sugerido
Precio para ganar el margen objetivo después de la comisión, redondeado hacia arriba (igual que costeo.py).

```dax
Precio sugerido =
VAR comision = SELECTEDVALUE('Canal para precio'[Comisión], 0)
VAR paso = CALCULATE(MAX(Tarifas[valor]), Tarifas[parametro] = "redondeo_precio")
VAR exacto = DIVIDE(SELECTEDVALUE(Piezas[Costo unitario]), 1 - [Margen objetivo] - comision)
RETURN IF(HASONEVALUE(Piezas[id_pieza]), CEILING(ROUND(exacto / paso, 9), 1) * paso)
```

## Qué pasa si

### Ajuste de precio

```dax
Ajuste de precio =
SELECTEDVALUE('Ajuste de precio'[Ajuste de precio %], 0) / 100
```

### Ajuste de cantidad

```dax
Ajuste de cantidad =
SELECTEDVALUE('Ajuste de cantidad'[Ajuste de cantidad %], 0) / 100
```

### Ventas con ajuste
Ventas del año si el precio y la cantidad cambian según los dos parámetros.

```dax
Ventas con ajuste =
VAR ap = [Ajuste de precio]
VAR ac = [Ajuste de cantidad]
RETURN CALCULATE(
    SUMX(Detalle, Detalle[cantidad] * (1 + ac) * Detalle[precio_unitario] * (1 - Detalle[descuento_pct]) * (1 + ap)),
    Pedidos[estado] = "Entregado"
)
```

### Ganancia con ajuste
Misma cuenta de sql/07_que_pasa_si.sql.

```dax
Ganancia con ajuste =
VAR ap = [Ajuste de precio]
VAR ac = [Ajuste de cantidad]
RETURN CALCULATE(
    SUMX(Detalle,
        Detalle[cantidad] * (1 + ac) * (
            Detalle[precio_unitario] * (1 - Detalle[descuento_pct]) * (1 + ap) * (1 - RELATED(Canales[comision_pct]))
            - RELATED(Piezas[Costo unitario])
        )
    ),
    Pedidos[estado] = "Entregado"
)
```

### Cambio en la ganancia

```dax
Cambio en la ganancia =
[Ganancia con ajuste] - [Ganancia]
```

### Margen con ajuste %

```dax
Margen con ajuste % =
DIVIDE([Ganancia con ajuste], [Ventas con ajuste])
```

## Parámetros «qué pasa si»

Dos tablas hechas con `GENERATESERIES(-30, 30, 5)`: el cambio de precio y el de cantidad, en %.
Si no se elige nada en el segmentador, las medidas usan 0 % (el año como fue).

## Power Query: costo por pieza (consulta `Piezas`)

```powerquery
let
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
    SinMarca
```
