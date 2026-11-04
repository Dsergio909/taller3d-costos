# Diccionario de datos

Los 7 CSV de `datos/` (ficticios) y los de `datos_reales/` (privados) tienen las mismas columnas. Todos terminan en `origen_datos`: `ficticio` en el repo, `real` en tu PC. `scripts/revisar_datos.py` revisa estas reglas.

Montos en pesos colombianos (COP). Decimales con punto. Fechas AAAA-MM-DD.

## tarifas.csv · una fila por tarifa
| Columna | Qué es |
|---|---|
| `parametro` | Nombre de la tarifa (único). Ver la lista abajo |
| `valor` | Número. Las fracciones van de 0 a 1: `0.4` = 40 % |
| `unidad` | COP/L, COP/kg, W, min, fracción… |
| `aplica_a` | Resina, FDM o Ambas |
| `descripcion` | Qué significa, en una frase |

Tarifas que usa la fórmula de costo:
- **Resina:** `resina_precio_litro`, `resina_soportes_pct`, `alcohol_ml_por_placa`, `alcohol_precio_litro`, `guantes_pares_por_placa`, `guantes_precio_par`, `papel_por_placa`, `fep_precio`, `fep_placas_vida`, `resina_potencia_w`, `resina_maquina_hora`, `resina_tasa_fallas`.
- **FDM:** `filamento_precio_kg`, `fdm_purga_pct`, `fdm_insumos_por_placa`, `fdm_potencia_w`, `fdm_maquina_hora`, `fdm_tasa_fallas`.
- **Las dos:** `energia_precio_kwh`, `mano_obra_hora`, `preparacion_min_por_placa`.
- **Precio y cotizador:** `margen_objetivo`, `redondeo_precio`, `minutos_acabado_a_medida`.

## canales.csv · una fila por canal de venta
| Columna | Qué es |
|---|---|
| `canal` | TikTok, Instagram, WhatsApp (único) |
| `comision_pct` | Lo que cobra el canal sobre la venta, en fracción (`0.10` = 10 %) |
| `descripcion` | De dónde sale la comisión |

## piezas.csv · el catálogo
| Columna | Qué es |
|---|---|
| `id_pieza` | Código único (R = resina, F = FDM) |
| `nombre`, `categoria` | Nombre y grupo |
| `tecnologia` | `Resina` o `FDM` |
| `material_cantidad` | ml de resina o gramos de filamento de **una** pieza, sin soportes ni purga |
| `horas_placa` | Horas que tarda la placa completa |
| `piezas_por_placa` | Cuántas caben en una placa (en resina, la placa llena tarda casi lo mismo que una pieza) |
| `minutos_acabado` | Trabajo a mano por pieza: lavar, curar, quitar soportes, lijar |
| `precio_lista` | Precio de venta antes de descuentos |

## clientes.csv
| Columna | Qué es |
|---|---|
| `id_cliente` | Código (`CLI-001`). Sin nombres, teléfonos ni correos |
| `ciudad` | Solo la ciudad |

## pedidos.csv · una fila por pedido
| Columna | Qué es |
|---|---|
| `id_pedido` | Código único |
| `fecha` | Día del pedido |
| `canal` | Debe existir en `canales.csv` |
| `id_cliente` | Debe existir en `clientes.csv` |
| `estado` | `Entregado`, `Cancelado` o `Devuelto`. Ventas, costos y ganancia cuentan solo los entregados |

## pedido_detalle.csv · una fila por pieza dentro de un pedido
| Columna | Qué es |
|---|---|
| `id_pedido`, `linea` | Pedido y número de línea (juntos son únicos) |
| `id_pieza` | Debe existir en `piezas.csv` |
| `cantidad` | Entero mayor que 0 |
| `precio_unitario` | Precio cobrado por unidad, antes del descuento |
| `descuento_pct` | Fracción (`0.15` = 15 %) |

## gastos.csv · salidas de caja
| Columna | Qué es |
|---|---|
| `id_gasto` | Código único |
| `fecha` | Día del gasto |
| `categoria` | Materiales, Insumos, Energía, Repuestos, Publicidad, Empaques, Herramientas |
| `concepto` | Detalle |
| `valor` | Monto pagado |

Ojo: los gastos son lo que salió de la caja (la resina se compra por litro, el filamento por kilo). No es lo mismo que el costo por pieza, que reparte el material, el desgaste y el trabajo entre las piezas.

## costo_por_pieza.csv (solo en `datos/`)
El costo de cada pieza ya calculado por `scripts/costeo.py`, por componente. Sirve de referencia para comprobar el tablero; en tus datos reales no hace falta.
