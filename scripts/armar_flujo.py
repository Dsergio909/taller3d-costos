"""Arma los flujos de n8n (JSON listo para importar) a partir de flujos/costeo.js.

Así el nodo que calcula el precio usa exactamente la misma fórmula que el tablero
y el SQL. Las pruebas comprueban que el JSON del repo esté al día con este script.

Uso:
    python scripts/armar_flujo.py                      # catálogo ficticio -> flujos/
    python scripts/armar_flujo.py --datos datos_reales  # tu catálogo -> datos_reales/flujos/ (no se sube)
"""
from __future__ import annotations

import argparse
import csv
import json
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ID_COTIZACION = "taller3dCotizar1"
ID_ERRORES = "taller3dErrores1"
NS = uuid.UUID("6f1c2a52-6b0e-4d55-9a3a-7d5a3c1f0e01")

COLUMNAS_REGISTRO = [
    "fecha_hora", "id_ejecucion", "origen", "cliente", "canal", "id_pieza", "pieza", "cantidad",
    "costo_unitario", "precio_unitario", "total", "margen_pct", "ia_ok", "nota_ia", "decision",
    "mensaje_final", "origen_datos",
]
COLUMNAS_PENDIENTES = ["fecha_hora", "id_ejecucion", "cliente", "pieza", "cantidad", "total", "enlace_aprobacion"]
COLUMNAS_ERRORES = ["fecha_hora", "flujo", "id_ejecucion", "nodo", "mensaje"]


def nid(nombre: str) -> str:
    return str(uuid.uuid5(NS, nombre))


def nodo(nombre, tipo, version, x, y, parametros, **extra):
    n = {"parameters": parametros, "id": nid(nombre), "name": nombre, "type": tipo,
         "typeVersion": version, "position": [x, y]}
    n.update(extra)
    return n


def a_texto_csv(columnas_js: str) -> str:
    """JS que convierte el objeto `r` en una línea CSV con esas columnas."""
    return (
        "const esc = (v) => { const s = v === undefined || v === null ? '' : String(v);\n"
        "  return /[\",\\n\\r]/.test(s) ? '\"' + s.replace(/\"/g, '\"\"') + '\"' : s; };\n"
        f"const linea = {columnas_js}.map((c) => esc(r[c])).join(',') + '\\n';\n"
    )


def codigo_normalizar() -> str:
    return """// Deja el pedido igual venga del formulario o del webhook.
const e = $input.first().json;
const cuerpo = e.body || e;              // el webhook trae los datos en body
const deFormulario = 'Pieza' in cuerpo;
const pieza = deFormulario ? String(cuerpo['Pieza']).split(' · ')[0] : cuerpo.id_pieza;
const num = (v) => (v === undefined || v === null || v === '' ? null : Number(v));
return [{ json: {
  origen: deFormulario ? 'formulario' : 'webhook',
  recibido_en: new Date().toISOString(),
  cliente: String(deFormulario ? cuerpo['Tu nombre o usuario'] : cuerpo.nombre || '').trim().slice(0, 60),
  canal: deFormulario ? cuerpo['Canal'] : cuerpo.canal,
  id_pieza: pieza,
  cantidad: num(deFormulario ? cuerpo['Cantidad'] : cuerpo.cantidad),
  a_medida: {
    tecnologia: deFormulario ? cuerpo['Tecnología (solo a medida)'] : cuerpo.tecnologia,
    material_cantidad: num(deFormulario ? cuerpo['Gramos o ml (solo a medida)'] : cuerpo.material_cantidad),
    horas_placa: num(deFormulario ? cuerpo['Horas de impresión (solo a medida)'] : cuerpo.horas_placa),
  },
  comentario: String((deFormulario ? cuerpo['Comentario'] : cuerpo.comentario) || '').slice(0, 300),
} }];
"""


