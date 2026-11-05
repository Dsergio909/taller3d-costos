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
| 3 | Segunda opinión externa sobre fórmula, SQL, DAX y código del flujo. Antigravity estuvo ocupado por otro chat 30 minutos (3:49 a 4:18 p. m.), así que la hizo Ollama, como dice la regla | **1 error de fórmula real:** las fallas se sumaban como +10 % del costo, pero si 1 de cada 10 placas sale mal, para tener 9 buenas se pagan 10: el costo es base / 0,9 (+11,1 %). **2 errores reales en el flujo:** un margen objetivo de 0 % hacía fallar el nodo («no se pudieron leer las tarifas») y una comisión con texto pasaba como `NaN` sin aviso. Una instrucción del prompt («sin inventar fechas») chocaba con los días de entrega | Fórmula corregida en los 4 lugares (Python, SQL, JS y Power Query) con protección si la tasa llega a 100 %. El nodo revisa que tarifas y comisiones sean números. Prompt aclarado. Cambiaron 13 cifras del README (por ejemplo, ganancia del año $15.012.331 → $14.958.330); la prueba de cifras las encontró todas y las 5 conclusiones siguen siendo ciertas |
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

Pruebas: 63 de 63.

## Vuelta 3 de mejoras (4-nov-2026): el flujo corriendo en n8n de verdad
Sergio aprobó instalar n8n (4-nov). n8n 2.44.7 con Node 24, puerto 5679, puerto interno 5699, datos en `.n8n_local/`.

| # | Qué | Resultado |
|---|---|---|
| 1 | Importar y activar los dos flujos | n8n los aceptó sin cambios: al activarlos revisa cada nodo y registra el formulario y el webhook |
| 2 | Pedido inválido | No llegó a la IA; quedó como «Inválido» en el registro |
| 3 | **Error 1:** Ollama no respondía (`ECONNREFUSED ::1:11434`) | `localhost` va primero a IPv6 en Node 24 y Ollama escucha en `127.0.0.1`. El respaldo funcionó (usó la plantilla y lo avisó). Arreglo: `127.0.0.1` |
| 4 | **Error 2:** al reanudar después de la aprobación, «Armar registro» fallaba | n8n no sabe cuál salida del IF tomar después de una espera. El flujo de errores lo anotó en `registro/errores.csv` (el manejo de errores funcionó). Arreglo: leer el nodo «Avisar al dueño» |
| 5 | **Error 3:** el formulario mostraba `**` y el costo sin formato | Texto plano y costo en pesos |
| 6 | Prueba de punta a punta nueva: `scripts/probar_flujo_n8n.py` | 4 de 4 pedidos bien (Aprobado, Corregido con tildes, Rechazado, Inválido), precios iguales a `costeo.py`, 0 errores nuevos. Detalle en `docs/prueba_n8n.md` |
| 7 | Lo que hace la IA de verdad | 2 de 3 borradores pasaron el control de cifras; en 1 no puso el total y se usó la plantilla. En otro dijo «la miniatura está lista» (falso): el control de números no lo ve, la aprobación humana sí |

Nota: el navegador integrado de Claude bloquea el envío de formularios (`ERR_BLOCKED_BY_CLIENT`); por eso las aprobaciones de prueba se envían con el script, igual que lo hace un navegador.

## Vuelta de facilidad y diseño (4-nov-2026)
Turno de Power BI coordinado con los otros chats (Olist → taller 3D → vuelos).

