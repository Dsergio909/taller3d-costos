# CLAUDE.md

## Qué es este repo
Plantilla pública del método de costos y cotizaciones de mi taller de impresión 3D. El plan está en mi cerebro de Obsidian (Google Drive, carpeta Cerebro): `Proyectos/Plan datos y n8n.md`, sección «3. Taller de impresión 3D». Cómo trabajo: `Proyectos/Como trabajar con Sergio.md`. Voz para textos públicos: `Personal/Mi_voz_al_escribir.md`.

## Reglas de este repo
- **Nunca datos reales del taller en el repo.** Van solo en `datos_reales/` (en `.gitignore`). Todo CSV del repo lleva `origen_datos = ficticio`; las pruebas fallan si no.
- La fórmula de costo vive en `scripts/costeo.py` y se repite en `sql/01_costo_por_pieza.sql`, `flujos/costeo.js` y la consulta `Piezas` de Power Query (`scripts/armar_powerbi.py`). Si cambia una, cambian las cuatro y las pruebas lo comprueban.
- Después de cambiar datos, flujo o tablero: `python scripts/generar_datos_ficticios.py`, `python scripts/armar_flujo.py`, `python scripts/armar_powerbi.py` y `python -m unittest discover -s pruebas -t pruebas`.
- No regenerar `powerbi/proyecto/` con Power BI abierto sobre ese proyecto: Power BI lo detecta y puede guardar encima.
- n8n de este proyecto: puerto 5679 y carpeta `.n8n_local/` (el 5678 es de otro proyecto).
- Nada se publica sin el «sí» de Sergio.

## Registro de carrera
Al cerrar ("cierra el chat") o cuando diga "registra esto", revisa si pasó algo que cumpla al menos uno de estos criterios: terminé o entregué algo, tomé una decisión importante con su razón, obtuve un resultado concreto, aprendí una herramienta usándola de verdad, o algo falló y entendí por qué. Si nada cumple, dime "nada para registrar".

- En mi Google Drive, carpeta Cerebro: Carrera/REGISTRO.md (registro) y Carrera/00_Carrera.md (formato).
- Si aparece una copia que dice "Este cerebro se mudó" (por ejemplo, en la carpeta vieja `Cerebro_Carrera`), ignórala.

Puedes escribir la entrada tú mismo: agrégala al final de REGISTRO.md sin editar ni borrar las anteriores, y confírmame en una línea. Si tu herramienta no puede agregar al final sin reemplazar el archivo completo o crear uno nuevo (por ejemplo, el conector de Drive desde la nube), no lo hagas: entrégame la entrada en un bloque de código para que yo la pegue.

Si no puedes leer 00_Carrera.md, usa este formato:

```markdown
## AAAA-MM-DD · <Proyecto> · <título corto>
- Qué hice:
- Problema que resuelve:
- Herramientas:
- Resultado o evidencia: (si no hay cifra real, no se inventa)
- Qué aprendí o qué falló:
- ¿Lo puedo defender en entrevista?: sí / parcial (qué me falta)
- ¿Se puede mostrar en público?: sí / no / solo sin datos internos
```

Máximo 8 líneas. Sin cifras inventadas, sin datos de terceros, sin claves ni rutas privadas.