def codigo_calcular(costeo_js: str) -> str:
    return costeo_js + """
// ---------------------------------------------------------------------------
// Pegamento de n8n: junta las filas de los 3 CSV y calcula la cotización.
const pedido = $('Configuración').first().json;
const filas = $input.all().map((i) => i.json);
const tarifas = tablaTarifas(filas.filter((f) => 'parametro' in f));
const catalogo = filas.filter((f) => 'id_pieza' in f && 'tecnologia' in f);
const canales = Object.fromEntries(filas.filter((f) => 'comision_pct' in f).map((f) => [f.canal, Number(f.comision_pct)]));
const origenDatos = filas.length && filas.every((f) => f.origen_datos === 'ficticio') ? 'ficticio' : 'real';

const fallo = (motivo) => [{ json: { ...pedido, ok: false, motivo, origen_datos: origenDatos } }];
if (!tarifas.margen_objetivo || !catalogo.length || !Object.keys(canales).length) {
  throw new Error('No se pudieron leer tarifas.csv, piezas.csv o canales.csv');
}

let pieza;
if (pedido.id_pieza === 'A medida') {
  const m = pedido.a_medida || {};
  if (!['Resina', 'FDM'].includes(m.tecnologia)) return fallo('Pieza a medida sin tecnología');
  if (!(m.material_cantidad > 0) || !(m.horas_placa > 0)) return fallo('Pieza a medida sin gramos/ml u horas');
  if (m.material_cantidad > 2000 || m.horas_placa > 72) return fallo('Pieza a medida fuera de rango: revisar a mano');
  pieza = { id_pieza: 'MEDIDA', nombre: 'Pieza a medida', tecnologia: m.tecnologia,
    material_cantidad: m.material_cantidad, horas_placa: m.horas_placa, piezas_por_placa: 1,
    minutos_acabado: tarifas.minutos_acabado_a_medida };
} else {
  pieza = catalogo.find((p) => p.id_pieza === pedido.id_pieza);
  if (!pieza) return fallo('La pieza no está en el catálogo');
}
if (!Number.isInteger(pedido.cantidad) || pedido.cantidad < 1 || pedido.cantidad > 500) {
  return fallo('Cantidad inválida (debe ser un entero entre 1 y 500)');
}
if (!(pedido.canal in canales)) return fallo('Canal desconocido');

const cot = cotizar(pieza, pedido.cantidad, pedido.canal, tarifas, canales);
const pesos = (n) => '$' + Math.round(n).toLocaleString('es-CO').replace(/,/g, '.');
const dias = Number(pedido.dias_entrega);
const prompt = [
  'Atiendes un taller de impresión 3D en Colombia. Escribe la respuesta para ' + (pedido.cliente || 'el cliente') + ', que escribió por ' + pedido.canal + '.',
  'Usa SOLO estas cifras, tal cual, sin agregar otras:',
  '- Pieza: ' + pieza.nombre,
  '- Cantidad: ' + cot.cantidad,
  '- Precio por unidad: ' + pesos(cot.precio_unitario),
  '- Total: ' + pesos(cot.total),
  '- Entrega: ' + dias + ' días hábiles',
  'Reglas: máximo 4 frases, tutea, tono amable y concreto, sin emojis, sin inventar descuentos, envíos ni fechas.',
  pedido.comentario ? 'El cliente comentó: "' + pedido.comentario + '" (respóndelo solo si se puede sin agregar cifras).' : '',
].filter(Boolean).join('\\n');
const plantilla = 'Hola' + (pedido.cliente ? ' ' + pedido.cliente : '') + ', gracias por escribirnos. '
  + cot.cantidad + ' x ' + pieza.nombre + ' quedan en ' + pesos(cot.precio_unitario) + ' cada una, '
  + pesos(cot.total) + ' en total. La entrega es en ' + dias + ' días hábiles. ¿Te lo separamos?';

return [{ json: { ...pedido, ok: true, pieza: pieza.nombre, tecnologia: pieza.tecnologia, ...cot,
  precio_texto: pesos(cot.precio_unitario), total_texto: pesos(cot.total), prompt, plantilla,
  origen_datos: origenDatos } }];
"""


