# Resultados de las consultas SQL

Generado con `python scripts/cargar_sqlite.py --md docs/resultados_sql.md`.
Datos: taller ficticio (`datos/`). Ninguna cifra es de un taller real.

## 01 · ¿Cuánto cuesta de verdad cada pieza?
`sql/01_costo_por_pieza.sql`

| id_pieza | nombre | tecnologia | costo_unitario | pct_material | pct_mano_obra | precio_lista |
|---|---|---|---|---|---|---|
| R05 | Busto 12 cm | Resina | 52,085 | 30.0 | 36.0 | 120,000 |
| R04 | Figura 10 cm | Resina | 29,590 | 29.7 | 40.1 | 90,000 |
| F05 | Lámpara (base) | FDM | 28,350 | 46.6 | 30.9 | 70,000 |
| F04 | Organizador de escritorio | FDM | 27,195 | 60.7 | 18.4 | 45,000 |
| F09 | Caja con tapa | FDM | 19,583 | 50.6 | 25.5 | 35,000 |
| F08 | Repuesto a medida | FDM | 16,249 | 16.9 | 69.2 | 20,000 |
| F06 | Figura multicolor | FDM | 15,593 | 35.3 | 40.1 | 30,000 |
| F02 | Maceta pequeña | FDM | 11,498 | 57.4 | 27.2 | 25,000 |
| F03 | Soporte de celular | FDM | 7,744 | 49.7 | 33.9 | 18,000 |
| R03 | Miniatura 32 mm | Resina | 5,412 | 21.6 | 52.0 | 25,000 |
| R08 | Llavero detallado | Resina | 4,121 | 18.9 | 54.6 | 14,000 |
| R07 | Anillo | Resina | 2,481 | 11.8 | 58.0 | 18,000 |
| R06 | Dije | Resina | 2,435 | 16.0 | 57.5 | 12,000 |
| R02 | Aretes (par) | Resina | 2,112 | 9.2 | 65.1 | 15,000 |
| F07 | Imán de nevera | FDM | 1,813 | 48.5 | 40.5 | 6,000 |
| F01 | Llavero | FDM | 1,675 | 39.4 | 48.5 | 8,000 |
| R01 | Ficha de juego | Resina | 1,481 | 15.8 | 57.0 | 6,000 |

## 02 · Resina frente a FDM: ¿en qué se va la plata en cada tecnología?
`sql/02_resina_vs_fdm.sql`

| tecnologia | piezas_en_catalogo | costo_promedio | pct_material | pct_insumos | pct_luz_y_maquina | pct_mano_obra | pct_fallas | margen_bruto_promedio_pct |
|---|---|---|---|---|---|---|---|---|
| Resina | 8 | 12,465 | 27.5 | 18.0 | 4.5 | 40.9 | 9.1 | 75.0 |
| FDM | 9 | 14,411 | 46.1 | 2.4 | 13.2 | 33.6 | 4.8 | 52.2 |

## 03 · Precio y margen por pieza y por canal
`sql/03_precio_y_margen.sql`

