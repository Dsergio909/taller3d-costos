# Resultados de las consultas SQL

Generado con `python scripts/cargar_sqlite.py --md docs/resultados_sql.md`.
Datos: taller ficticio (`datos/`). Ninguna cifra es de un taller real.

## 01 · ¿Cuánto cuesta de verdad cada pieza?
`sql/01_costo_por_pieza.sql`

| id_pieza | nombre | tecnologia | costo_unitario | pct_material | pct_mano_obra | precio_lista |
|---|---|---|---|---|---|---|
| R05 | Busto 12 cm | Resina | 52,611 | 29.7 | 35.6 | 120,000 |
| R04 | Figura 10 cm | Resina | 29,889 | 29.4 | 39.7 | 90,000 |
| F05 | Lámpara (base) | FDM | 28,421 | 46.4 | 30.8 | 70,000 |
| F04 | Organizador de escritorio | FDM | 27,263 | 60.5 | 18.3 | 45,000 |
| F09 | Caja con tapa | FDM | 19,632 | 50.4 | 25.5 | 35,000 |
| F08 | Repuesto a medida | FDM | 16,289 | 16.9 | 69.1 | 20,000 |
| F06 | Figura multicolor | FDM | 15,632 | 35.2 | 40.0 | 30,000 |
| F02 | Maceta pequeña | FDM | 11,526 | 57.3 | 27.1 | 25,000 |
| F03 | Soporte de celular | FDM | 7,763 | 49.6 | 33.8 | 18,000 |
| R03 | Miniatura 32 mm | Resina | 5,467 | 21.4 | 51.4 | 25,000 |
| R08 | Llavero detallado | Resina | 4,163 | 18.7 | 54.0 | 14,000 |
| R07 | Anillo | Resina | 2,506 | 11.7 | 57.4 | 18,000 |
| R06 | Dije | Resina | 2,460 | 15.9 | 56.9 | 12,000 |
| R02 | Aretes (par) | Resina | 2,133 | 9.1 | 64.5 | 15,000 |
| F07 | Imán de nevera | FDM | 1,818 | 48.4 | 40.4 | 6,000 |
| F01 | Llavero | FDM | 1,679 | 39.3 | 48.4 | 8,000 |
| R01 | Ficha de juego | Resina | 1,496 | 15.6 | 56.4 | 6,000 |

## 02 · Resina frente a FDM: ¿en qué se va la plata en cada tecnología?
`sql/02_resina_vs_fdm.sql`

| tecnologia | piezas_en_catalogo | costo_promedio | pct_material | pct_insumos | pct_luz_y_maquina | pct_mano_obra | pct_fallas | margen_bruto_promedio_pct |
|---|---|---|---|---|---|---|---|---|
| Resina | 8 | 12,591 | 27.2 | 17.9 | 4.5 | 40.5 | 10.0 | 74.7 |
| FDM | 9 | 14,447 | 46.0 | 2.4 | 13.1 | 33.5 | 5.0 | 52.1 |

## 03 · Precio y margen por pieza y por canal
`sql/03_precio_y_margen.sql`