CODIGO_REVISAR = r"""// Control de la IA: cada número del borrador debe estar en la cotización.
const c = $('Calcular cotización').first().json;
const r = $input.first().json;
let borrador = String(r.response || '').trim();
// Algunos modelos piensan en voz alta entre <think>…</think>: se quita.
borrador = borrador.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
const permitidos = new Set([c.cantidad, Math.round(c.precio_unitario), Math.round(c.total), Number(c.dias_entrega)]
  .map((n) => String(n)));
for (const n of String(c.pieza).match(/\d+/g) || []) permitidos.add(n);   // «Miniatura 32 mm»
const limpio = borrador.replace(/\b3D\b/gi, '');
const numeros = (limpio.match(/\d[\d.,]*/g) || []).map((n) => n.replace(/[.,](?=\d{3}\b)/g, '').replace(/[.,]$/, ''));
const extranos = numeros.filter((n) => !permitidos.has(n));
const tieneTotal = numeros.includes(String(Math.round(c.total)));
let ia_ok = borrador.length > 0 && extranos.length === 0 && tieneTotal;
let nota_ia = ia_ok ? 'Borrador de la IA revisado: todas las cifras cuadran'
  : !borrador ? 'La IA no devolvió texto: se usó la plantilla'
  : extranos.length ? 'La IA puso cifras que no están en la cotización (' + extranos.join(', ') + '): se usó la plantilla'
  : 'La IA no puso el total: se usó la plantilla';
const texto = ia_ok ? borrador : c.plantilla;
return [{ json: { ...c, borrador: texto, ia_ok, nota_ia } }];
"""

CODIGO_SIN_IA = """// Ollama no respondió después de los reintentos: se sigue con la plantilla.
const c = $('Calcular cotización').first().json;
return [{ json: { ...c, borrador: c.plantilla, ia_ok: false,
  nota_ia: 'Ollama no respondió después de 3 intentos: se usó la plantilla' } }];
"""


def codigo_pendiente() -> str:
    return (
        "// Aviso para Sergio: deja el enlace de aprobación en registro/pendientes.csv.\n"
        "// (Aquí se puede conectar Telegram o correo, con la credencial guardada en n8n, nunca en el repo.)\n"
        "const c = $input.first().json;\n"
        "const r = { fecha_hora: new Date().toISOString(), id_ejecucion: $execution.id, cliente: c.cliente,\n"
        "  pieza: c.pieza, cantidad: c.cantidad, total: Math.round(c.total), enlace_aprobacion: $execution.resumeFormUrl };\n"
        + a_texto_csv(json.dumps(COLUMNAS_PENDIENTES))
        + "return [{ json: { ...c, linea, resumen_para_sergio: '**' + c.cliente + '** pidió ' + c.cantidad + ' x ' + c.pieza\n"
        "  + ' por ' + c.canal + '. Costo ' + Math.round(c.costo_unitario) + ' c/u, precio ' + c.precio_texto\n"
        "  + ', total ' + c.total_texto + ', margen ' + Math.round(c.margen_pct * 100) + ' %.\\n\\n' + c.nota_ia\n"
        "  + '\\n\\nBorrador:\\n\\n' + c.borrador } }];\n"
    )