| id_pieza | nombre | tecnologia | canal | precio_lista | costo_unitario | margen_pct | precio_sugerido | puesto_de_menor_margen |
|---|---|---|---|---|---|---|---|---|
| F08 | Repuesto a medida | FDM | Instagram | 20,000 | 16,249 | 15.8 | 29,000 | 1 |
| F04 | Organizador de escritorio | FDM | Instagram | 45,000 | 27,195 | 36.6 | 48,000 | 2 |
| F09 | Caja con tapa | FDM | Instagram | 35,000 | 19,583 | 41.0 | 34,500 | 3 |
| F06 | Figura multicolor | FDM | Instagram | 30,000 | 15,593 | 45.0 | 27,500 | 4 |
| F02 | Maceta pequeña | FDM | Instagram | 25,000 | 11,498 | 51.0 | 20,500 | 5 |
| R05 | Busto 12 cm | Resina | Instagram | 120,000 | 52,085 | 53.6 | 91,500 | 6 |
| F03 | Soporte de celular | FDM | Instagram | 18,000 | 7,744 | 54.0 | 14,000 | 7 |
| F05 | Lámpara (base) | FDM | Instagram | 70,000 | 28,350 | 56.5 | 50,000 | 8 |
| R04 | Figura 10 cm | Resina | Instagram | 90,000 | 29,590 | 64.1 | 52,000 | 9 |
| F07 | Imán de nevera | FDM | Instagram | 6,000 | 1,813 | 66.8 | 3,500 | 10 |
| R08 | Llavero detallado | Resina | Instagram | 14,000 | 4,121 | 67.6 | 7,500 | 11 |
| R01 | Ficha de juego | Resina | Instagram | 6,000 | 1,481 | 72.3 | 3,000 | 12 |
| R03 | Miniatura 32 mm | Resina | Instagram | 25,000 | 5,412 | 75.4 | 9,500 | 13 |
| F01 | Llavero | FDM | Instagram | 8,000 | 1,675 | 76.1 | 3,000 | 14 |
| R06 | Dije | Resina | Instagram | 12,000 | 2,435 | 76.7 | 4,500 | 15 |
| R02 | Aretes (par) | Resina | Instagram | 15,000 | 2,112 | 82.9 | 4,000 | 16 |
| R07 | Anillo | Resina | Instagram | 18,000 | 2,481 | 83.2 | 4,500 | 17 |
| F08 | Repuesto a medida | FDM | TikTok | 20,000 | 16,249 | 8.8 | 32,500 | 1 |
| F04 | Organizador de escritorio | FDM | TikTok | 45,000 | 27,195 | 29.6 | 54,500 | 2 |
| F09 | Caja con tapa | FDM | TikTok | 35,000 | 19,583 | 34.1 | 39,500 | 3 |
| F06 | Figura multicolor | FDM | TikTok | 30,000 | 15,593 | 38.0 | 31,500 | 4 |
| F02 | Maceta pequeña | FDM | TikTok | 25,000 | 11,498 | 44.0 | 23,000 | 5 |
| R05 | Busto 12 cm | Resina | TikTok | 120,000 | 52,085 | 46.6 | 104,500 | 6 |
| F03 | Soporte de celular | FDM | TikTok | 18,000 | 7,744 | 47.0 | 15,500 | 7 |
| F05 | Lámpara (base) | FDM | TikTok | 70,000 | 28,350 | 49.5 | 57,000 | 8 |
| R04 | Figura 10 cm | Resina | TikTok | 90,000 | 29,590 | 57.1 | 59,500 | 9 |
| F07 | Imán de nevera | FDM | TikTok | 6,000 | 1,813 | 59.8 | 4,000 | 10 |
| R08 | Llavero detallado | Resina | TikTok | 14,000 | 4,121 | 60.6 | 8,500 | 11 |
| R01 | Ficha de juego | Resina | TikTok | 6,000 | 1,481 | 65.3 | 3,000 | 12 |
| R03 | Miniatura 32 mm | Resina | TikTok | 25,000 | 5,412 | 68.4 | 11,000 | 13 |
| F01 | Llavero | FDM | TikTok | 8,000 | 1,675 | 69.1 | 3,500 | 14 |
| R06 | Dije | Resina | TikTok | 12,000 | 2,435 | 69.7 | 5,000 | 15 |
| R02 | Aretes (par) | Resina | TikTok | 15,000 | 2,112 | 75.9 | 4,500 | 16 |
| R07 | Anillo | Resina | TikTok | 18,000 | 2,481 | 76.2 | 5,000 | 17 |
| F08 | Repuesto a medida | FDM | WhatsApp | 20,000 | 16,249 | 18.8 | 27,500 | 1 |
| F04 | Organizador de escritorio | FDM | WhatsApp | 45,000 | 27,195 | 39.6 | 45,500 | 2 |
| F09 | Caja con tapa | FDM | WhatsApp | 35,000 | 19,583 | 44.0 | 33,000 | 3 |
| F06 | Figura multicolor | FDM | WhatsApp | 30,000 | 15,593 | 48.0 | 26,000 | 4 |
| F02 | Maceta pequeña | FDM | WhatsApp | 25,000 | 11,498 | 54.0 | 19,500 | 5 |
| R05 | Busto 12 cm | Resina | WhatsApp | 120,000 | 52,085 | 56.6 | 87,000 | 6 |
| F03 | Soporte de celular | FDM | WhatsApp | 18,000 | 7,744 | 57.0 | 13,000 | 7 |
| F05 | Lámpara (base) | FDM | WhatsApp | 70,000 | 28,350 | 59.5 | 47,500 | 8 |
| R04 | Figura 10 cm | Resina | WhatsApp | 90,000 | 29,590 | 67.1 | 49,500 | 9 |
| F07 | Imán de nevera | FDM | WhatsApp | 6,000 | 1,813 | 69.8 | 3,500 | 10 |
| R08 | Llavero detallado | Resina | WhatsApp | 14,000 | 4,121 | 70.6 | 7,000 | 11 |
| R01 | Ficha de juego | Resina | WhatsApp | 6,000 | 1,481 | 75.3 | 2,500 | 12 |
| R03 | Miniatura 32 mm | Resina | WhatsApp | 25,000 | 5,412 | 78.4 | 9,500 | 13 |
| F01 | Llavero | FDM | WhatsApp | 8,000 | 1,675 | 79.1 | 3,000 | 14 |
| R06 | Dije | Resina | WhatsApp | 12,000 | 2,435 | 79.7 | 4,500 | 15 |
| R02 | Aretes (par) | Resina | WhatsApp | 15,000 | 2,112 | 85.9 | 4,000 | 16 |
| R07 | Anillo | Resina | WhatsApp | 18,000 | 2,481 | 86.2 | 4,500 | 17 |

