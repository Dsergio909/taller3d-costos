# Prueba del flujo en n8n de verdad

Corrida el 4-nov-2026 en el PC, con n8n 2.44.7 (Node 24, sin Docker, puerto 5679) y Ollama `qwen3.5:4b` en la GPU. Datos ficticios.

## Cómo repetirla
1. `powershell -ExecutionPolicy Bypass -File scripts\iniciar_n8n.ps1`
2. Importar y activar `flujos/aviso_errores.json` y `flujos/cotizacion.json`.
3. `python scripts/probar_flujo_n8n.py`

## Resultado de `scripts/probar_flujo_n8n.py`
| Pedido | Decisión del dueño | Precio en n8n | Precio en `costeo.py` | IA | Registro |
|---|---|---|---|---|---|
| 0 x Llavero por TikTok | (no llega a la IA) | — | — | — | Inválido |
| 2 x Figura 10 cm por WhatsApp | Aprobar | $50.000 | $50.000 | Borrador revisado: las cifras cuadran | Aprobado |
| 1 pieza FDM a medida (40 g, 3 h) por Instagram | Corregir (texto con tildes) | $33.500 | $33.500 | Borrador revisado: las cifras cuadran | Corregido, texto intacto |
| 3 x Aretes por TikTok | Rechazar | $4.500 | $4.500 | No puso el total: se usó la plantilla | Rechazado |

4 de 4 pedidos bien, 0 errores nuevos en `registro/errores.csv`.

## Lo que mostró la prueba
- **El control de cifras funciona:** en un pedido la IA no escribió el total y el borrador se cambió por la plantilla.
- **La IA puede inventar cosas que no son cifras.** En otra prueba escribió «la miniatura está lista» y «te enviamos», cuando la pieza todavía no estaba impresa. El control de números no lo atrapa: por eso el dueño aprueba o corrige antes de que salga. Captura del formulario de aprobación: `capturas/05_aprobacion_n8n.png`.
- **El manejo de errores funciona:** el primer intento falló en un nodo (ver abajo) y el flujo «Aviso de errores» lo dejó anotado en `registro/errores.csv` con el nodo y el mensaje.

## Errores que solo aparecieron corriendo n8n
1. **Ollama no respondía (`ECONNREFUSED ::1:11434`).** En Node 24, `localhost` se resuelve primero a IPv6 y Ollama solo escucha en `127.0.0.1`. El flujo siguió con la plantilla (el respaldo funcionó), pero sin IA. Arreglo: `ollama_url` = `http://127.0.0.1:11434`.
2. **Al reanudar después de la aprobación, «Armar registro» no encontraba los datos del IF** («Cannot read properties of undefined»). Después de una espera, n8n no sabe cuál de las dos salidas del IF tomar. Arreglo: el nodo distingue el camino por lo que le llega y lee «Avisar al dueño», que tiene una sola salida.
3. **El formulario de aprobación mostraba `**` en vez de negrita** y el costo sin formato. Arreglo: texto plano y costo en pesos.
4. **Puerto interno de n8n:** n8n abre un segundo puerto (por defecto 5679) que chocaba con el puerto principal. Arreglo: `N8N_RUNNERS_BROKER_PORT=5699` en `scripts/iniciar_n8n.ps1`.