def codigo_registro() -> str:
    return (
        "// Arma la línea del registro con la decisión de Sergio (o el motivo del rechazo automático).\n"
        "const valido = $('¿Pedido válido?').first().json.ok === true;\n"
        "const c = valido ? $('Avisar a Sergio').first().json : $('Calcular cotización').first().json;\n"
        "const f = valido ? $input.first().json : {};\n"
        "let decision, mensaje;\n"
        "if (!valido) { decision = 'Inválido'; mensaje = c.motivo; }\n"
        "else if (f['Decisión'] === 'Aprobar') { decision = 'Aprobado'; mensaje = c.borrador; }\n"
        "else if (f['Decisión'] === 'Corregir') {\n"
        "  const t = String(f['Texto corregido'] || '').trim();\n"
        "  decision = t ? 'Corregido' : 'Aprobado sin cambios (corrección vacía)'; mensaje = t || c.borrador; }\n"
        "else if (f['Decisión'] === 'Rechazar') { decision = 'Rechazado'; mensaje = ''; }\n"
        "else { decision = 'Sin respuesta en 24 h'; mensaje = ''; }\n"
        "const r = { fecha_hora: new Date().toISOString(), id_ejecucion: $execution.id, origen: c.origen,\n"
        "  cliente: c.cliente, canal: c.canal, id_pieza: c.id_pieza, pieza: c.pieza || '', cantidad: c.cantidad,\n"
        "  costo_unitario: valido ? Math.round(c.costo_unitario) : '', precio_unitario: valido ? c.precio_unitario : '',\n"
        "  total: valido ? Math.round(c.total) : '', margen_pct: valido ? Math.round(c.margen_pct * 1000) / 10 : '',\n"
        "  ia_ok: valido ? c.ia_ok : '', nota_ia: valido ? c.nota_ia : '', decision, mensaje_final: mensaje,\n"
        "  origen_datos: c.origen_datos };\n"
        + a_texto_csv(json.dumps(COLUMNAS_REGISTRO))
        + "return [{ json: { ...r, linea } }];\n"
    )


def codigo_error() -> str:
    return (
        "// Toma el error de cualquier corrida y lo deja en registro/errores.csv.\n"
        "const e = $input.first().json;\n"
        "const r = { fecha_hora: new Date().toISOString(), flujo: e.workflow?.name || '',\n"
        "  id_ejecucion: e.execution?.id || '', nodo: e.execution?.lastNodeExecuted || '',\n"
        "  mensaje: (e.execution?.error?.message || 'Error sin mensaje').slice(0, 300) };\n"
        + a_texto_csv(json.dumps(COLUMNAS_ERRORES))
        + "return [{ json: { ...r, linea } }];\n"
    )


def nodos_guardar(prefijo: str, archivo_expr: str, x: int, y: int) -> list[dict]:
    """Par de nodos: texto -> archivo, y escribirlo al final (append) del CSV."""
    return [
        nodo(f"{prefijo}: a archivo", "n8n-nodes-base.convertToFile", 1.1, x, y,
             {"operation": "toText", "sourceProperty": "linea", "options": {"fileName": "linea.csv"}}),
        nodo(f"{prefijo}: guardar", "n8n-nodes-base.readWriteFile", 1, x + 220, y,
             {"operation": "write", "fileName": archivo_expr, "dataPropertyName": "data",
              "options": {"append": True}},
             retryOnFail=True, maxTries=3, waitBetweenTries=2000),
    ]