## 04 · Gastos del taller por mes y por categoría
`sql/04_gastos_por_mes.sql`

| mes | categoria | gasto | pct_del_mes | acumulado_categoria | acumulado_año |
|---|---|---|---|---|---|
| 2025-01 | Materiales | 350,000 | 59.6 | 350,000 | 587,000 |
| 2025-01 | Publicidad | 150,000 | 25.6 | 150,000 | 587,000 |
| 2025-01 | Empaques | 42,000 | 7.2 | 42,000 | 587,000 |
| 2025-01 | Insumos | 36,000 | 6.1 | 36,000 | 587,000 |
| 2025-01 | Energía | 9,000 | 1.5 | 9,000 | 587,000 |
| 2025-02 | Materiales | 350,000 | 60.2 | 700,000 | 1,168,500 |
| 2025-02 | Publicidad | 150,000 | 25.8 | 300,000 | 1,168,500 |
| 2025-02 | Empaques | 46,500 | 8.0 | 88,500 | 1,168,500 |
| 2025-02 | Insumos | 27,000 | 4.6 | 63,000 | 1,168,500 |
| 2025-02 | Energía | 8,000 | 1.4 | 17,000 | 1,168,500 |
| 2025-03 | Materiales | 350,000 | 48.1 | 1,050,000 | 1,895,500 |
| 2025-03 | Publicidad | 150,000 | 20.6 | 450,000 | 1,895,500 |
| 2025-03 | Herramientas | 120,000 | 16.5 | 120,000 | 1,895,500 |
| 2025-03 | Empaques | 54,000 | 7.4 | 142,500 | 1,895,500 |
| 2025-03 | Insumos | 45,000 | 6.2 | 108,000 | 1,895,500 |
| 2025-03 | Energía | 8,000 | 1.1 | 25,000 | 1,895,500 |
| 2025-04 | Materiales | 450,000 | 58.3 | 1,500,000 | 2,667,500 |
| 2025-04 | Publicidad | 150,000 | 19.4 | 600,000 | 2,667,500 |
| 2025-04 | Repuestos | 80,000 | 10.4 | 80,000 | 2,667,500 |
| 2025-04 | Empaques | 51,000 | 6.6 | 193,500 | 2,667,500 |
| 2025-04 | Insumos | 27,000 | 3.5 | 135,000 | 2,667,500 |
| 2025-04 | Energía | 14,000 | 1.8 | 39,000 | 2,667,500 |
| 2025-05 | Materiales | 450,000 | 58.9 | 1,950,000 | 3,431,000 |
| 2025-05 | Publicidad | 150,000 | 19.6 | 750,000 | 3,431,000 |
| 2025-05 | Empaques | 73,500 | 9.6 | 267,000 | 3,431,000 |
| 2025-05 | Insumos | 72,000 | 9.4 | 207,000 | 3,431,000 |
| 2025-05 | Energía | 18,000 | 2.4 | 57,000 | 3,431,000 |
| 2025-06 | Materiales | 450,000 | 62.3 | 2,400,000 | 4,153,000 |
| 2025-06 | Publicidad | 150,000 | 20.8 | 900,000 | 4,153,000 |
| 2025-06 | Empaques | 60,000 | 8.3 | 327,000 | 4,153,000 |
| 2025-06 | Insumos | 45,000 | 6.2 | 252,000 | 4,153,000 |
| 2025-06 | Energía | 17,000 | 2.4 | 74,000 | 4,153,000 |
| 2025-07 | Materiales | 450,000 | 59.8 | 2,850,000 | 4,906,000 |
| 2025-07 | Publicidad | 150,000 | 19.9 | 1,050,000 | 4,906,000 |
| 2025-07 | Insumos | 72,000 | 9.6 | 324,000 | 4,906,000 |
| 2025-07 | Empaques | 60,000 | 8.0 | 387,000 | 4,906,000 |
| 2025-07 | Energía | 21,000 | 2.8 | 95,000 | 4,906,000 |
| 2025-08 | Materiales | 350,000 | 51.4 | 3,200,000 | 5,587,500 |
| 2025-08 | Publicidad | 150,000 | 22.0 | 1,200,000 | 5,587,500 |
| 2025-08 | Empaques | 61,500 | 9.0 | 448,500 | 5,587,500 |
| 2025-08 | Herramientas | 60,000 | 8.8 | 180,000 | 5,587,500 |
| 2025-08 | Insumos | 45,000 | 6.6 | 369,000 | 5,587,500 |
| 2025-08 | Energía | 15,000 | 2.2 | 110,000 | 5,587,500 |
| 2025-09 | Materiales | 350,000 | 49.9 | 3,550,000 | 6,289,000 |
| 2025-09 | Publicidad | 150,000 | 21.4 | 1,350,000 | 6,289,000 |
| 2025-09 | Repuestos | 80,000 | 11.4 | 160,000 | 6,289,000 |
| 2025-09 | Empaques | 64,500 | 9.2 | 513,000 | 6,289,000 |
| 2025-09 | Insumos | 45,000 | 6.4 | 414,000 | 6,289,000 |
| 2025-09 | Energía | 12,000 | 1.7 | 122,000 | 6,289,000 |
| 2025-10 | Materiales | 600,000 | 61.7 | 4,150,000 | 7,261,500 |
| 2025-10 | Publicidad | 150,000 | 15.4 | 1,500,000 | 7,261,500 |
| 2025-10 | Insumos | 126,000 | 13.0 | 540,000 | 7,261,500 |
| 2025-10 | Empaques | 73,500 | 7.6 | 586,500 | 7,261,500 |
| 2025-10 | Energía | 23,000 | 2.4 | 145,000 | 7,261,500 |
| 2025-11 | Materiales | 450,000 | 44.8 | 4,600,000 | 8,265,500 |
| 2025-11 | Publicidad | 400,000 | 39.8 | 1,900,000 | 8,265,500 |
| 2025-11 | Empaques | 81,000 | 8.1 | 667,500 | 8,265,500 |
| 2025-11 | Insumos | 54,000 | 5.4 | 594,000 | 8,265,500 |
| 2025-11 | Energía | 19,000 | 1.9 | 164,000 | 8,265,500 |
| 2025-12 | Materiales | 650,000 | 47.9 | 5,250,000 | 9,622,500 |
| 2025-12 | Publicidad | 400,000 | 29.5 | 2,300,000 | 9,622,500 |
| 2025-12 | Empaques | 114,000 | 8.4 | 781,500 | 9,622,500 |
| 2025-12 | Insumos | 99,000 | 7.3 | 693,000 | 9,622,500 |
| 2025-12 | Repuestos | 60,000 | 4.4 | 220,000 | 9,622,500 |
| 2025-12 | Energía | 34,000 | 2.5 | 198,000 | 9,622,500 |

