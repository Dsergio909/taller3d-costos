# Revisión por vueltas

Cómo se construyó y se revisó este repo, con números. Método: construir lo mínimo de punta a punta, 3 vueltas buscando errores (con revisión de privacidad en cada una), 3 vueltas mejorando y una de facilidad y diseño.

## Fase 0 · Construcción (4-nov-2026)
- Datos ficticios con semilla fija: 17 piezas, 549 pedidos, 718 líneas, 77 gastos, 320 clientes, 24 tarifas, 3 canales. 8 CSV, todos con `origen_datos = ficticio`.
- Fórmula de costo en 4 lugares: Python (`scripts/costeo.py`), SQL (`sql/01`), JavaScript del flujo (`flujos/costeo.js`) y Power Query (consulta `Piezas`).
- 8 consultas SQL en SQLite. Tablero de Power BI de 4 páginas generado como proyecto PBIP (TMDL + PBIR) por `scripts/armar_powerbi.py`: 35 medidas DAX, 2 parámetros «qué pasa si».
- Flujo de n8n de 20 nodos más el flujo de errores de 4 nodos, generados por `scripts/armar_flujo.py`.
- Errores encontrados al construir y ya arreglados:
  1. **SQL redondeaba hacia abajo el precio sugerido.** El truco `-CAST(-x AS INTEGER)` da el piso, no el techo, porque SQLite corta hacia cero. Repuesto a medida por Instagram daba $28.500 en vez de $29.000. Lo encontró la prueba que compara Python con SQL.
  2. **Ruido de coma flotante en el techo del precio.** Python, JS y SQL podían diferir en 500 pesos en casos límite. Ahora los tres redondean a 9 decimales antes del techo.
  3. **El segmentador de canal del precio sugerido filtraba las ventas.** La ganancia del año mostraba solo la de Instagram ($5.458.143 en vez de $15.012.331) y faltaban 7 piezas en el gráfico. Se cambió por una tabla desconectada (`Canal para precio`).
  4. **Los parámetros «qué pasa si» arrancaban en −30 %** por la selección única estricta. Ahora arrancan sin selección (0 %) o con el escenario guardado.
  5. **Identificadores repetidos en el modelo:** 8 columnas con el mismo `lineageTag` en tablas distintas. Ahora incluyen el nombre de la tabla.
  6. Gastos acumulados (`sql/04`) se ordenaban por categoría dentro del mes; ahora es el acumulado del año por mes.
- Comprobado en Power BI Desktop (en pantalla) contra el SQL: 549 pedidos, ventas netas $25.654.750, ganancia $15.012.331, escenario +10 % precio y −10 % cantidad $15.742.466, clientes que vuelven 42,0 / 26,0 / 25,9 %. Todo cuadra.

## Vuelta 1 de errores (4-nov-2026)
| # | Qué revisé | Qué encontré | Arreglo |
|---|---|---|---|
| 1 | Cifras del README contra los datos | Nada las comprobaba; el conteo de pruebas estaba viejo (41, eran 49) | Prueba nueva `test_readme.py`: recalcula 30 cifras desde los datos y revisa que estén en español y en inglés |
| 2 | Diferencia del «qué pasa si» | +$730.136 (tablero, sin redondear) contra +$730.135 (resta de cifras redondeadas) | La prueba calcula sin redondear, igual que el tablero |
| 3 | Correr «como un desconocido» (clon limpio) | Pruebas 49/49. Regenerar los flujos en Windows dejaba los archivos «cambiados» (finales de línea CRLF) | `armar_flujo.py` y `cargar_sqlite.py` escriben siempre LF |
| 4 | Traducción al inglés hecha por Ollama (qwen3.5:4b, 13 secciones, 76 s) | 14 errores, 3 de sentido: «next year's profit» (es la del año), «more revenue» (es más ganancia), «doesn't just reply» (es «no responde solo»). También «weight for weight», «Update» en vez de «Refresh» y montos sin COP | Corregidos a mano; la prueba de cifras cubre también el inglés |
| 5 | Privacidad: búsqueda de marcas, máquinas, productos, rutas, IP, correo y teléfono | Nada del taller real. Las tarifas ficticias no coinciden con ninguna real. El nombre «Sergio» aparece en 2 nodos del flujo | Se deja para la vuelta de mejoras (nombre genérico) |
| 6 | Power BI abierto mientras el script regeneraba el PBIP | Power BI detectó el cambio y ofreció guardar encima | Se cerró sin guardar; regla anotada en `CLAUDE.md` |

Pruebas al cerrar la vuelta: 49 de 49.

## Uso de IA delegada
| Cuándo | Herramienta | Qué hizo | Qué tuve que corregir |
|---|---|---|---|
| Vuelta 1 | Ollama qwen3.5:4b (local; Antigravity estaba ocupado y Power BI abierto en otro chat, por eso no el 9b) | Traducción del README al inglés, sección por sección | 14 errores, 3 de sentido (ver vuelta 1) |