def flujo_cotizacion(piezas: list[dict], costeo_js: str) -> dict:
    opciones_pieza = [{"option": f"{p['id_pieza']} · {p['nombre']}"} for p in piezas] + [{"option": "A medida"}]
    canales = [{"option": c} for c in ("TikTok", "Instagram", "WhatsApp")]
    tecnologias = [{"option": "Resina"}, {"option": "FDM"}]
    config = [
        ("carpeta_datos", "datos"), ("carpeta_registro", "registro"),
        ("ollama_url", "http://localhost:11434"), ("modelo", "qwen3.5:4b"), ("dias_entrega", "5"),
    ]
    nodos = [
        nodo("Pedido por formulario", "n8n-nodes-base.formTrigger", 2.2, 0, 0, {
            "formTitle": "Pide tu cotización",
            "formDescription": "Taller de impresión 3D (ejemplo con datos ficticios). Te respondemos con el precio exacto.",
            "formFields": {"values": [
                {"fieldLabel": "Tu nombre o usuario", "requiredField": True},
                {"fieldLabel": "Canal", "fieldType": "dropdown", "fieldOptions": {"values": canales}, "requiredField": True},
                {"fieldLabel": "Pieza", "fieldType": "dropdown", "fieldOptions": {"values": opciones_pieza}, "requiredField": True},
                {"fieldLabel": "Cantidad", "fieldType": "number", "requiredField": True},
                {"fieldLabel": "Tecnología (solo a medida)", "fieldType": "dropdown", "fieldOptions": {"values": tecnologias}},
                {"fieldLabel": "Gramos o ml (solo a medida)", "fieldType": "number"},
                {"fieldLabel": "Horas de impresión (solo a medida)", "fieldType": "number"},
                {"fieldLabel": "Comentario", "fieldType": "textarea"},
            ]},
            "responseMode": "onReceived",
            "options": {"respondWithOptions": {"values": {
                "formSubmittedText": "Listo, recibimos tu pedido. Te respondemos con el precio pronto."}}},
        }, webhookId=nid("form")),
        nodo("Pedido por webhook", "n8n-nodes-base.webhook", 2, 0, 200, {
            "httpMethod": "POST", "path": "cotizar-taller3d", "responseMode": "onReceived", "options": {},
        }, webhookId=nid("webhook")),
        nodo("Normalizar pedido", "n8n-nodes-base.code", 2, 220, 100, {"jsCode": codigo_normalizar()}),
        nodo("Configuración", "n8n-nodes-base.set", 3.4, 440, 100, {
            "assignments": {"assignments": [
                {"id": nid("cfg-" + k), "name": k, "value": v, "type": "string"} for k, v in config]},
            "includeOtherFields": True, "options": {},
        }),
        nodo("Leer tarifas y catálogo", "n8n-nodes-base.readWriteFile", 1, 660, 100, {
            "fileSelector": "={{ $json.carpeta_datos }}/{tarifas,piezas,canales}.csv", "options": {},
        }, retryOnFail=True, maxTries=3, waitBetweenTries=2000),
        nodo("CSV a filas", "n8n-nodes-base.extractFromFile", 1, 880, 100, {"options": {}}),
        nodo("Calcular cotización", "n8n-nodes-base.code", 2, 1100, 100, {"jsCode": codigo_calcular(costeo_js)}),
        nodo("¿Pedido válido?", "n8n-nodes-base.if", 2, 1320, 100, {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [{"id": nid("cond-ok"), "leftValue": "={{ $json.ok }}", "rightValue": True,
                                "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                "combinator": "and"},
            "options": {},
        }),
        nodo("Redactar con IA local (Ollama)", "n8n-nodes-base.httpRequest", 4.2, 1540, 0, {
            "method": "POST", "url": "={{ $json.ollama_url }}/api/generate",
            "sendBody": True, "specifyBody": "json",
            "jsonBody": "={{ JSON.stringify({ model: $json.modelo, prompt: $json.prompt, stream: false, think: false, "
                        "options: { temperature: 0.3 } }) }}",
            "options": {"timeout": 120000},
        }, retryOnFail=True, maxTries=3, waitBetweenTries=3000, onError="continueErrorOutput"),
        nodo("Revisar cifras del borrador", "n8n-nodes-base.code", 2, 1760, -80, {"jsCode": CODIGO_REVISAR}),
        nodo("Plantilla sin IA", "n8n-nodes-base.code", 2, 1760, 80, {"jsCode": CODIGO_SIN_IA}),
        nodo("Avisar a Sergio", "n8n-nodes-base.code", 2, 1980, 0, {"jsCode": codigo_pendiente()}),
        *nodos_guardar("Pendiente", "={{ $('Configuración').first().json.carpeta_registro }}/pendientes.csv", 2200, -160),
        nodo("Aprobación de Sergio", "n8n-nodes-base.wait", 1.1, 2200, 0, {
            "resume": "form",
            "formTitle": "Aprobar cotización",
            "formDescription": "={{ $json.resumen_para_sergio }}",
            "formFields": {"values": [
                {"fieldLabel": "Decisión", "fieldType": "dropdown", "requiredField": True,
                 "fieldOptions": {"values": [{"option": "Aprobar"}, {"option": "Corregir"}, {"option": "Rechazar"}]}},
                {"fieldLabel": "Texto corregido", "fieldType": "textarea"},
            ]},
            "limitWaitTime": True, "limitType": "afterTimeInterval", "resumeAmount": 24, "resumeUnit": "hours",
            "options": {},
        }, webhookId=nid("aprobacion")),
        nodo("Armar registro", "n8n-nodes-base.code", 2, 2420, 100, {"jsCode": codigo_registro()}),
        *nodos_guardar("Registro", "={{ $('Configuración').first().json.carpeta_registro }}/cotizaciones.csv", 2640, 100),
    ]
    conexiones = {
        "Pedido por formulario": [["Normalizar pedido"]],
        "Pedido por webhook": [["Normalizar pedido"]],
        "Normalizar pedido": [["Configuración"]],
        "Configuración": [["Leer tarifas y catálogo"]],
        "Leer tarifas y catálogo": [["CSV a filas"]],
        "CSV a filas": [["Calcular cotización"]],
        "Calcular cotización": [["¿Pedido válido?"]],
        "¿Pedido válido?": [["Redactar con IA local (Ollama)"], ["Armar registro"]],
        "Redactar con IA local (Ollama)": [["Revisar cifras del borrador"], ["Plantilla sin IA"]],
        "Revisar cifras del borrador": [["Avisar a Sergio"]],
        "Plantilla sin IA": [["Avisar a Sergio"]],
        "Avisar a Sergio": [["Pendiente: a archivo", "Aprobación de Sergio"]],
        "Pendiente: a archivo": [["Pendiente: guardar"]],
        "Aprobación de Sergio": [["Armar registro"]],
        "Armar registro": [["Registro: a archivo"]],
        "Registro: a archivo": [["Registro: guardar"]],
    }
    return {
        "id": ID_COTIZACION,
        "name": "Taller 3D · Cotización con aprobación",
        "nodes": nodos,
        "connections": {
            origen: {"main": [[{"node": d, "type": "main", "index": 0} for d in salida] for salida in salidas]}
            for origen, salidas in conexiones.items()
        },
        "settings": {"executionOrder": "v1", "errorWorkflow": ID_ERRORES, "saveManualExecutions": True},
        "pinData": {},
        "active": False,
        "tags": [],
        "meta": {"templateCredsSetupCompleted": True},
    }


def flujo_errores() -> dict:
    nodos = [
        nodo("Cuando falla una corrida", "n8n-nodes-base.errorTrigger", 1, 0, 0, {}),
        nodo("Armar línea de error", "n8n-nodes-base.code", 2, 220, 0, {"jsCode": codigo_error()}),
        *nodos_guardar("Error", "registro/errores.csv", 440, 0),
    ]
    conexiones = {
        "Cuando falla una corrida": [["Armar línea de error"]],
        "Armar línea de error": [["Error: a archivo"]],
        "Error: a archivo": [["Error: guardar"]],
    }
    return {
        "id": ID_ERRORES,
        "name": "Taller 3D · Aviso de errores",
        "nodes": nodos,
        "connections": {
            o: {"main": [[{"node": d, "type": "main", "index": 0} for d in s] for s in ss]} for o, ss in conexiones.items()
        },
        "settings": {"executionOrder": "v1"},
        "pinData": {},
        "active": False,
        "tags": [],
        "meta": {"templateCredsSetupCompleted": True},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Arma los flujos de n8n")
    ap.add_argument("--datos", default="datos", help="carpeta del catálogo (datos o datos_reales)")
    a = ap.parse_args()
    carpeta = RAIZ / a.datos
    salida = RAIZ / "flujos" if a.datos == "datos" else carpeta / "flujos"
    with open(carpeta / "piezas.csv", encoding="utf-8", newline="") as f:
        piezas = list(csv.DictReader(f))
    costeo_js = (RAIZ / "flujos" / "costeo.js").read_text(encoding="utf-8")
    salida.mkdir(parents=True, exist_ok=True)
    for nombre, flujo in (("cotizacion.json", flujo_cotizacion(piezas, costeo_js)), ("aviso_errores.json", flujo_errores())):
        (salida / nombre).write_text(json.dumps(flujo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("Escrito", (salida / nombre).relative_to(RAIZ))


if __name__ == "__main__":
    main()
