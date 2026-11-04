# Guía corta: el tablero en Power BI Desktop

## Abrir el tablero
- **Rápido:** abre `powerbi/taller3d-costos.pbix`. Ya trae los datos ficticios cargados.
- **Desde la fuente en texto:** abre `powerbi/proyecto/taller3d-costos.pbip`. La primera vez sale «Algunas de las tablas tienen datos incompletos»: dale **Actualizar ahora**.

Si clonaste el repo en otra carpeta: **Inicio → Transformar datos → Editar parámetros** → cambia `CarpetaDatos` a la ruta de tu carpeta `datos\` (con la barra `\` al final) → **Aceptar** → **Aplicar cambios**.

## Qué hace cada parte del modelo
- **Power Query** lee los 7 CSV con cultura `en-US` (punto decimal y fechas AAAA-MM-DD), quita la columna de marca donde no hace falta y, en la consulta `Piezas`, calcula el costo de cada pieza con la misma fórmula de `scripts/costeo.py`.
- **Tablas:** `Pedidos` y `Detalle` (hechos), `Piezas`, `Canales`, `Clientes`, `Calendario` y `Gastos`. `Tarifas` está oculta: solo la usan las medidas de precio.
- **Tablas que no se relacionan con nada, a propósito:**
  - `Ajuste de precio` y `Ajuste de cantidad` (los parámetros «qué pasa si», de −30 % a +30 %);
  - `Canal para precio`, para elegir la comisión del precio sugerido sin filtrar las ventas del año.
- **Medidas:** todas en la tabla `Medidas`, en carpetas. Copia en texto en `dax/medidas.md`.

## Usar tus datos reales (sin que se filtren)
1. Copia `datos\` como `datos_reales\`, cambia los valores y pon `real` en la columna `origen_datos`.
2. Si los editaste en Excel: `python scripts/revisar_datos.py --datos datos_reales --arreglar`.
3. Genera tu copia privada del tablero: `python scripts/armar_powerbi.py --datos datos_reales`. Queda en `datos_reales\powerbi\`, que no se sube a GitHub.
4. Ábrela y dale **Actualizar**. Arriba a la derecha de cada página debe decir **«DATOS REALES · no publicar»**.
5. Guarda esa versión solo dentro de `datos_reales\`. El `.pbix` guarda los datos adentro: nunca lo copies a `powerbi\`.
6. Antes de subir cualquier cosa: `python scripts/revisar_privacidad.py`.

## Guardar el .pbix y el PDF del repo (versión ficticia)
1. Abre `powerbi/proyecto/taller3d-costos.pbip` y dale **Actualizar**. Revisa que cada página diga «Datos ficticios · taller de ejemplo».
2. **Archivo → Guardar como** → tipo **Archivos de Power BI (\*.pbix)** → `powerbi\taller3d-costos.pbix`.
3. **Archivo → Exportar → Exportar a PDF** → guárdalo como `powerbi\taller3d-costos.pdf`.
4. Corre las pruebas: `test_pbix_lee_datos_ficticios` revisa que el `.pbix` lea `datos\` y no `datos_reales\`.

## Si cambias el tablero
El tablero se genera con `scripts/armar_powerbi.py`. Cambia el script, córrelo y vuelve a abrir el `.pbip`. **No lo corras con el proyecto abierto en Power BI**: Power BI nota el cambio y puede guardar encima.