| id_pieza | nombre | tecnologia | canal | precio_lista | costo_unitario | margen_pct | precio_sugerido | puesto_de_menor_margen |
|---|---|---|---|---|---|---|---|---|
| F08 | Repuesto a medida | FDM | Instagram | 20,000 | 16,289 | 15.6 | 29,000 | 1 |
| F04 | Organizador de escritorio | FDM | Instagram | 45,000 | 27,263 | 36.4 | 48,000 | 2 |
| F09 | Caja con tapa | FDM | Instagram | 35,000 | 19,632 | 40.9 | 34,500 | 3 |
| F06 | Figura multicolor | FDM | Instagram | 30,000 | 15,632 | 44.9 | 27,500 | 4 |
| F02 | Maceta pequeña | FDM | Instagram | 25,000 | 11,526 | 50.9 | 20,500 | 5 |
| R05 | Busto 12 cm | Resina | Instagram | 120,000 | 52,611 | 53.2 | 92,500 | 6 |
| F03 | Soporte de celular | FDM | Instagram | 18,000 | 7,763 | 53.9 | 14,000 | 7 |
| F05 | Lámpara (base) | FDM | Instagram | 70,000 | 28,421 | 56.4 | 50,000 | 8 |
| R04 | Figura 10 cm | Resina | Instagram | 90,000 | 29,889 | 63.8 | 52,500 | 9 |
| F07 | Imán de nevera | FDM | Instagram | 6,000 | 1,818 | 66.7 | 3,500 | 10 |
| R08 | Llavero detallado | Resina | Instagram | 14,000 | 4,163 | 67.3 | 7,500 | 11 |
| R01 | Ficha de juego | Resina | Instagram | 6,000 | 1,496 | 72.1 | 3,000 | 12 |
| R03 | Miniatura 32 mm | Resina | Instagram | 25,000 | 5,467 | 75.1 | 10,000 | 13 |
| F01 | Llavero | FDM | Instagram | 8,000 | 1,679 | 76.0 | 3,000 | 14 |
| R06 | Dije | Resina | Instagram | 12,000 | 2,460 | 76.5 | 4,500 | 15 |
| R02 | Aretes (par) | Resina | Instagram | 15,000 | 2,133 | 82.8 | 4,000 | 16 |
| R07 | Anillo | Resina | Instagram | 18,000 | 2,506 | 83.1 | 4,500 | 17 |
| F08 | Repuesto a medida | FDM | TikTok | 20,000 | 16,289 | 8.6 | 33,000 | 1 |
| F04 | Organizador de escritorio | FDM | TikTok | 45,000 | 27,263 | 29.4 | 55,000 | 2 |
| F09 | Caja con tapa | FDM | TikTok | 35,000 | 19,632 | 33.9 | 39,500 | 3 |
| F06 | Figura multicolor | FDM | TikTok | 30,000 | 15,632 | 37.9 | 31,500 | 4 |
| F02 | Maceta pequeña | FDM | TikTok | 25,000 | 11,526 | 43.9 | 23,500 | 5 |
| R05 | Busto 12 cm | Resina | TikTok | 120,000 | 52,611 | 46.2 | 105,500 | 6 |
| F03 | Soporte de celular | FDM | TikTok | 18,000 | 7,763 | 46.9 | 16,000 | 7 |
| F05 | Lámpara (base) | FDM | TikTok | 70,000 | 28,421 | 49.4 | 57,000 | 8 |
| R04 | Figura 10 cm | Resina | TikTok | 90,000 | 29,889 | 56.8 | 60,000 | 9 |
| F07 | Imán de nevera | FDM | TikTok | 6,000 | 1,818 | 59.7 | 4,000 | 10 |
| R08 | Llavero detallado | Resina | TikTok | 14,000 | 4,163 | 60.3 | 8,500 | 11 |
| R01 | Ficha de juego | Resina | TikTok | 6,000 | 1,496 | 65.1 | 3,000 | 12 |
| R03 | Miniatura 32 mm | Resina | TikTok | 25,000 | 5,467 | 68.1 | 11,000 | 13 |
| F01 | Llavero | FDM | TikTok | 8,000 | 1,679 | 69.0 | 3,500 | 14 |
| R06 | Dije | Resina | TikTok | 12,000 | 2,460 | 69.5 | 5,000 | 15 |
| R02 | Aretes (par) | Resina | TikTok | 15,000 | 2,133 | 75.8 | 4,500 | 16 |
| R07 | Anillo | Resina | TikTok | 18,000 | 2,506 | 76.1 | 5,500 | 17 |
| F08 | Repuesto a medida | FDM | WhatsApp | 20,000 | 16,289 | 18.6 | 27,500 | 1 |
| F04 | Organizador de escritorio | FDM | WhatsApp | 45,000 | 27,263 | 39.4 | 45,500 | 2 |
| F09 | Caja con tapa | FDM | WhatsApp | 35,000 | 19,632 | 43.9 | 33,000 | 3 |
| F06 | Figura multicolor | FDM | WhatsApp | 30,000 | 15,632 | 47.9 | 26,500 | 4 |
| F02 | Maceta pequeña | FDM | WhatsApp | 25,000 | 11,526 | 53.9 | 19,500 | 5 |
| R05 | Busto 12 cm | Resina | WhatsApp | 120,000 | 52,611 | 56.2 | 88,000 | 6 |
| F03 | Soporte de celular | FDM | WhatsApp | 18,000 | 7,763 | 56.9 | 13,000 | 7 |
| F05 | Lámpara (base) | FDM | WhatsApp | 70,000 | 28,421 | 59.4 | 47,500 | 8 |
| R04 | Figura 10 cm | Resina | WhatsApp | 90,000 | 29,889 | 66.8 | 50,000 | 9 |
| F07 | Imán de nevera | FDM | WhatsApp | 6,000 | 1,818 | 69.7 | 3,500 | 10 |
| R08 | Llavero detallado | Resina | WhatsApp | 14,000 | 4,163 | 70.3 | 7,000 | 11 |
| R01 | Ficha de juego | Resina | WhatsApp | 6,000 | 1,496 | 75.1 | 2,500 | 12 |
| R03 | Miniatura 32 mm | Resina | WhatsApp | 25,000 | 5,467 | 78.1 | 9,500 | 13 |
| F01 | Llavero | FDM | WhatsApp | 8,000 | 1,679 | 79.0 | 3,000 | 14 |
| R06 | Dije | Resina | WhatsApp | 12,000 | 2,460 | 79.5 | 4,500 | 15 |
| R02 | Aretes (par) | Resina | WhatsApp | 15,000 | 2,133 | 85.8 | 4,000 | 16 |
| R07 | Anillo | Resina | WhatsApp | 18,000 | 2,506 | 86.1 | 4,500 | 17 |

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
| WhatsApp | 10,982,100 | 5,149,258 | 0.0 | 5,832,842 | 53.1 |
| Instagram | 8,650,000 | 2,947,912 | 259,500 | 5,442,588 | 62.9 |
| TikTok | 6,022,650 | 1,737,485 | 602,265 | 3,682,900 | 61.2 |