## 05 · Pedidos por canal
`sql/05_pedidos_por_canal.sql`

| canal | pedidos | entregados | pct_cancelado_o_devuelto | unidades | ventas_netas | ticket_promedio | pct_clientes_que_vuelven |
|---|---|---|---|---|---|---|---|
| WhatsApp | 136 | 129 | 5.1 | 315 | 10,982,100 | 85,133 | 42.0 |
| Instagram | 209 | 189 | 9.6 | 304 | 8,650,000 | 45,767 | 26.0 |
| TikTok | 204 | 188 | 7.8 | 648 | 6,022,650 | 32,035 | 25.9 |

## 06 · ¿Cuánto deja cada canal después de costos y comisiones?
`sql/06_ganancia_por_canal.sql`

| canal | ventas_netas | costo_piezas | comision | ganancia | margen_pct |
|---|---|---|---|---|---|
| WhatsApp | 10,982,100 | 5,121,906 | 0.0 | 5,860,194 | 53.4 |
| Instagram | 8,650,000 | 2,932,357 | 259,500 | 5,458,143 | 63.1 |
| TikTok | 6,022,650 | 1,726,390 | 602,265 | 3,693,995 | 61.3 |

## 07 · ¿Qué pasa si cambio el precio y vendo más o menos?
`sql/07_que_pasa_si.sql`

