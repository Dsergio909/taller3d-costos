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

## Vuelta 2 de errores (4-nov-2026): usar el método con datos reales
La pregunta de esta vuelta: ¿qué se rompe cuando el dueño del taller copia `datos/` a `datos_reales/` y lo edita en Excel?

| # | Qué revisé | Qué encontré | Arreglo |
|---|---|---|---|
| 1 | CSV guardados por Excel en español (punto y coma, coma decimal, fechas dd/mm/aaaa, BOM, CRLF) | `costeo.py` se caía (`KeyError: 'parametro'`); el SQL, Power Query y n8n también esperan coma y punto decimal | `scripts/revisar_datos.py --arreglar`: los 7 CSV de Excel quedan idénticos byte a byte a los originales, y antes guarda copia en `_originales/`. Los lectores de Python ahora toleran el BOM |
| 2 | Errores típicos al editar a mano | Nada los atrapaba: margen escrito «40» en vez de 0,4, tarifa borrada, canal que no existe, columna renombrada, texto en una columna de número | El revisor los detecta con un mensaje claro; con errores no toca ningún archivo |
| 3 | Identificadores repetidos | Un parámetro repetido en `tarifas.csv` hace que Python use el último sin avisar y que Power Query falle | El revisor avisa de claves repetidas en 5 tablas |
| 4 | Privacidad con datos reales presentes | Las pruebas de GitHub no pueden ver `datos_reales/` (no existe allá) | `scripts/revisar_privacidad.py`, solo local: compara piezas, clientes y tarifas reales contra los 121 archivos que se subirían, incluido el `.pbix`. Probado con un `datos_reales/` falso y una fuga plantada: la encontró |
| 5 | Que `datos_reales/` no se cuele en git | Con la carpeta creada, `git status` no la muestra | Ya estaba en `.gitignore`; confirmado |

Pruebas al cerrar la vuelta: 57 de 57 (8 nuevas del revisor de datos).

## Vuelta 3 de errores (4-nov-2026): casos borde y privacidad del historial
| # | Qué revisé | Qué encontré | Arreglo |
|---|---|---|---|
| 1 | Privacidad en **todo el historial de git** (no solo lo actual): 126 archivos de todos los commits | Nada sensible. El único hallazgo es un comentario del esquema SQL que nombra la carpeta `datos_reales/`. Autor de los commits: el correo privado de GitHub (`noreply`) | Nada que arreglar |
| 2 | Control de cifras de la IA con nombres de cliente que traen números | Un cliente «andrea_92» saludado por su nombre hacía descartar un borrador correcto (el «92» contaba como cifra inventada) | Los números del nombre del cliente se permiten; prueba nueva |
| 3 | Segunda opinión externa (Gemini vía Antigravity) sobre fórmula, SQL, DAX y código del flujo | Pendiente: Antigravity estaba en uso por otro chat desde las 3:49 p. m. | Ver «Uso de IA delegada» |
| 4 | Correr el flujo en n8n de verdad | Pendiente del permiso de Sergio para instalar n8n | — |

## Vuelta 1 de mejoras (4-nov-2026): qué valora un reclutador de datos u operaciones
| # | Mejora | Por qué | Resultado |
|---|---|---|---|
| 1 | **Ganancia por hora de impresora** (`sql/09`, medida DAX y columna en la página 1) | La impresora es el cuello de botella: importa cuánto deja cada hora de máquina, no solo el margen % | Aretes de resina $386.640 por hora contra $2.968 del organizador, que deja más por pieza ($17.805). Reemplaza la conclusión 5 del README (la de la luz, más débil) |
| 2 | **Cohortes de clientes** (`sql/10`) con corrección del sesgo de los últimos meses | Muestra SQL avanzado (LEAD, ROW_NUMBER, julianday) y criterio: no comparar cohortes con distinto tiempo para volver | Volvieron en 90 días: T1 40,3 %, T2 29,2 %, T3 24,5 %; T4 sin tiempo suficiente (1 de 50 clientes) |
| 3 | Nombres genéricos en el flujo («Avisar al dueño», «Aprobación del dueño») | Es una plantilla: la puede usar cualquier taller | 0 menciones de nombres propios en el flujo |
| 4 | Diagrama del flujo en SVG generado desde el JSON (`scripts/diagrama_flujo.py`), en dos filas | Las reglas piden el diagrama como imagen; generado no se desactualiza | Prueba nueva que falla si el diagrama queda viejo |
| 5 | Guía corta de Power BI (`docs/guia_power_bi.md`) | Cómo cambiar a datos reales sin que se filtren y cómo guardar el `.pbix` y el PDF | — |

Error encontrado de paso: el patrón `0[1-9]_*.sql` no veía la consulta 10. Ahora busca `[0-9][0-9]_*.sql` sin el esquema.

Pruebas: 62 de 62.

## Uso de IA delegada
| Cuándo | Herramienta | Qué hizo | Qué tuve que corregir |
|---|---|---|---|
| Vuelta 1 | Ollama qwen3.5:4b (local; Antigravity estaba ocupado y Power BI abierto en otro chat, por eso no el 9b) | Traducción del README al inglés, sección por sección | 14 errores, 3 de sentido (ver vuelta 1) |