## 07 · ¿Qué pasa si cambio el precio y vendo más o menos?
`sql/07_que_pasa_si.sql`

| escenario | ventas | ganancia |
|---|---|---|
| Subo 10 % y vendo igual | 28,220,225 | 17,437,629 |
| Subo 10 % y vendo 10 % menos | 25,398,203 | 15,693,866 |
| Bajo 10 % y vendo 20 % más | 27,707,130 | 14,974,838 |
| Como va | 25,654,750 | 14,958,330 |
| Bajo 10 % y vendo 10 % más | 25,398,203 | 13,726,935 |

## 08 · Mes a mes: ventas, gastos de caja y cambio contra el mes anterior (LAG)
`sql/08_resultado_por_mes.sql`

| mes | pedidos | ventas_sin_comision | gastos | resultado_caja | pct_ventas_vs_mes_anterior |
|---|---|---|---|---|---|
| 2025-01 | 28 | 1,205,290 | 587,000 | 618,290 | — |
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

## 09 · ¿Qué pieza deja más plata por cada hora de impresora?
`sql/09_ganancia_por_hora_de_impresora.sql`

| id_pieza | nombre | tecnologia | ganancia_por_pieza | minutos_de_impresora | ganancia_por_hora | puesto_por_hora | puesto_por_pieza | puesto_en_su_impresora |
|---|---|---|---|---|---|---|---|---|
| R02 | Aretes (par) | Resina | 12,867 | 2.0 | 386,000 | 1 | 10 | 1 |
| R07 | Anillo | Resina | 15,494 | 3.0 | 309,889 | 2 | 6 | 2 |
| R06 | Dije | Resina | 9,540 | 2.9 | 198,750 | 3 | 13 | 3 |
| R01 | Ficha de juego | Resina | 4,504 | 2.3 | 120,104 | 4 | 15 | 4 |
| R08 | Llavero detallado | Resina | 9,837 | 6.0 | 98,370 | 5 | 12 | 5 |
| R03 | Miniatura 32 mm | Resina | 19,533 | 12.5 | 93,760 | 6 | 4 | 6 |
| F01 | Llavero | FDM | 6,321 | 7.5 | 50,565 | 7 | 14 | 1 |
| F07 | Imán de nevera | FDM | 4,182 | 7.5 | 33,458 | 8 | 16 | 2 |
| R04 | Figura 10 cm | Resina | 60,111 | 150.0 | 24,044 | 9 | 2 | 7 |
| R05 | Busto 12 cm | Resina | 67,389 | 360.0 | 11,231 | 10 | 1 | 8 |
| F03 | Soporte de celular | FDM | 10,237 | 60.0 | 10,237 | 11 | 11 | 3 |
| F02 | Maceta pequeña | FDM | 13,474 | 90.0 | 8,982 | 12 | 9 | 4 |
| F05 | Lámpara (base) | FDM | 41,579 | 420.0 | 5,940 | 13 | 3 | 5 |
| F06 | Figura multicolor | FDM | 14,368 | 240.0 | 3,592 | 14 | 8 | 6 |
| F09 | Caja con tapa | FDM | 15,368 | 300.0 | 3,074 | 15 | 7 | 7 |
| F04 | Organizador de escritorio | FDM | 17,737 | 360.0 | 2,956 | 16 | 5 | 8 |
| F08 | Repuesto a medida | FDM | 3,711 | 90.0 | 2,474 | 17 | 17 | 9 |

## 10 · Cohortes: de los clientes nuevos de cada trimestre, ¿cuántos volvieron a comprar?
`sql/10_cohortes_de_clientes.sql`

| cohorte | clientes_nuevos | con_90_dias_para_mirar | volvieron_en_90_dias | pct_volvieron_en_90_dias | dias_promedio_si_volvio_en_90 |
|---|---|---|---|---|---|
| 2025-T1 | 77 | 77 | 31 | 40.3 | 50.0 |
| 2025-T2 | 72 | 72 | 21 | 29.2 | 43.0 |
| 2025-T3 | 53 | 53 | 13 | 24.5 | 44.0 |
| 2025-T4 | 50 | 1 | 0 | 0.0 | — |