| escenario | ventas | ganancia |
|---|---|---|
| Subo 10 % y vendo igual | 28,220,225 | 17,491,629 |
| Subo 10 % y vendo 10 % menos | 25,398,203 | 15,742,466 |
| Bajo 10 % y vendo 20 % más | 27,707,130 | 15,039,639 |
| Como va | 25,654,750 | 15,012,331 |
| Bajo 10 % y vendo 10 % más | 25,398,203 | 13,786,335 |

## 08 · Mes a mes: ventas, gastos de caja y cambio contra el mes anterior (LAG)
`sql/08_resultado_por_mes.sql`

| mes | pedidos | ventas_sin_comision | gastos | resultado_caja | pct_ventas_vs_mes_anterior |
|---|---|---|---|---|---|
| 2025-01 | 28 | 1,205,290 | 587,000 | 618,290 | None |
| 2025-02 | 30 | 1,195,320 | 581,500 | 613,820 | -0.8 |
| 2025-03 | 36 | 1,495,210 | 727,000 | 768,210 | 25.1 |
| 2025-04 | 34 | 1,378,690 | 772,000 | 606,690 | -7.8 |
| 2025-05 | 46 | 2,209,290 | 763,500 | 1,445,790 | 60.2 |
| 2025-06 | 38 | 2,020,520 | 722,000 | 1,298,520 | -8.5 |
| 2025-07 | 38 | 2,437,500 | 753,000 | 1,684,500 | 20.6 |
| 2025-08 | 41 | 1,783,160 | 681,500 | 1,101,660 | -26.8 |
| 2025-09 | 42 | 1,798,480 | 701,500 | 1,096,980 | 0.9 |
| 2025-10 | 48 | 3,198,470 | 972,500 | 2,225,970 | 77.8 |
| 2025-11 | 52 | 2,222,995 | 1,004,000 | 1,218,995 | -30.5 |
| 2025-12 | 73 | 3,848,060 | 1,357,000 | 2,491,060 | 73.1 |