| # | Qué revisé | Qué encontré | Arreglo |
|---|---|---|---|
| 1 | Las 4 páginas con la fórmula corregida, contra el SQL | Todo cuadra: ganancia $14.958.330, escenario $15.693.866 (+$735.536), WhatsApp $5.832.842 y 53,1 %, 549 pedidos, $25.654.750 | — |
| 2 | Página 1 | La tabla de 6 columnas no cabía: «Ganancia por hora» cortada y barra de desplazamiento | Gráfico 700 → 580 px, tabla 516 → 636 px |
| 3 | Página 4 | La tabla de 3 filas dejaba mucho espacio vacío | Gráficos 296 → 330 px de alto, tabla 204 → 166 |
| 4 | Estilo | Fondo claro, letra Segoe UI, un solo azul (#1a5fb4) y grises; sin neón, degradados ni adornos. Aviso «Datos ficticios · taller de ejemplo» en cada página | — |
| 5 | Entregables | `powerbi/taller3d-costos.pbix` (144 KB), `powerbi/taller3d-costos.pdf` (4 páginas), 4 capturas en `capturas/` | — |
| 6 | Prueba de privacidad del `.pbix` | **Pasaba sin revisar nada:** Power BI 2.159 ya no guarda las consultas en la parte legible `DataMashup`, sino dentro del modelo comprimido | La prueba ahora revisa que el `.pbix` tenga las mismas 4 páginas del proyecto (que sí lee `datos\`) y el aviso del origen de los datos en cada una. Limitación anotada: el modelo comprimido no se puede leer sin Power BI |

Pruebas: 63 de 63.

## Auditoría final (4-nov-2026, noche)
La hizo el chat principal sobre una copia limpia: regenerar datos, costeo y SQL no cambió nada, 63 de 63 pruebas, control de privacidad limpio. Antigravity (Gemini, en 2 partes) revisó la fórmula en Python, JS y SQL, las 10 consultas y las conclusiones del README: **0 errores de cálculo** (confirmó unidades, fallas /(1 − tasa), margen y comisión, redondeo y las cifras de las conclusiones 2, 4 y 5). Una sugerencia se descartó: «división entera en el FEP» no pasa porque `tarifas.valor` es REAL. Quedaron 4 ajustes:

| # | Qué | Por qué importaba | Arreglo | Prueba |
|---|---|---|---|---|
| 1 | README, conclusión 3: «el 42 % de sus clientes vuelve a comprar» | `sql/05` cuenta dentro de cada canal: quien compra por Instagram y después por WhatsApp no cuenta como cliente que vuelve en ninguno | El texto dice «vuelve a comprar por WhatsApp (se cuenta dentro del mismo canal)», en español e inglés. Comentario en `sql/05` | `test_readme` exige la frase nueva |
| 2 | `sql/08` mes a mes: `JOIN caja USING (mes)` era INNER | Con datos reales, un mes con gastos y sin ventas (o al revés) desaparecía y el LAG comparaba contra dos meses atrás | Lista completa de meses (CTE recursiva del primer al último mes), LEFT JOIN de ventas y gastos con 0, y % vacío si el mes anterior no vendió | `test_mes_a_mes_no_pierde_meses`: junio sin ventas y marzo sin gastos → siguen los 12 meses, junio −100 % contra mayo, julio sin % |
| 3 | `sql/01`: el CASE mandaba cualquier tecnología rara a FDM | Python y JS dan error; SQL la cobraba como FDM | El esquema ya la rechazaba (CHECK); además la vista ahora pide `'FDM'` explícito y deja el costo vacío con otro valor | `test_tecnologia_desconocida_no_se_cobra_como_fdm` |
| 4 | `sql/10` cohortes: `dias_promedio_hasta_volver` usaba a todos, sin la ventana de 90 días | No era comparable con `pct_volvieron_en_90_dias` (T1: 122 días contra un % medido a 90) | Ahora es `dias_promedio_si_volvio_en_90`, con la misma ventana: T1 50, T2 43, T3 44, T4 vacío. No sale en el README ni en el tablero | `test_cohortes` revisa que sea ≤ 90 |

Las cifras del tablero y del README no cambiaron (la tabla mes a mes da lo mismo con los datos ficticios; solo cambió `docs/resultados_sql.md` en la columna de cohortes). De paso: `docs/resultados_sql.md` mostraba «None» y ahora muestra «—».

Pruebas: 65 de 65.

## Revisión de la nube y arreglos (5-nov-2026)
La nube clonó el repo como un desconocido (commit 9cdd02a): 65 de 65 pruebas, regenerar deja `git status` vacío, historial de 15 commits sin datos reales, y las tarifas no coinciden con las reales. Rehízo la fórmula desde el README: da lo mismo en las 17 piezas y todas las cifras de «Qué encontré» cuadran. Pidió 9 arreglos de texto y diseño. Cada uno se comprobó contra los datos antes de cambiarlo:

| # | Qué pidió | Comprobado | Arreglo |
|---|---|---|---|
| 1 | WhatsApp mezclaba bases: «136 de 549 pedidos» con un % de ventas y un ticket de pedidos entregados | Sí: 129 de 506 entregados; con 136 el ticket daría otro | README (ES y EN): «129 de los 506 pedidos entregados», frase partida en dos. Tablero p. 4: la columna es «Pedidos entregados». `test_readme` exige la misma base |
| 2 | 40,5 / 27,2 / 46,0 % no decía sobre qué se calcula | Sí: suma de una pieza de cada una del catálogo. Pesado por lo vendido: mano de obra en resina 45,7 %, filamento en FDM 43,1 % | El README dice las dos cosas; la prueba calcula las dos |
| 3 | «De lo más vendido (64 unidades)» | Sí: quinto de 17 (fichas 380, imanes 104, aretes 99, miniaturas 76) | «El quinto más vendido». La prueba calcula el puesto |
| 4 | Tablas con barra de desplazamiento (p. 1 y p. 2, faltaban 4 piezas en la 2) | Sí, en Power BI | Filas más bajas (relleno 4 → 2); en la p. 2 la fila de tarjetas baja de 84 a 76 px, el filtro de canal de 84 a 60 y la tabla sube de 412 a 452 px. Revisado en Power BI: 17 de 17 filas, sin barra |
| 5 | «Datos ficticios» cortado arriba en las capturas | Las capturas viejas eran pantallazos; en el PDF se leía | Tarjeta más alta (40 → 56 px) y capturas sacadas del PDF: se lee completo en las 4 |
| 6 | Líneas curvas; «may 25» cortado | Sí | Línea recta en p. 3 y p. 4. En la p. 3 el gráfico de líneas pasa de 456 a 600 px de ancho |
| 7 | «Ventas sin comisión» se confunde con «Ventas netas» | Sí | La medida ahora se llama «Ventas menos comisiones» ($24.792.985) |
| 8 | Capturas en JPG de 1.403 px | Sí | PNG de 2.656 × 1.536 px sacadas del PDF con Inkscape. El formulario de n8n, en PNG al doble (1.280 px) con Edge sin ventana, y el «40 %» ya no se parte en dos líneas |
| 9 | `CLAUDE.md` desactualizado | Sí | El cerebro es el repo privado `Dsergio909/cerebro`, nota `Proyectos/Taller 3D costos.md`; desde la nube solo se lee y se entrega un paquete |
| 11 | Frase de 47 palabras en «Privacidad» | Sí | Partida en dos (ES y EN) |
| 12 | «Submit» → «Enviar» en el formulario | Se probó: el nodo de espera de n8n 2.44 ignora la opción del botón | Queda «Submit» (anotado en el script). Sí se quitó el pie «Form automated with n8n» |

No se hizo el punto 10 (rama `main`): espera el «sí» de Sergio.

Prueba nueva: todas las imágenes del README existen. Pruebas: 66 de 66. Las cifras del tablero no cambiaron (revisadas en Power BI: $14.958.330, $15.693.866, +$735.536, WhatsApp 129 pedidos entregados, $85.133, 53,1 %).

## Uso de IA delegada
| Cuándo | Herramienta | Qué hizo | Qué tuve que corregir |
|---|---|---|---|
| Vuelta 1 | Ollama qwen3.5:4b (local; Antigravity estaba ocupado y Power BI abierto en otro chat, por eso no el 9b) | Traducción del README al inglés, sección por sección | 14 errores, 3 de sentido (ver vuelta 1) |
| Vuelta 3 | Ollama qwen3.5:4b (Antigravity ocupado 30 min; Power BI abierto en otro chat) | Segunda opinión de código en 4 partes (5,8 min) | De ~25 hallazgos, 4 reales (tasa de fallas, margen 0 %, comisión no numérica, prompt). Los demás eran falsos: decía que en JS `"5" * precio` concatena textos, que «$1.200» no se reconoce como 1200 y que la fórmula del trimestre está mal; en la parte de DAX repitió el mismo punto más de 40 veces |
| Auditoría final | Antigravity (Gemini), lo lanzó el chat principal | Revisó fórmula (Python, JS, SQL), consultas y conclusiones del README en 2 partes | 0 errores de cálculo; 1 sugerencia descartada (división entera en el FEP: `valor` es REAL); 4 ajustes válidos, arreglados arriba |
